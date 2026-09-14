from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from agent.providers.anthropic.provider import AnthropicProviderSession
from agent.providers.factory import create_provider_session
from agent.providers.openai import (
    OpenAIChatParseState,
    OpenAIProviderSession,
    _build_chat_provider_turn,
    _is_chat_param_compat_error,
    parse_chat_event,
    serialize_openai_chat_tools,
)
from agent.providers.base import StreamEvent
from agent.tools import CanonicalToolDefinition
from llm import (
    CUSTOM_MODELS,
    CustomProviderConfig,
    Llm,
    create_custom_anthropic_client,
    create_custom_openai_client,
    create_custom_provider_client,
    custom_provider_wire_format,
    normalize_custom_provider_format,
)
from routes.generate_code import ModelSelectionStage, ParameterExtractionStage


class TestCustomProviderFormat:
    def test_normalize_canonical_formats(self) -> None:
        for format_name in ("openai", "anthropic", "xai", "openrouter", "custom"):
            assert normalize_custom_provider_format(format_name) == format_name

    def test_normalize_is_case_and_whitespace_tolerant(self) -> None:
        assert normalize_custom_provider_format("  OpenAI ") == "openai"
        assert normalize_custom_provider_format("ANTHROPIC") == "anthropic"

    def test_normalize_aliases(self) -> None:
        assert normalize_custom_provider_format("openai-compatible") == "openai"
        assert normalize_custom_provider_format("anthropic-compatible") == "anthropic"

    @pytest.mark.parametrize("value", [None, "", "   "])
    def test_normalize_blank_defaults_to_openai(self, value: str | None) -> None:
        assert normalize_custom_provider_format(value) == "openai"

    def test_normalize_unknown_falls_back_to_custom(self) -> None:
        assert normalize_custom_provider_format("azure") == "custom"

    def test_wire_format_routing(self) -> None:
        assert custom_provider_wire_format("anthropic") == "anthropic"
        for format_name in ("openai", "xai", "openrouter", "custom", None, "azure"):
            assert custom_provider_wire_format(format_name) == "openai"

    def test_custom_model_registered(self) -> None:
        assert Llm.CUSTOM.value == "custom"
        assert Llm.CUSTOM in CUSTOM_MODELS


class TestCustomProviderConfig:
    def test_from_values_cleans_inputs(self) -> None:
        config = CustomProviderConfig.from_values(
            base_url="  https://example.com/v1  ",
            api_key="  key  ",
            provider_format="  OpenRouter ",
            model="  openai/gpt-4o  ",
        )
        assert config.base_url == "https://example.com/v1"
        assert config.api_key == "key"
        assert config.provider_format == "openrouter"
        assert config.model == "openai/gpt-4o"

    def test_from_values_blank_is_none(self) -> None:
        config = CustomProviderConfig.from_values(
            base_url="   ", api_key="", provider_format=None, model=None
        )
        assert config.base_url is None
        assert config.api_key is None
        assert config.provider_format == "openai"
        assert config.model is None

    def test_is_configured_requires_key_and_model(self) -> None:
        assert (
            CustomProviderConfig.from_values(api_key="k", model="m").is_configured
            is True
        )
        assert (
            CustomProviderConfig.from_values(api_key="k").is_configured is False
        )
        assert (
            CustomProviderConfig.from_values(model="m").is_configured is False
        )

    def test_effective_base_url_prefers_explicit(self) -> None:
        config = CustomProviderConfig.from_values(
            base_url="https://proxy.local/v1/", provider_format="openai"
        )
        assert config.effective_base_url == "https://proxy.local/v1"

    def test_effective_base_url_defaults_per_format(self) -> None:
        assert (
            CustomProviderConfig.from_values(provider_format="openai").effective_base_url
            == "https://api.openai.com/v1"
        )
        assert (
            CustomProviderConfig.from_values(
                provider_format="anthropic"
            ).effective_base_url
            == "https://api.anthropic.com"
        )
        assert (
            CustomProviderConfig.from_values(provider_format="xai").effective_base_url
            == "https://api.x.ai/v1"
        )
        assert (
            CustomProviderConfig.from_values(
                provider_format="openrouter"
            ).effective_base_url
            == "https://openrouter.ai/api/v1"
        )
        assert (
            CustomProviderConfig.from_values(provider_format="custom").effective_base_url
            is None
        )

    def test_api_model_name(self) -> None:
        assert (
            CustomProviderConfig.from_values(model="x/model").api_model_name
            == "x/model"
        )
        assert CustomProviderConfig.from_values().api_model_name == ""


