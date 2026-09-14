from typing import Optional

from anthropic import AsyncAnthropic
from google import genai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from agent.providers.anthropic import AnthropicProviderSession, serialize_anthropic_tools
from agent.providers.base import ProviderSession
from agent.providers.gemini import GeminiProviderSession, serialize_gemini_tools
from agent.providers.openai import (
    OpenAIProviderSession,
    serialize_openai_chat_tools,
    serialize_openai_tools,
)
from agent.tools import canonical_tool_definitions
from config import REPLICATE_API_KEY
from fs_logging.agent_runs import AgentRunRecorder
from llm import (
    ANTHROPIC_MODELS,
    CUSTOM_MODELS,
    GEMINI_MODELS,
    OPENAI_MODELS,
    CustomProviderConfig,
    Llm,
    create_custom_anthropic_client,
    create_custom_openai_client,
)
from preview_screenshot import is_screenshot_preview_available


def create_provider_session(
    model: Llm,
    prompt_messages: list[ChatCompletionMessageParam],
    should_generate_images: bool,
    openai_api_key: Optional[str],
    openai_base_url: Optional[str],
    anthropic_api_key: Optional[str],
    gemini_api_key: Optional[str],
    replicate_api_key: Optional[str],
    should_extract_assets: bool = True,
    recorder: Optional[AgentRunRecorder] = None,
    custom_provider: Optional[CustomProviderConfig] = None,
) -> ProviderSession:
    canonical_tools = canonical_tool_definitions(
        image_generation_enabled=should_generate_images,
        # The edit_images tool calls Replicate, so don't offer it without a key.
        image_editing_enabled=bool(replicate_api_key or REPLICATE_API_KEY),
        # The extract_assets tool calls Gemini, so don't offer it without a key.
        asset_extraction_enabled=should_extract_assets and bool(gemini_api_key),
        # screenshot_preview needs headless Chromium; skip it if it can't launch.
        screenshot_enabled=is_screenshot_preview_available(),
    )

    if model in CUSTOM_MODELS:
        if custom_provider is None or not custom_provider.is_configured:
            raise Exception(
                "Custom provider is not configured. Set a custom API key and "
                "model in the Settings dialog (Customized Provider) or via "
                "the CUSTOM_PROVIDER_API_KEY / CUSTOM_PROVIDER_MODEL env vars."
            )
        if custom_provider.wire_format == "anthropic":
            client = create_custom_anthropic_client(custom_provider)
            return AnthropicProviderSession(
                client=client,
                model=model,
                prompt_messages=prompt_messages,
                tools=serialize_anthropic_tools(canonical_tools),
                recorder=recorder,
                api_model_name=custom_provider.api_model_name,
            )
        # OpenAI-compatible custom providers (OpenAI, xAI, OpenRouter, Ollama,
        # ...) use Chat Completions, the one API every such endpoint speaks.
        client = create_custom_openai_client(custom_provider)
        return OpenAIProviderSession(
            client=client,
            model=model,
            prompt_messages=prompt_messages,
            tools=serialize_openai_chat_tools(canonical_tools),
            recorder=recorder,
            api_model_name=custom_provider.api_model_name,
            use_chat_completions=True,
        )

    if model in OPENAI_MODELS:
        if not openai_api_key:
            raise Exception("OpenAI API key is missing.")

        client = AsyncOpenAI(api_key=openai_api_key, base_url=openai_base_url)
        return OpenAIProviderSession(
            client=client,
            model=model,
            prompt_messages=prompt_messages,
            tools=serialize_openai_tools(canonical_tools),
            recorder=recorder,
        )

    if model in ANTHROPIC_MODELS:
        if not anthropic_api_key:
            raise Exception("Anthropic API key is missing.")

        client = AsyncAnthropic(api_key=anthropic_api_key)
        return AnthropicProviderSession(
            client=client,
            model=model,
            prompt_messages=prompt_messages,
            tools=serialize_anthropic_tools(canonical_tools),
            recorder=recorder,
        )

    if model in GEMINI_MODELS:
        if not gemini_api_key:
            raise Exception("Gemini API key is missing.")

        client = genai.Client(api_key=gemini_api_key)
        return GeminiProviderSession(
            client=client,
            model=model,
            prompt_messages=prompt_messages,
            tools=serialize_gemini_tools(canonical_tools),
            recorder=recorder,
        )

    raise ValueError(f"Unsupported model: {model.value}")
