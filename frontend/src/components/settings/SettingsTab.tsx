import React, { useEffect, useState } from "react";
import { BsCheckCircleFill, BsExclamationTriangleFill } from "react-icons/bs";
import {
  AppTheme,
  CustomProviderFormat,
  EditorTheme,
  Settings,
} from "../../types";
import { capitalize } from "../../lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "../ui/select";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Switch } from "../ui/switch";
import { HTTP_BACKEND_URL, IS_RUNNING_ON_CLOUD } from "../../config";
import {
  CUSTOM_PROVIDER_FORMAT_FALLBACKS,
  CustomProviderFormatOption,
  fetchCustomProviderFormats,
  fetchCustomProviderModels,
  resolveCustomProviderFormat,
} from "../../lib/customProvider";

interface Props {
  settings: Settings;
  setSettings: React.Dispatch<React.SetStateAction<Settings>>;
  appTheme: AppTheme;
  setAppTheme: React.Dispatch<React.SetStateAction<AppTheme>>;
}

function SettingsTab({ settings, setSettings, appTheme, setAppTheme }: Props) {
  // null = not yet known (loading / unreachable); otherwise the backend's answer.
  const [screenshotPreviewAvailable, setScreenshotPreviewAvailable] = useState<
    boolean | null
  >(null);

  // Customized Provider state. Formats come from the backend with a static
  // fallback so the dropdown works even if the backend is unreachable.
  const [customProviderFormats, setCustomProviderFormats] = useState<
    CustomProviderFormatOption[]
  >(CUSTOM_PROVIDER_FORMAT_FALLBACKS);
  const [isFetchingCustomModels, setIsFetchingCustomModels] = useState(false);
  const [customModelsError, setCustomModelsError] = useState<string | null>(null);
  const [customModelsNotice, setCustomModelsNotice] = useState<string | null>(
    null
  );

  useEffect(() => {
    let cancelled = false;
    fetch(`${HTTP_BACKEND_URL}/api/capabilities`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!cancelled && data && typeof data.screenshot_preview === "boolean") {
          setScreenshotPreviewAvailable(data.screenshot_preview);
        }
      })
      .catch(() => {
        /* leave as null — don't show a false alarm if the backend is unreachable */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchCustomProviderFormats()
      .then((formats) => {
        if (!cancelled && formats.length > 0) {
          setCustomProviderFormats(formats);
        }
      })
      .catch(() => {
        /* keep the static fallback list */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const customProviderFormat = resolveCustomProviderFormat(
    settings.customProviderFormat
  );
  const customProviderFormatOption = customProviderFormats.find(
    (option) => option.value === customProviderFormat
  );
  const customProviderDefaultBaseUrl =
    customProviderFormatOption?.default_base_url || "";
  const customProviderModels = settings.customProviderModels || [];
  const isCustomProviderActive = Boolean(
    settings.customProviderApiKey?.trim() && settings.customProviderModel?.trim()
  );

  const handleFetchCustomModels = async () => {
    setIsFetchingCustomModels(true);
    setCustomModelsError(null);
    setCustomModelsNotice(null);
    try {
      const models = await fetchCustomProviderModels({
        baseUrl: settings.customProviderBaseUrl,
        apiKey: settings.customProviderApiKey,
        format: customProviderFormat,
      });
      setSettings((s) => ({
        ...s,
        customProviderModels: models.map((model) => model.id),
      }));
      if (models.length === 0) {
        setCustomModelsNotice(
          "Connected, but the endpoint returned no models. You can still type a model id manually."
        );
      } else {
        setCustomModelsNotice(
          `Found ${models.length} model${models.length === 1 ? "" : "s"}.`
        );
      }
    } catch (error) {
      setCustomModelsError(
        error instanceof Error ? error.message : "Failed to fetch models."
      );
    } finally {
      setIsFetchingCustomModels(false);
    }
  };

  const handleThemeChange = (theme: EditorTheme) => {
    setSettings((s) => ({
      ...s,
      editorTheme: theme,
    }));
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="px-4 py-4 lg:px-6 lg:py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            Settings
          </h1>
        </div>

        <div className="mx-auto max-w-lg space-y-6">
          {/* Theme */}
          <div className="rounded-lg border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-800/60">
            <div className="border-b border-gray-100 px-4 py-3 dark:border-zinc-700">
              <h2 className="text-sm font-medium text-gray-900 dark:text-white">
                Theme
              </h2>
            </div>
            <div className="divide-y divide-gray-100 dark:divide-zinc-700">
              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <span className="text-sm text-gray-700 dark:text-zinc-300">
                    App Theme
                  </span>
                  <p className="mt-0.5 text-xs text-gray-500 dark:text-zinc-400">
                    System default, with optional light/dark override
                  </p>
                </div>
                <Select
                  name="app-theme"
                  value={appTheme}
                  onValueChange={(value) => setAppTheme(value as AppTheme)}
                >
                  <SelectTrigger className="w-[140px]">
                    {capitalize(appTheme)}
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={AppTheme.SYSTEM}>System</SelectItem>
                    <SelectItem value={AppTheme.LIGHT}>Light</SelectItem>
                    <SelectItem value={AppTheme.DARK}>Dark</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <span className="text-sm text-gray-700 dark:text-zinc-300">
                    Code Editor Theme
                  </span>
                  <p className="mt-0.5 text-xs text-gray-500 dark:text-zinc-400">
                    Requires page refresh to update
                  </p>
                </div>
                <Select
                  name="editor-theme"
                  value={settings.editorTheme}
                  onValueChange={(value) =>
                    handleThemeChange(value as EditorTheme)
                  }
                >
                  <SelectTrigger className="w-[140px]">
                    <span className="notranslate" translate="no">
                      {capitalize(settings.editorTheme)}
                    </span>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cobalt">
                      <span className="notranslate" translate="no">Cobalt</span>
                    </SelectItem>
                    <SelectItem value="espresso">
                      <span className="notranslate" translate="no">Espresso</span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* API Keys */}
          <div className="rounded-lg border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-800/60">
            <div className="border-b border-gray-100 px-4 py-3 dark:border-zinc-700">
              <h2 className="text-sm font-medium text-gray-900 dark:text-white">
                API Keys
              </h2>
            </div>
            <div className="space-y-4 p-4">
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-zinc-300">
                  OpenAI API key
                </p>
                <p className="mt-1 text-xs text-gray-500 dark:text-zinc-400">
                  Only stored in your browser. Never stored on servers. Overrides
                  your .env config.
                </p>
                <Input
                  id="openai-api-key"
                  className="mt-2"
                  placeholder="OpenAI API key"
                  value={settings.openAiApiKey || ""}
                  onChange={(e) =>
                    setSettings((s) => ({
                      ...s,
                      openAiApiKey: e.target.value,
                    }))
                  }
                />
              </div>

              {!IS_RUNNING_ON_CLOUD && (
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-zinc-300">
                    OpenAI Base URL (optional)
                  </p>
                  <p className="mt-1 text-xs text-gray-500 dark:text-zinc-400">
                    Replace with a proxy URL if you don't want to use the
                    default.
                  </p>
                  <Input
                    id="openai-base-url"
                    className="mt-2"
                    placeholder="OpenAI Base URL"
                    value={settings.openAiBaseURL || ""}
                    onChange={(e) =>
                      setSettings((s) => ({
                        ...s,
                        openAiBaseURL: e.target.value,
                      }))
                    }
                  />
                </div>
              )}

              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-zinc-300">
                  Anthropic API key
                </p>
                <p className="mt-1 text-xs text-gray-500 dark:text-zinc-400">
                  Only stored in your browser. Never stored on servers. Overrides
                  your .env config.
                </p>
                <Input
                  id="anthropic-api-key"
                  className="mt-2"
                  placeholder="Anthropic API key"
                  value={settings.anthropicApiKey || ""}
                  onChange={(e) =>
                    setSettings((s) => ({
                      ...s,
                      anthropicApiKey: e.target.value,
                    }))
                  }
                />
              </div>

              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-zinc-300">
                  Gemini API key
                </p>
                <p className="mt-1 text-xs text-gray-500 dark:text-zinc-400">
                  Only stored in your browser. Never stored on servers. Overrides
                  your .env config.
                </p>
                <Input
                  id="gemini-api-key"
                  className="mt-2"
                  placeholder="Gemini API key"
                  value={settings.geminiApiKey || ""}
                  onChange={(e) =>
                    setSettings((s) => ({
                      ...s,
                      geminiApiKey: e.target.value,
                    }))
                  }
                />
              </div>

              {!IS_RUNNING_ON_CLOUD && (
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-zinc-300">
                    Replicate API key
                  </p>
                  <p className="mt-1 text-xs text-gray-500 dark:text-zinc-400">
                    Only stored in your browser. Never stored on servers. Overrides
                    your .env config for image generation and editing.
                  </p>
                  <Input
                    id="replicate-api-key"
                    className="mt-2"
                    placeholder="Replicate API key"
                    value={settings.replicateApiKey || ""}
                    onChange={(e) =>
                      setSettings((s) => ({
                        ...s,
                        replicateApiKey: e.target.value,
                      }))
                    }
                  />
                </div>
              )}
            </div>
          </div>

          {/* Customized Provider */}
          <div className="rounded-lg border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-800/60">
            <div className="border-b border-gray-100 px-4 py-3 dark:border-zinc-700">
              <h2 className="text-sm font-medium text-gray-900 dark:text-white">
                Customized Provider
              </h2>
            </div>
            <div className="space-y-4 p-4">
              <p className="text-xs text-gray-500 dark:text-zinc-400">
                Point code generation at any OpenAI- or Anthropic-compatible
                endpoint (OpenAI, Anthropic, xAI, OpenRouter, Ollama, vLLM, or
                your own gateway). When a custom API key and model are set, all
                variants use your custom provider.
              </p>

              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-zinc-300">
                  Provider format
                </p>
                <Select
                  name="custom-provider-format"
                  value={customProviderFormat}
                  onValueChange={(value) => {
                    setSettings((s) => ({
                      ...s,
                      customProviderFormat: value as CustomProviderFormat,
                    }));
                    setCustomModelsNotice(null);
                    setCustomModelsError(null);
                  }}
                >
                  <SelectTrigger
                    id="custom-provider-format"
                    className="mt-2 w-full"
                  >
                    {customProviderFormatOption?.label ?? "Select a format"}
                  </SelectTrigger>
                  <SelectContent>
                    {customProviderFormats.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-zinc-300">
                  Base URL
                </p>
                <p className="mt-1 text-xs text-gray-500 dark:text-zinc-400">
                  {customProviderDefaultBaseUrl
                    ? `Leave blank to use the default (${customProviderDefaultBaseUrl}).`
                    : "Required for this format, e.g. https://your-host/v1."}
                </p>
                <Input
                  id="custom-provider-base-url"
                  className="mt-2"
                  placeholder={
                    customProviderDefaultBaseUrl || "https://your-host/v1"
                  }
                  value={settings.customProviderBaseUrl || ""}
                  onChange={(e) =>
                    setSettings((s) => ({
                      ...s,
                      customProviderBaseUrl: e.target.value,
                    }))
                  }
                />
              </div>

              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-zinc-300">
                  API key
                </p>
                <p className="mt-1 text-xs text-gray-500 dark:text-zinc-400">
                  Only stored in your browser. Never stored on servers.
                </p>
                <Input
                  id="custom-provider-api-key"
                  className="mt-2"
                  type="password"
                  placeholder="Custom provider API key"
                  value={settings.customProviderApiKey || ""}
                  onChange={(e) =>
                    setSettings((s) => ({
                      ...s,
                      customProviderApiKey: e.target.value,
                    }))
                  }
                />
              </div>

              <div>
                <div className="flex items-end justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-zinc-300">
                      Model
                    </p>
                    <p className="mt-1 text-xs text-gray-500 dark:text-zinc-400">
                      Fetch the model list from your endpoint, then pick one —
                      or type any model id manually.
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="shrink-0"
                    onClick={handleFetchCustomModels}
                    disabled={isFetchingCustomModels}
                  >
                    {isFetchingCustomModels ? "Fetching…" : "Fetch models"}
                  </Button>
                </div>
                <Input
                  id="custom-provider-model"
                  className="mt-2"
                  list="custom-provider-models"
                  placeholder={
                    customProviderModels.length > 0
                      ? "Select or type a model id"
                      : "e.g. gpt-4o, claude-opus-4-8, xai/grok-4"
                  }
                  value={settings.customProviderModel || ""}
                  onChange={(e) =>
                    setSettings((s) => ({
                      ...s,
                      customProviderModel: e.target.value,
                    }))
                  }
                />
                <datalist id="custom-provider-models">
                  {customProviderModels.map((model) => (
                    <option key={model} value={model} />
                  ))}
                </datalist>
                {customModelsError && (
                  <p className="mt-2 text-xs text-red-600 dark:text-red-400">
                    {customModelsError}
                  </p>
                )}
                {customModelsNotice && !customModelsError && (
                  <p className="mt-2 text-xs text-gray-500 dark:text-zinc-400">
                    {customModelsNotice}
                  </p>
                )}
                {isCustomProviderActive && (
                  <div className="mt-2 flex items-start gap-2.5 rounded-md border border-emerald-300 bg-emerald-50 p-3 dark:border-emerald-700/60 dark:bg-emerald-900/20">
                    <BsCheckCircleFill className="mt-0.5 shrink-0 text-emerald-500" />
                    <p className="text-xs text-emerald-800 dark:text-emerald-200">
                      Custom provider active — all variants will use{" "}
                      <span className="font-mono font-medium">
                        {settings.customProviderModel}
                      </span>
                      .
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Image Generation */}
          <div className="rounded-lg border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-800/60">
            <div className="border-b border-gray-100 px-4 py-3 dark:border-zinc-700">
              <h2 className="text-sm font-medium text-gray-900 dark:text-white">
                Image Generation
              </h2>
            </div>
            <div className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-700 dark:text-zinc-300">
                    Placeholder Images
                  </p>
                  <p className="mt-1 text-xs text-gray-500 dark:text-zinc-400">
                    More fun with it but if you want to save money, turn it off.
                  </p>
                </div>
                <Switch
                  id="image-generation"
                  checked={settings.isImageGenerationEnabled}
                  onCheckedChange={(checked) =>
                    setSettings((s) => ({
                      ...s,
                      isImageGenerationEnabled: checked,
                    }))
                  }
                />
              </div>
            </div>
          </div>

          {/* Screenshot Preview (agent self-verification) */}
          <div className="rounded-lg border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-800/60">
            <div className="border-b border-gray-100 px-4 py-3 dark:border-zinc-700">
              <h2 className="text-sm font-medium text-gray-900 dark:text-white">
                Screenshot Preview
              </h2>
            </div>
            <div className="p-4">
              {screenshotPreviewAvailable === false ? (
                <div className="flex items-start gap-2.5 rounded-md border border-amber-300 bg-amber-50 p-3 dark:border-amber-700/60 dark:bg-amber-900/20">
                  <BsExclamationTriangleFill className="mt-0.5 shrink-0 text-amber-500" />
                  <div>
                    <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                      Screenshot preview is unavailable
                    </p>
                    <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">
                      Headless Chromium isn't installed on the backend, so the
                      agent can't render and visually verify its own output.
                      Install it with{" "}
                      <code className="rounded bg-amber-100 px-1 py-0.5 font-mono dark:bg-amber-900/40">
                        playwright install chromium
                      </code>{" "}
                      and restart the backend.
                    </p>
                  </div>
                </div>
              ) : screenshotPreviewAvailable === true ? (
                <div className="flex items-start gap-2.5">
                  <BsCheckCircleFill className="mt-0.5 shrink-0 text-emerald-500" />
                  <div>
                    <p className="text-sm text-gray-700 dark:text-zinc-300">
                      Available
                    </p>
                    <p className="mt-1 text-xs text-gray-500 dark:text-zinc-400">
                      The agent renders your generated page in a headless browser
                      to visually check its work and fix layout issues.
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-gray-500 dark:text-zinc-400">
                  Checking backend capabilities…
                </p>
              )}
            </div>
          </div>

          {/* Screenshot by URL */}
          <div className="rounded-lg border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-800/60">
            <div className="border-b border-gray-100 px-4 py-3 dark:border-zinc-700">
              <h2 className="text-sm font-medium text-gray-900 dark:text-white">
                Screenshot by URL
              </h2>
            </div>
            <div className="p-4">
              <p className="text-xs text-gray-500 dark:text-zinc-400">
                If you want to use URLs directly instead of taking the screenshot
                yourself, add a ScreenshotOne API key.{" "}
                <a
                  href="https://screenshotone.com?via=screenshot-to-code"
                  className="text-violet-600 hover:text-violet-700 dark:text-violet-400 dark:hover:text-violet-300"
                  target="_blank"
                >
                  Get 100 screenshots/mo for free.
                </a>
              </p>
              <Input
                id="screenshot-one-api-key"
                className="mt-3"
                placeholder="ScreenshotOne API key"
                value={settings.screenshotOneApiKey || ""}
                onChange={(e) =>
                  setSettings((s) => ({
                    ...s,
                    screenshotOneApiKey: e.target.value,
                  }))
                }
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsTab;