class TestCustomProviderClients:
    def test_openai_client_uses_custom_base_url(self) -> None:
        config = CustomProviderConfig.from_values(
            base_url="https://openrouter.ai/api/v1",
            api_key="key",
            provider_format="openrouter",
            model="openai/gpt-4o",
        )
        client = create_custom_openai_client(config)
        assert str(client.base_url) == "https://openrouter.ai/api/v1/"
        assert client.api_key == "key"

    def test_openai_client_requires_key(self) -> None:
        with pytest.raises(ValueError, match="API key"):
            create_custom_openai_client(CustomProviderConfig.from_values(model="m"))

    def test_anthropic_client_uses_custom_base_url(self) -> None:
        config = CustomProviderConfig.from_values(
            base_url="https://gateway.local",
            api_key="key",
            provider_format="anthropic",
            model="claude-x",
        )
        client = create_custom_anthropic_client(config)
        assert str(client.base_url).rstrip("/") == "https://gateway.local"
        assert client.api_key == "key"

    def test_router_picks_client_by_wire_format(self) -> None:
        openai_config = CustomProviderConfig.from_values(
            api_key="k", provider_format="xai", model="grok-x"
        )
        anthropic_config = CustomProviderConfig.from_values(
            api_key="k", provider_format="anthropic", model="claude-x"
        )
        assert type(create_custom_provider_client(openai_config)).__name__ == (
            "AsyncOpenAI"
        )
        assert type(create_custom_provider_client(anthropic_config)).__name__ == (
            "AsyncAnthropic"
        )


class TestCustomProviderFactory:
    def test_custom_openai_routes_to_chat_completions_session(self) -> None:
        session = create_provider_session(
            model=Llm.CUSTOM,
            prompt_messages=[{"role": "user", "content": "Build a page."}],
            should_generate_images=True,
            openai_api_key=None,
            openai_base_url=None,
            anthropic_api_key=None,
            gemini_api_key=None,
            replicate_api_key=None,
            custom_provider=CustomProviderConfig.from_values(
                base_url="https://openrouter.ai/api/v1",
                api_key="key",
                provider_format="openrouter",
                model="openai/gpt-4o",
            ),
        )
        assert isinstance(session, OpenAIProviderSession)
        assert session._api_model_name == "openai/gpt-4o"
        assert session._use_chat_completions is True
        # Chat tools use non-strict function calling for third-party compat.
        assert session._tools
        assert all("strict" not in tool for tool in session._tools)
        assert all(tool["type"] == "function" for tool in session._tools)

    def test_custom_anthropic_routes_to_anthropic_session(self) -> None:
        session = create_provider_session(
            model=Llm.CUSTOM,
            prompt_messages=[
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "Build a page."},
            ],
            should_generate_images=True,
            openai_api_key=None,
            openai_base_url=None,
            anthropic_api_key=None,
            gemini_api_key=None,
            replicate_api_key=None,
            custom_provider=CustomProviderConfig.from_values(
                base_url="https://gateway.local",
                api_key="key",
                provider_format="anthropic",
                model="claude-x",
            ),
        )
        assert isinstance(session, AnthropicProviderSession)
        assert session._api_model_name == "claude-x"
        assert session._is_custom is True
        assert all(
            "eager_input_streaming" not in tool for tool in session._tools
        )

    def test_custom_without_config_raises(self) -> None:
        with pytest.raises(Exception, match="not configured"):
            create_provider_session(
                model=Llm.CUSTOM,
                prompt_messages=[{"role": "user", "content": "Build a page."}],
                should_generate_images=True,
                openai_api_key=None,
                openai_base_url=None,
                anthropic_api_key=None,
                gemini_api_key=None,
                replicate_api_key=None,
                custom_provider=CustomProviderConfig.from_values(),
            )


