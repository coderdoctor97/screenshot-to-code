from dataclasses import dataclass
from enum import Enum
from typing import Literal, TypedDict


# Actual model versions that are passed to the LLMs and stored in our logs
class Llm(Enum):
    # Custom provider (user-configured Base URL / API key / model).
    # The concrete model id lives on CustomProviderConfig, not in this enum.
    CUSTOM = "custom"
    # GPT
    GPT_5_4_MINI_LOW = "gpt-5.4-mini (low thinking)"
    GPT_5_4_2026_03_05_NONE = "gpt-5.4-2026-03-05 (no thinking)"
    GPT_5_4_2026_03_05_LOW = "gpt-5.4-2026-03-05 (low thinking)"
    GPT_5_4_2026_03_05_MEDIUM = "gpt-5.4-2026-03-05 (medium thinking)"
    GPT_5_4_2026_03_05_HIGH = "gpt-5.4-2026-03-05 (high thinking)"
    GPT_5_4_2026_03_05_XHIGH = "gpt-5.4-2026-03-05 (xhigh thinking)"
    GPT_5_5_NONE = "gpt-5.5 (no thinking)"
    GPT_5_5_LOW = "gpt-5.5 (low thinking)"
    GPT_5_5_MEDIUM = "gpt-5.5 (medium thinking)"
    GPT_5_5_HIGH = "gpt-5.5 (high thinking)"
    GPT_5_5_XHIGH = "gpt-5.5 (xhigh thinking)"
    GPT_5_6_SOL_NONE = "gpt-5.6-sol (no thinking)"
    GPT_5_6_SOL_LOW = "gpt-5.6-sol (low thinking)"
    GPT_5_6_SOL_MEDIUM = "gpt-5.6-sol (medium thinking)"
    GPT_5_6_SOL_HIGH = "gpt-5.6-sol (high thinking)"
    GPT_5_6_SOL_XHIGH = "gpt-5.6-sol (xhigh thinking)"
    GPT_5_6_SOL_MAX = "gpt-5.6-sol (max thinking)"
    GPT_5_6_TERRA_LOW = "gpt-5.6-terra (low thinking)"
    # Claude
    CLAUDE_SONNET_4_6 = "claude-sonnet-4-6"
    CLAUDE_OPUS_5_LOW = "claude-opus-5 (low effort)"
    CLAUDE_OPUS_5_MEDIUM = "claude-opus-5 (medium effort)"
    CLAUDE_OPUS_5_HIGH = "claude-opus-5 (high effort)"
    CLAUDE_OPUS_5_XHIGH = "claude-opus-5 (xhigh effort)"
    CLAUDE_OPUS_5_MAX = "claude-opus-5 (max effort)"
    CLAUDE_OPUS_4_8_LOW = "claude-opus-4-8 (low effort)"
    CLAUDE_OPUS_4_8_MEDIUM = "claude-opus-4-8 (medium effort)"
    CLAUDE_OPUS_4_8_HIGH = "claude-opus-4-8 (high effort)"
    CLAUDE_OPUS_4_8_XHIGH = "claude-opus-4-8 (xhigh effort)"
    CLAUDE_OPUS_4_8_MAX = "claude-opus-4-8 (max effort)"
    CLAUDE_FABLE_5_LOW = "claude-fable-5 (low effort)"
    CLAUDE_FABLE_5_MEDIUM = "claude-fable-5 (medium effort)"
    CLAUDE_FABLE_5_HIGH = "claude-fable-5 (high effort)"
    CLAUDE_FABLE_5_XHIGH = "claude-fable-5 (xhigh effort)"
    CLAUDE_FABLE_5_MAX = "claude-fable-5 (max effort)"
    # Gemini
    GEMINI_3_FLASH_PREVIEW_HIGH = "gemini-3-flash-preview (high thinking)"
    GEMINI_3_FLASH_PREVIEW_MINIMAL = "gemini-3-flash-preview (minimal thinking)"
    GEMINI_3_1_PRO_PREVIEW_HIGH = "gemini-3.1-pro-preview (high thinking)"
    GEMINI_3_1_PRO_PREVIEW_MEDIUM = "gemini-3.1-pro-preview (medium thinking)"
    GEMINI_3_1_PRO_PREVIEW_LOW = "gemini-3.1-pro-preview (low thinking)"
    GEMINI_3_5_FLASH_HIGH = "gemini-3.5-flash (high thinking)"
    GEMINI_3_5_FLASH_MEDIUM = "gemini-3.5-flash (medium thinking)"
    GEMINI_3_5_FLASH_LOW = "gemini-3.5-flash (low thinking)"
    GEMINI_3_5_FLASH_MINIMAL = "gemini-3.5-flash (minimal thinking)"
    GEMINI_3_6_FLASH_HIGH = "gemini-3.6-flash (high thinking)"
    GEMINI_3_6_FLASH_MEDIUM = "gemini-3.6-flash (medium thinking)"
    GEMINI_3_6_FLASH_LOW = "gemini-3.6-flash (low thinking)"
    GEMINI_3_6_FLASH_MINIMAL = "gemini-3.6-flash (minimal thinking)"


