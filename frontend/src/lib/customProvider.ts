import { HTTP_BACKEND_URL } from "../config";
import { CustomProviderFormat } from "../types";

export interface CustomProviderFormatOption {
  value: CustomProviderFormat;
  label: string;
  default_base_url: string;
  wire_format: "openai" | "anthropic";
}

export interface CustomProviderModelOption {
  id: string;
  name: string | null;
}

// Static fallback used when the backend is unreachable. Keep in sync with
// backend (llm.py CUSTOM_PROVIDER_FORMAT_LABELS / DEFAULT_BASE_URLS).
export const CUSTOM_PROVIDER_FORMAT_FALLBACKS: CustomProviderFormatOption[] = [
  {
    value: "openai",
    label: "OpenAI-compatible",
    default_base_url: "https://api.openai.com/v1",
    wire_format: "openai",
  },
  {
    value: "anthropic",
    label: "Anthropic-compatible",
    default_base_url: "https://api.anthropic.com",
    wire_format: "anthropic",
  },
  {
    value: "xai",
    label: "xAI",
    default_base_url: "https://api.x.ai/v1",
    wire_format: "openai",
  },
  {
    value: "openrouter",
    label: "OpenRouter",
    default_base_url: "https://openrouter.ai/api/v1",
    wire_format: "openai",
  },
  {
    value: "custom",
    label: "Custom (OpenAI-compatible)",
    default_base_url: "",
    wire_format: "openai",
  },
];

function isFormatOption(value: unknown): value is CustomProviderFormatOption {
  if (typeof value !== "object" || value === null) return false;
  const option = value as Record<string, unknown>;
  return (
    typeof option.value === "string" &&
    typeof option.label === "string" &&
    typeof option.default_base_url === "string" &&
    (option.wire_format === "openai" || option.wire_format === "anthropic")
  );
}

export async function fetchCustomProviderFormats(): Promise<
  CustomProviderFormatOption[]
> {
  const response = await fetch(`${HTTP_BACKEND_URL}/api/custom-provider/formats`);
  if (!response.ok) {
    throw new Error(`Backend returned HTTP ${response.status}`);
  }
  const payload: unknown = await response.json();
  if (!Array.isArray(payload) || !payload.every(isFormatOption)) {
    throw new Error("Unexpected response from the backend.");
  }
  return payload;
}

function isModelOption(value: unknown): value is CustomProviderModelOption {
  if (typeof value !== "object" || value === null) return false;
  const option = value as Record<string, unknown>;
  return (
    typeof option.id === "string" &&
    (option.name === null ||
      option.name === undefined ||
      typeof option.name === "string")
  );
}

export async function fetchCustomProviderModels(args: {
  baseUrl: string | null;
  apiKey: string | null;
  format: CustomProviderFormat;
}): Promise<CustomProviderModelOption[]> {
  const response = await fetch(`${HTTP_BACKEND_URL}/api/custom-provider/models`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      base_url: args.baseUrl || null,
      api_key: args.apiKey || null,
      provider_format: args.format,
    }),
  });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null
        ? (payload as Record<string, unknown>).detail
        : null;
    throw new Error(
      typeof detail === "string" && detail
        ? detail
        : `Backend returned HTTP ${response.status}`
    );
  }
  const models =
    typeof payload === "object" && payload !== null
      ? (payload as Record<string, unknown>).models
      : null;
  if (!Array.isArray(models) || !models.every(isModelOption)) {
    throw new Error("Unexpected response from the backend.");
  }
  return models;
}

export function resolveCustomProviderFormat(
  value: string | null | undefined
): CustomProviderFormat {
  switch (value) {
    case "openai":
    case "anthropic":
    case "xai":
    case "openrouter":
    case "custom":
      return value;
    default:
      return "openai";
  }
}