class TestCustomModelSelection:
    def setup_method(self):
        self.model_selector = ModelSelectionStage(AsyncMock())

    def _custom(self) -> CustomProviderConfig:
        return CustomProviderConfig.from_values(
            base_url="https://openrouter.ai/api/v1",
            api_key="key",
            provider_format="openrouter",
            model="openai/gpt-4o",
        )

    async def test_custom_create_uses_custom_for_all_variants(self) -> None:
        models = await self.model_selector.select_models(
            generation_type="create",
            input_mode="image",
            openai_api_key=None,
            anthropic_api_key=None,
            gemini_api_key=None,
            custom_provider=self._custom(),
        )
        assert models == [Llm.CUSTOM] * 4

    async def test_custom_update_uses_two_variants(self) -> None:
        models = await self.model_selector.select_models(
            generation_type="update",
            input_mode="text",
            openai_api_key=None,
            anthropic_api_key=None,
            gemini_api_key=None,
            custom_provider=self._custom(),
        )
        assert models == [Llm.CUSTOM] * 2

    async def test_custom_video_uses_two_variants(self) -> None:
        models = await self.model_selector.select_models(
            generation_type="create",
            input_mode="video",
            openai_api_key=None,
            anthropic_api_key=None,
            gemini_api_key=None,
            custom_provider=self._custom(),
        )
        assert models == [Llm.CUSTOM] * 2

    async def test_unconfigured_custom_falls_back_to_key_selection(self) -> None:
        models = await self.model_selector.select_models(
            generation_type="update",
            input_mode="text",
            openai_api_key="key",
            anthropic_api_key=None,
            gemini_api_key=None,
            custom_provider=CustomProviderConfig.from_values(),
        )
        assert models != [Llm.CUSTOM] * 2


class TestCustomParameterExtraction:
    async def test_extracts_custom_provider_from_ui(self) -> None:
        stage = ParameterExtractionStage(AsyncMock())
        extracted = await stage.extract_and_validate(
            {
                "generatedCodeConfig": "html_tailwind",
                "inputMode": "text",
                "prompt": {"text": "hello"},
                "customProviderBaseUrl": "https://openrouter.ai/api/v1",
                "customProviderApiKey": "ui-key",
                "customProviderFormat": "openrouter",
                "customProviderModel": "openai/gpt-4o",
            }
        )
        assert extracted.custom_provider is not None
        assert extracted.custom_provider.is_configured is True
        assert extracted.custom_provider.api_key == "ui-key"
        assert extracted.custom_provider.api_model_name == "openai/gpt-4o"
        assert extracted.custom_provider.provider_format == "openrouter"

    async def test_extracts_custom_provider_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "routes.generate_code.CUSTOM_PROVIDER_BASE_URL", "https://x.ai/v1"
        )
        monkeypatch.setattr(
            "routes.generate_code.CUSTOM_PROVIDER_API_KEY", "env-key"
        )
        monkeypatch.setattr("routes.generate_code.CUSTOM_PROVIDER_FORMAT", "xai")
        monkeypatch.setattr(
            "routes.generate_code.CUSTOM_PROVIDER_MODEL", "grok-x"
        )
        stage = ParameterExtractionStage(AsyncMock())
        extracted = await stage.extract_and_validate(
            {
                "generatedCodeConfig": "html_tailwind",
                "inputMode": "text",
                "prompt": {"text": "hello"},
            }
        )
        assert extracted.custom_provider is not None
        assert extracted.custom_provider.is_configured is True
        assert extracted.custom_provider.api_key == "env-key"
        assert extracted.custom_provider.api_model_name == "grok-x"

    async def test_custom_provider_defaults_to_unconfigured(self) -> None:
        stage = ParameterExtractionStage(AsyncMock())
        extracted = await stage.extract_and_validate(
            {
                "generatedCodeConfig": "html_tailwind",
                "inputMode": "text",
                "prompt": {"text": "hello"},
            }
        )
        assert extracted.custom_provider is not None
        assert extracted.custom_provider.is_configured is False