class Completion(TypedDict):
    duration: float
    code: str


# Explicitly map each model to the provider backing it.  This keeps provider
# groupings authoritative and avoids relying on name conventions when checking
# models elsewhere in the codebase.
MODEL_PROVIDER: dict[Llm, str] = {
    # Custom provider models (routed dynamically by CustomProviderConfig)
    Llm.CUSTOM: "custom",
    # OpenAI models
    Llm.GPT_5_4_MINI_LOW: "openai",
    Llm.GPT_5_4_2026_03_05_NONE: "openai",
    Llm.GPT_5_4_2026_03_05_LOW: "openai",
    Llm.GPT_5_4_2026_03_05_MEDIUM: "openai",
    Llm.GPT_5_4_2026_03_05_HIGH: "openai",
    Llm.GPT_5_4_2026_03_05_XHIGH: "openai",
    Llm.GPT_5_5_NONE: "openai",
    Llm.GPT_5_5_LOW: "openai",
    Llm.GPT_5_5_MEDIUM: "openai",
    Llm.GPT_5_5_HIGH: "openai",
    Llm.GPT_5_5_XHIGH: "openai",
    Llm.GPT_5_6_SOL_NONE: "openai",
    Llm.GPT_5_6_SOL_LOW: "openai",
    Llm.GPT_5_6_SOL_MEDIUM: "openai",
    Llm.GPT_5_6_SOL_HIGH: "openai",
    Llm.GPT_5_6_SOL_XHIGH: "openai",
    Llm.GPT_5_6_SOL_MAX: "openai",
    Llm.GPT_5_6_TERRA_LOW: "openai",
    # Anthropic models
    Llm.CLAUDE_SONNET_4_6: "anthropic",
    Llm.CLAUDE_OPUS_5_LOW: "anthropic",
    Llm.CLAUDE_OPUS_5_MEDIUM: "anthropic",
    Llm.CLAUDE_OPUS_5_HIGH: "anthropic",
    Llm.CLAUDE_OPUS_5_XHIGH: "anthropic",
    Llm.CLAUDE_OPUS_5_MAX: "anthropic",
    Llm.CLAUDE_OPUS_4_8_LOW: "anthropic",
    Llm.CLAUDE_OPUS_4_8_MEDIUM: "anthropic",
    Llm.CLAUDE_OPUS_4_8_HIGH: "anthropic",
    Llm.CLAUDE_OPUS_4_8_XHIGH: "anthropic",
    Llm.CLAUDE_OPUS_4_8_MAX: "anthropic",
    Llm.CLAUDE_FABLE_5_LOW: "anthropic",
    Llm.CLAUDE_FABLE_5_MEDIUM: "anthropic",
    Llm.CLAUDE_FABLE_5_HIGH: "anthropic",
    Llm.CLAUDE_FABLE_5_XHIGH: "anthropic",
    Llm.CLAUDE_FABLE_5_MAX: "anthropic",
    # Gemini models
    Llm.GEMINI_3_FLASH_PREVIEW_HIGH: "gemini",
    Llm.GEMINI_3_FLASH_PREVIEW_MINIMAL: "gemini",
    Llm.GEMINI_3_1_PRO_PREVIEW_HIGH: "gemini",
    Llm.GEMINI_3_1_PRO_PREVIEW_MEDIUM: "gemini",
    Llm.GEMINI_3_1_PRO_PREVIEW_LOW: "gemini",
    Llm.GEMINI_3_5_FLASH_HIGH: "gemini",
    Llm.GEMINI_3_5_FLASH_MEDIUM: "gemini",
    Llm.GEMINI_3_5_FLASH_LOW: "gemini",
    Llm.GEMINI_3_5_FLASH_MINIMAL: "gemini",
    Llm.GEMINI_3_6_FLASH_HIGH: "gemini",
    Llm.GEMINI_3_6_FLASH_MEDIUM: "gemini",
    Llm.GEMINI_3_6_FLASH_LOW: "gemini",
    Llm.GEMINI_3_6_FLASH_MINIMAL: "gemini",
}

