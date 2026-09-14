jest.mock("../config", () => ({
  HTTP_BACKEND_URL: "http://test-backend",
  IS_RUNNING_ON_CLOUD: false,
}));

import {
  CUSTOM_PROVIDER_FORMAT_FALLBACKS,
  fetchCustomProviderFormats,
  fetchCustomProviderModels,
  resolveCustomProviderFormat,
} from "./customProvider";

describe("resolveCustomProviderFormat", () => {
  test.each(["openai", "anthropic", "xai", "openrouter", "custom"] as const)(
    "keeps the canonical format %s",
    (format) => {
      expect(resolveCustomProviderFormat(format)).toBe(format);
    }
  );

  test.each([null, undefined, "", "azure", "OPENAI"])(
    "falls back to openai for %s",
    (value) => {
      expect(resolveCustomProviderFormat(value as string)).toBe("openai");
    }
  );
});

describe("CUSTOM_PROVIDER_FORMAT_FALLBACKS", () => {
  test("covers every supported format with a wire format", () => {
    const values = CUSTOM_PROVIDER_FORMAT_FALLBACKS.map((option) => option.value);
    expect(values).toEqual(["openai", "anthropic", "xai", "openrouter", "custom"]);
    for (const option of CUSTOM_PROVIDER_FORMAT_FALLBACKS) {
      expect(["openai", "anthropic"]).toContain(option.wire_format);
    }
    expect(
      CUSTOM_PROVIDER_FORMAT_FALLBACKS.find((option) => option.value === "anthropic")
        ?.wire_format
    ).toBe("anthropic");
  });
});

function mockFetchOnce(payload: unknown, ok = true, status = 200) {
  const mock = jest.fn().mockResolvedValue({
    ok,
    status,
    json: async () => payload,
  });
  global.fetch = mock as unknown as typeof fetch;
  return mock;
}

describe("fetchCustomProviderModels", () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  test("posts credentials and returns the model list", async () => {
    const mock = mockFetchOnce({
      models: [
        { id: "b-model", name: null },
        { id: "a-model", name: "A Model" },
      ],
      wire_format: "openai",
    });

    const models = await fetchCustomProviderModels({
      baseUrl: "https://openrouter.ai/api/v1",
      apiKey: "key",
      format: "openrouter",
    });

    expect(mock).toHaveBeenCalledTimes(1);
    const [url, init] = mock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/custom-provider/models");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      base_url: "https://openrouter.ai/api/v1",
      api_key: "key",
      provider_format: "openrouter",
    });
    expect(models).toEqual([
      { id: "b-model", name: null },
      { id: "a-model", name: "A Model" },
    ]);
  });

  test("surfaces the backend error detail", async () => {
    mockFetchOnce({ detail: "Could not reach https://bad.local" }, false, 400);

    await expect(
      fetchCustomProviderModels({ baseUrl: null, apiKey: null, format: "custom" })
    ).rejects.toThrow("Could not reach https://bad.local");
  });
});

describe("fetchCustomProviderFormats", () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  test("returns the backend format list", async () => {
    mockFetchOnce(CUSTOM_PROVIDER_FORMAT_FALLBACKS);

    const formats = await fetchCustomProviderFormats();

    expect(formats).toEqual(CUSTOM_PROVIDER_FORMAT_FALLBACKS);
  });

  test("throws on unexpected payloads", async () => {
    mockFetchOnce({ nope: true });

    await expect(fetchCustomProviderFormats()).rejects.toThrow();
  });
});