def _canonical_tool() -> CanonicalToolDefinition:
    return CanonicalToolDefinition(
        name="create_file",
        description="Create a file.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    )


class TestChatCompletionsPath:
    def test_serialize_chat_tools(self) -> None:
        serialized = serialize_openai_chat_tools([_canonical_tool()])
        assert serialized == [
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": "Create a file.",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                    },
                },
            }
        ]

    def test_param_compat_error_detection(self) -> None:
        assert (
            _is_chat_param_compat_error(
                Exception("Unrecognized request argument: stream_options")
            )
            is True
        )
        assert (
            _is_chat_param_compat_error(Exception("Unsupported max_tokens value"))
            is True
        )
        assert (
            _is_chat_param_compat_error(Exception("model_not_found: nope")) is False
        )

    async def test_parse_chat_event_content_and_tools(self) -> None:
        events: list[StreamEvent] = []

        async def sink(event: StreamEvent) -> None:
            events.append(event)

        state = OpenAIChatParseState()
        await parse_chat_event(
            SimpleNamespace(
                usage=None,
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(
                            content="Hello",
                            reasoning_content=None,
                            reasoning=None,
                            tool_calls=[],
                        )
                    )
                ],
            ),
            state,
            sink,
        )
        await parse_chat_event(
            SimpleNamespace(
                usage=None,
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(
                            content=None,
                            reasoning_content=None,
                            reasoning=None,
                            tool_calls=[
                                SimpleNamespace(
                                    index=0,
                                    id="call-1",
                                    function=SimpleNamespace(
                                        name="create_file",
                                        arguments='{"path":',
                                    ),
                                )
                            ],
                        )
                    )
                ],
            ),
            state,
            sink,
        )
        await parse_chat_event(
            SimpleNamespace(
                usage=SimpleNamespace(
                    prompt_tokens=10, completion_tokens=5, total_tokens=15
                ),
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(
                            content=None,
                            reasoning_content=None,
                            reasoning=None,
                            tool_calls=[
                                SimpleNamespace(
                                    index=0,
                                    id=None,
                                    function=SimpleNamespace(
                                        name=None,
                                        arguments='"index.html"}',
                                    ),
                                )
                            ],
                        )
                    )
                ],
            ),
            state,
            sink,
        )

        assert state.assistant_text == "Hello"
        assert state.tool_calls[0]["arguments"] == '{"path":"index.html"}'
        assert state.turn_usage is not None
        assert state.turn_usage.input == 10
        assert state.turn_usage.output == 5

        turn = _build_chat_provider_turn(state)
        assert turn.assistant_text == "Hello"
        assert len(turn.tool_calls) == 1
        assert turn.tool_calls[0].id == "call-1"
        assert turn.tool_calls[0].name == "create_file"
        assert turn.tool_calls[0].arguments == {"path": "index.html"}
        assert turn.assistant_turn["role"] == "assistant"
        assert turn.assistant_turn["tool_calls"][0]["id"] == "call-1"

        assert [event.type for event in events] == [
            "assistant_delta",
            "tool_call_delta",
            "tool_call_delta",
        ]

    async def test_parse_chat_event_reasoning(self) -> None:
        events: list[StreamEvent] = []

        async def sink(event: StreamEvent) -> None:
            events.append(event)

        state = OpenAIChatParseState()
        await parse_chat_event(
            SimpleNamespace(
                usage=None,
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(
                            content=None,
                            reasoning_content="thinking...",
                            reasoning=None,
                            tool_calls=[],
                        )
                    )
                ],
            ),
            state,
            sink,
        )
        assert [event.type for event in events] == ["thinking_delta"]
        assert events[0].text == "thinking..."