# Convenience sets for membership checks
OPENAI_MODELS = {m for m, p in MODEL_PROVIDER.items() if p == "openai"}
ANTHROPIC_MODELS = {m for m, p in MODEL_PROVIDER.items() if p == "anthropic"}
GEMINI_MODELS = {m for m, p in MODEL_PROVIDER.items() if p == "gemini"}
CUSTOM_MODELS = {m for m, p in MODEL_PROVIDER.items() if p == "custom"}

OPENAI_MODEL_CONFIG: dict[Llm, dict[str, str]] = {
    Llm.GPT_5_4_MINI_LOW: {"api_name": "gpt-5.4-mini", "reasoning_effort": "low"},
    Llm.GPT_5_4_2026_03_05_NONE: {
        "api_name": "gpt-5.4-2026-03-05",
        "reasoning_effort": "none",
    },
    Llm.GPT_5_4_2026_03_05_LOW: {
        "api_name": "gpt-5.4-2026-03-05",
        "reasoning_effort": "low",
    },
    Llm.GPT_5_4_2026_03_05_MEDIUM: {
        "api_name": "gpt-5.4-2026-03-05",
        "reasoning_effort": "medium",
    },
    Llm.GPT_5_4_2026_03_05_HIGH: {
        "api_name": "gpt-5.4-2026-03-05",
        "reasoning_effort": "high",
    },
    Llm.GPT_5_4_2026_03_05_XHIGH: {
        "api_name": "gpt-5.4-2026-03-05",
        "reasoning_effort": "xhigh",
    },
    Llm.GPT_5_5_NONE: {"api_name": "gpt-5.5", "reasoning_effort": "none"},
    Llm.GPT_5_5_LOW: {"api_name": "gpt-5.5", "reasoning_effort": "low"},
    Llm.GPT_5_5_MEDIUM: {"api_name": "gpt-5.5", "reasoning_effort": "medium"},
    Llm.GPT_5_5_HIGH: {"api_name": "gpt-5.5", "reasoning_effort": "high"},
    Llm.GPT_5_5_XHIGH: {"api_name": "gpt-5.5", "reasoning_effort": "xhigh"},
    Llm.GPT_5_6_SOL_NONE: {"api_name": "gpt-5.6-sol", "reasoning_effort": "none"},
    Llm.GPT_5_6_SOL_LOW: {"api_name": "gpt-5.6-sol", "reasoning_effort": "low"},
    Llm.GPT_5_6_SOL_MEDIUM: {"api_name": "gpt-5.6-sol", "reasoning_effort": "medium"},
    Llm.GPT_5_6_SOL_HIGH: {"api_name": "gpt-5.6-sol", "reasoning_effort": "high"},
    Llm.GPT_5_6_SOL_XHIGH: {"api_name": "gpt-5.6-sol", "reasoning_effort": "xhigh"},
    Llm.GPT_5_6_SOL_MAX: {"api_name": "gpt-5.6-sol", "reasoning_effort": "max"},
    Llm.GPT_5_6_TERRA_LOW: {"api_name": "gpt-5.6-terra", "reasoning_effort": "low"},
}


def get_openai_api_name(model: Llm) -> str:
    return OPENAI_MODEL_CONFIG[model]["api_name"]


def get_openai_reasoning_effort(model: Llm) -> str | None:
    return OPENAI_MODEL_CONFIG.get(model, {}).get("reasoning_effort")


# ---------------------------------------------------------------------------
# Custom provider support
#
# A custom provider lets the user point code generation at any OpenAI- or
# Anthropic-compatible endpoint (OpenAI, Anthropic, xAI, OpenRouter, Ollama,
# vLLM, LM Studio, LiteLLM, ...). The user configures a Base URL, an API key,
# a provider format, and a model id in the Settings UI (or via the
# CUSTOM_PROVIDER_* env vars); everything here is resolved dynamically at
# request time instead of from the fixed Llm enum above.
# ---------------------------------------------------------------------------

CustomProviderFormat = Literal["openai", "anthropic", "xai", "openrouter", "custom"]

CUSTOM_PROVIDER_FORMATS: tuple[str, ...] = (
    "openai",
    "anthropic",
    "xai",
    "openrouter",
    "custom",
)

CUSTOM_PROVIDER_FORMAT_LABELS: dict[str, str] = {
    "openai": "OpenAI-compatible",
    "anthropic": "Anthropic-compatible",
    "xai": "xAI",
    "openrouter": "OpenRouter",
    "custom": "Custom (OpenAI-compatible)",
}

