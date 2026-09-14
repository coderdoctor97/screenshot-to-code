# screenshot-to-code

Convert screenshots, mockups, Figma designs, and screen recordings into clean, functional code using AI. The easiest way to try this is using <a href="https://screenshottocode.com/?utm_source=github&utm_medium=readme&utm_campaign=oss_readme&utm_content=top_cta" target="_blank" rel="noopener noreferrer">the official, hosted product at screenshottocode.com →</a>


https://github.com/user-attachments/assets/ec08a5e6-9606-41c5-b03a-1bf47dfeba75


Supported stacks:

- HTML + Tailwind
- HTML + CSS
- React + Tailwind
- Vue + Tailwind
- Bootstrap
- Ionic + Tailwind

AI models are fully configurable: use the **Customized Provider** section in the
in-app Settings (gear icon) to point code generation at any OpenAI- or
Anthropic-compatible endpoint — OpenAI, Anthropic, xAI, OpenRouter, Ollama,
vLLM, or your own gateway — by setting a Base URL, API key, provider format,
and model. z-image-turbo (using Replicate) is used for image generation.

See the [Examples](#-examples) section below for more demos.

Screenshot to Code also supports taking a screen recording of a website in action and turning that into a functional prototype.

![google in app quick 3](https://github.com/abi/screenshot-to-code/assets/23818/8758ffa4-9483-4b9b-bb66-abd6d1594c33)

## 🛠 Getting Started

Choose the path that fits what you want to do:

- **Run locally:** best if you want to customize, self-host, or contribute.
- **Use the hosted app:** the fastest way to try Screenshot to Code with no local setup. <a href="https://screenshottocode.com/?utm_source=github&utm_medium=readme&utm_campaign=oss_readme&utm_content=getting_started_cta" target="_blank" rel="noopener noreferrer">Open the hosted app →</a>

Running locally requires API keys and a backend/frontend setup. The app has a React/Vite frontend and a FastAPI backend.

### API keys

The recommended setup is the **Customized Provider** in the in-app Settings
dialog (click the gear icon after loading the app): enter a Base URL, an API
key, pick a provider format (OpenAI-compatible, Anthropic-compatible, xAI,
OpenRouter, or Custom), fetch the model list, and select a model. When a
custom API key and model are set, all variants run on your custom provider.

Alternatively, the same credentials can be set server-side via environment
variables (restart the backend after editing `backend/.env`):

| Key | Required? | What it unlocks |
|-----|-----------|-----------------|
| `CUSTOM_PROVIDER_API_KEY` | Yes (for custom-provider mode) | Authenticates your custom endpoint |
| `CUSTOM_PROVIDER_MODEL` | Yes (for custom-provider mode) | The model id to generate with (e.g. `gpt-4o`, `claude-opus-4-8`, `xai/grok-4`) |
| `CUSTOM_PROVIDER_BASE_URL` | Only for `custom` / self-hosted formats | Your endpoint's base URL (e.g. `https://your-host/v1`); the known formats default to their public APIs |
| `CUSTOM_PROVIDER_FORMAT` | No (defaults to `openai`) | `openai`, `anthropic`, `xai`, `openrouter`, or `custom` |
| `REPLICATE_API_KEY` | **Strongly recommended** | Image editing, background removal, and Replicate-backed image generation — without it, `edit_images` and `remove_backgrounds` are unavailable |
| `GEMINI_API_KEY` | Optional | Asset extraction (reusing the real logos/images from your screenshot); required for video mode |

Legacy `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` configuration
is still supported as a fallback when no custom provider is configured: with
those keys the app picks from its fixed model sets per variant.

If you'd like to run the app with Ollama open-source models (not recommended due to poor-quality results), configure a Customized Provider with format `custom`, Base URL `http://localhost:11434/v1`, and your Ollama model id.

Run the backend (I use Poetry for package management; run `pip install --upgrade poetry` if you don't have it):

```bash
cd backend
echo "CUSTOM_PROVIDER_API_KEY=sk-your-key" > .env
echo "CUSTOM_PROVIDER_MODEL=your-model-id" >> .env
# Optional: CUSTOM_PROVIDER_BASE_URL and CUSTOM_PROVIDER_FORMAT (default: openai)
echo "REPLICATE_API_KEY=r8_your-key" >> .env
poetry install
# Install the Chromium browser used by the screenshot preview tool.
# On Linux, use `poetry run playwright install --with-deps chromium` to also
# install the required system libraries (needs sudo/apt).
poetry run playwright install chromium
poetry env activate
# run the printed command, e.g. source /path/to/venv/bin/activate
poetry run uvicorn main:app --reload --port 7001
```

You can also set up the custom provider (Base URL, API key, format, and model) using the settings dialog in the frontend (click the gear icon after loading the app) — UI values override `backend/.env`. Replicate must be configured in `backend/.env` as `REPLICATE_API_KEY`. The Settings dialog also shows whether **screenshot preview** is available on your backend.

> **Screenshot preview** (optional) lets the agent render its own generated page in a headless browser and visually check its work. It's enabled automatically once Chromium is installed (the `playwright install chromium` step above, or automatically in the Docker image). If Chromium is missing, the app just skips the tool — the Settings dialog shows whether it's available.

Run the frontend:

```bash
cd frontend
pnpm install
pnpm dev
```

Open http://localhost:5173 to use the app.

If you prefer to run the backend on a different port, update `VITE_WS_BACKEND_URL` in `frontend/.env.local`.

## Docker

If you have Docker installed, run this from the root directory:

```bash
echo "CUSTOM_PROVIDER_API_KEY=sk-your-key" > .env
echo "CUSTOM_PROVIDER_MODEL=your-model-id" >> .env
docker-compose up -d --build
```

The app will be up and running at http://localhost:5173. Note that you can't develop the application with this setup, as file changes won't trigger a rebuild.

## 🙋‍♂️ FAQs

- **I'm running into an error when setting up the backend. How can I fix it?** [Try this](https://github.com/abi/screenshot-to-code/issues/3#issuecomment-1814777959). If that still doesn't work, open an issue.
- **How do I get an OpenAI API key?** See https://github.com/abi/screenshot-to-code/blob/main/Troubleshooting.md
- **How can I configure an OpenAI proxy or a third-party endpoint?** Use the Customized Provider in the Settings dialog (or the `CUSTOM_PROVIDER_*` variables in `backend/.env`): pick the matching provider format and set the Base URL to your proxy/gateway, e.g. `https://xxx.xxxxx.xxx/v1` for OpenAI-compatible endpoints. This works with OpenRouter, xAI, Ollama, vLLM, LiteLLM, and other OpenAI- or Anthropic-compatible services.
- **How can I update the backend host that my frontend connects to?** Configure `VITE_HTTP_BACKEND_URL` and `VITE_WS_BACKEND_URL` in `frontend/.env.local`. For example, set `VITE_HTTP_BACKEND_URL=http://124.10.20.1:7001`.
- **Seeing UTF-8 errors when running the backend?** On Windows, open the `.env` file with Notepad++, then go to Encoding and select UTF-8.
- **How can I provide feedback?** For feedback, feature requests, and bug reports, open an issue or ping me on [Twitter](https://twitter.com/_abi_).

## 📚 Examples

**NYTimes**

| Original                                                                                                                                                        | Replica                                                                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <img width="1238" alt="Screenshot 2023-11-20 at 12 54 03 PM" src="https://github.com/user-attachments/assets/6b0ae86c-1b0f-4598-a578-c7b62205b3e2"> | <img width="1435" height="737" alt="Screenshot 2026-06-15 at 3 06 37 PM" src="https://github.com/user-attachments/assets/48f0ab94-5fdc-41e7-ad6e-b4ad7ef69ae1" /> |


**Instagram**

https://github.com/user-attachments/assets/a335a105-f9cc-40e6-ac6b-64e5390bfc21

**Hacker News**


https://github.com/user-attachments/assets/205cb5c7-9c3c-438d-acd4-26dfe6e077e5