class TestCustomProviderRoutes:
    @staticmethod
    def _client() -> TestClient:
        from main import app

        return TestClient(app)

    def test_list_formats(self) -> None:
        response = self._client().get("/api/custom-provider/formats")
        assert response.status_code == 200
        formats = {entry["value"]: entry for entry in response.json()}
        assert set(formats) == {"openai", "anthropic", "xai", "openrouter", "custom"}
        assert formats["openai"]["label"] == "OpenAI-compatible"
        assert formats["anthropic"]["wire_format"] == "anthropic"
        assert formats["xai"]["wire_format"] == "openai"
        assert (
            formats["openrouter"]["default_base_url"]
            == "https://openrouter.ai/api/v1"
        )

    def test_list_models_openai_wire(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from routes import custom_provider as route_module
        from routes.custom_provider import CustomProviderModelInfo

        seen: dict[str, Any] = {}

        async def fake_fetch(base_url: str, api_key: str | None):
            seen["base_url"] = base_url
            seen["api_key"] = api_key
            return [CustomProviderModelInfo(id="b-model"), CustomProviderModelInfo(id="a-model")]

        monkeypatch.setattr(
            route_module, "_fetch_openai_compatible_models", fake_fetch
        )
        response = self._client().post(
            "/api/custom-provider/models",
            json={
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "key",
                "provider_format": "openrouter",
            },
        )
        assert response.status_code == 200
        assert seen == {
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "key",
        }
        payload = response.json()
        assert payload["wire_format"] == "openai"
        assert [model["id"] for model in payload["models"]] == [
            "b-model",
            "a-model",
        ]

    def test_list_models_anthropic_wire_uses_default_base_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from routes import custom_provider as route_module
        from routes.custom_provider import CustomProviderModelInfo

        seen: dict[str, Any] = {}

        async def fake_fetch(base_url: str, api_key: str | None):
            seen["base_url"] = base_url
            return [CustomProviderModelInfo(id="claude-x", name="Claude X")]

        monkeypatch.setattr(
            route_module, "_fetch_anthropic_compatible_models", fake_fetch
        )
        response = self._client().post(
            "/api/custom-provider/models",
            json={"api_key": "key", "provider_format": "anthropic"},
        )
        assert response.status_code == 200
        assert seen == {"base_url": "https://api.anthropic.com"}
        payload = response.json()
        assert payload["wire_format"] == "anthropic"
        assert payload["models"] == [{"id": "claude-x", "name": "Claude X"}]

    def test_list_models_requires_base_url_for_custom_format(self) -> None:
        response = self._client().post(
            "/api/custom-provider/models",
            json={"provider_format": "custom"},
        )
        assert response.status_code == 400
        assert "Base URL" in response.json()["detail"]

    def test_extract_model_ids_sorts_and_dedupes(self) -> None:
        from routes.custom_provider import _extract_model_ids

        models = _extract_model_ids(
            {"data": [{"id": "b"}, {"id": "a"}, {"id": "b"}, {"id": "  "}, "nope"]}
        )
        assert [model.id for model in models] == ["a", "b"]

    def test_extract_model_ids_rejects_unexpected_payload(self) -> None:
        from fastapi import HTTPException

        from routes.custom_provider import _extract_model_ids

        with pytest.raises(HTTPException):
            _extract_model_ids({"unexpected": True})