# Default Base URLs applied when the user leaves the Base URL blank.
CUSTOM_PROVIDER_DEFAULT_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "xai": "https://api.x.ai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "custom": "",
}

# Formats that speak the Anthropic Messages wire format. Everything else
# (including "custom") speaks the OpenAI Chat Completions wire format.
ANTHROPIC_WIRE_FORMATS = frozenset({"anthropic"})

DEFAULT_CUSTOM_PROVIDER_FORMAT = "openai"

# Accepted aliases (e.g. from env vars) for the canonical format names.
_CUSTOM_PROVIDER_FORMAT_ALIASES: dict[str, str] = {
    "openai-compatible": "openai",
    "openai_compatible": "openai",
    "anthropic-compatible": "anthropic",
    "anthropic_compatible": "anthropic",
    "x-ai": "xai",
    "open-router": "openrouter",
    "open_router": "openrouter",
}


def normalize_custom_provider_format(value: str | None) -> str:
    """Return the canonical provider format name for a user-supplied value."""
    if not value or not isinstance(value, str):
        return DEFAULT_CUSTOM_PROVIDER_FORMAT
    normalized = value.strip().lower()
    if not normalized:
        return DEFAULT_CUSTOM_PROVIDER_FORMAT
    if normalized in CUSTOM_PROVIDER_FORMATS:
        return normalized
    if normalized in _CUSTOM_PROVIDER_FORMAT_ALIASES:
        return _CUSTOM_PROVIDER_FORMAT_ALIASES[normalized]
    # Unknown formats are treated as generic OpenAI-compatible endpoints.
    return "custom"


def custom_provider_wire_format(
    provider_format: str | None,
) -> Literal["openai", "anthropic"]:
    """Return the API wire format ("openai" or "anthropic") for a format name."""
    if normalize_custom_provider_format(provider_format) in ANTHROPIC_WIRE_FORMATS:
        return "anthropic"
    return "openai"


def _clean_custom_provider_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


@dataclass
class CustomProviderConfig:
    """User-configured custom provider credentials (UI settings or env)."""

    base_url: str | None = None
    api_key: str | None = None
    provider_format: str = DEFAULT_CUSTOM_PROVIDER_FORMAT
    model: str | None = None

    @classmethod
    def from_values(
        cls,
        base_url: object = None,
        api_key: object = None,
        provider_format: object = None,
        model: object = None,
    ) -> "CustomProviderConfig":
        """Build a config from raw UI/env values (whitespace-tolerant)."""
        return cls(
            base_url=_clean_custom_provider_value(base_url),
            api_key=_clean_custom_provider_value(api_key),
            provider_format=normalize_custom_provider_format(
                provider_format if isinstance(provider_format, str) else None
            ),
            model=_clean_custom_provider_value(model),
        )

    @property
    def is_configured(self) -> bool:
        """Whether generation can run on this provider (key + model set)."""
        return bool(self.api_key and self.model)

    @property
    def wire_format(self) -> Literal["openai", "anthropic"]:
        return custom_provider_wire_format(self.provider_format)

    @property
    def effective_base_url(self) -> str | None:
        """Explicit Base URL, or the default for the chosen format (if any)."""
        if self.base_url:
            return self.base_url.rstrip("/")
        default = CUSTOM_PROVIDER_DEFAULT_BASE_URLS.get(self.provider_format, "")
        return default or None

    @property
    def api_model_name(self) -> str:
        return self.model or ""


def create_custom_openai_client(config: CustomProviderConfig):
    """Build an AsyncOpenAI client for a custom OpenAI-compatible endpoint.

    The openai package is imported lazily so this module stays importable
    without third-party dependencies installed.
    """
    from openai import AsyncOpenAI

    if not config.api_key:
        raise ValueError("Custom provider API key is missing.")
    return AsyncOpenAI(api_key=config.api_key, base_url=config.effective_base_url)


def create_custom_anthropic_client(config: CustomProviderConfig):
    """Build an AsyncAnthropic client for a custom Anthropic-compatible endpoint."""
    from anthropic import AsyncAnthropic

    if not config.api_key:
        raise ValueError("Custom provider API key is missing.")
    kwargs: dict[str, str] = {"api_key": config.api_key}
    if config.effective_base_url:
        kwargs["base_url"] = config.effective_base_url
    return AsyncAnthropic(**kwargs)  # type: ignore[arg-type]


def create_custom_provider_client(config: CustomProviderConfig):
    """Route to the OpenAI or Anthropic SDK client for a custom provider."""
    if config.wire_format == "anthropic":
        return create_custom_anthropic_client(config)
    return create_custom_openai_client(config)
