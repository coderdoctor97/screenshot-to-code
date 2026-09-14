# pyright: reportUnknownVariableType=false
"""Custom provider discovery endpoints (Settings UI "Customized Provider").

The frontend configures a custom Base URL / API key / provider format and
calls these endpoints to list the provider formats and to fetch the models
available on the configured endpoint. Proxying through the backend avoids
browser CORS issues with arbitrary third-party endpoints and keeps the API
key out of cross-origin browser traffic.
"""

from typing import Any

import httpx
from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from llm import (
    CUSTOM_PROVIDER_DEFAULT_BASE_URLS,
    CUSTOM_PROVIDER_FORMAT_LABELS,
    CUSTOM_PROVIDER_FORMATS,
    CustomProviderConfig,
    custom_provider_wire_format,
    normalize_custom_provider_format,
)

router = APIRouter()

_MODELS_FETCH_TIMEOUT_SECONDS = 15.0
_ANTHROPIC_VERSION = "2023-06-01"


class CustomProviderFormatInfo(BaseModel):
    value: str
    label: str
    default_base_url: str
    wire_format: str


class CustomProviderModelsRequest(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    provider_format: str | None = None


class CustomProviderModelInfo(BaseModel):
    id: str
    name: str | None = None


class CustomProviderModelsResponse(BaseModel):
    models: list[CustomProviderModelInfo]
    wire_format: str


@router.get("/api/custom-provider/formats", response_model=list[CustomProviderFormatInfo])
async def list_custom_provider_formats() -> list[CustomProviderFormatInfo]:
    """Provider formats the UI can offer in the Customized Provider dropdown."""
    return [
        CustomProviderFormatInfo(
            value=format_name,
            label=CUSTOM_PROVIDER_FORMAT_LABELS[format_name],
            default_base_url=CUSTOM_PROVIDER_DEFAULT_BASE_URLS[format_name],
            wire_format=custom_provider_wire_format(format_name),
        )
        for format_name in CUSTOM_PROVIDER_FORMATS
    ]


def _openai_models_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/models"


def _anthropic_models_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if not base.endswith("/v1"):
        base = f"{base}/v1"
    return f"{base}/models?limit=100"


def _extract_model_ids(payload: Any) -> list[CustomProviderModelInfo]:
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=502, detail="Unexpected response from the provider."
        )
    data: Any = payload.get("data")
    if not isinstance(data, list):
        raise HTTPException(
            status_code=502, detail="Unexpected response from the provider."
        )
    models: list[CustomProviderModelInfo] = []
    seen: set[str] = set()
    entries: list[Any] = data
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        model_id: Any = entry.get("id")
        if not isinstance(model_id, str) or not model_id.strip() or model_id in seen:
            continue
        seen.add(model_id)
        display_name: Any = entry.get("display_name") or entry.get("name")
        models.append(
            CustomProviderModelInfo(
                id=model_id,
                name=display_name if isinstance(display_name, str) else None,
            )
        )
    models.sort(key=lambda model: model.id.lower())
    return models


def _provider_error_detail(response: httpx.Response) -> str:
    try:
        payload: Any = response.json()
    except ValueError:
        payload = None
    message: str | None = None
    if isinstance(payload, dict):
        error: Any = payload.get("error")
        if isinstance(error, dict):
            error_message: Any = error.get("message")
            if isinstance(error_message, str):
                message = error_message
        elif isinstance(error, str):
            message = error
        if message is None:
            fallback: Any = payload.get("message")
            if isinstance(fallback, str):
                message = fallback
    if not message:
        message = f"Provider returned HTTP {response.status_code}."
    # Truncate defensively; provider messages must never leak credentials and
    # stay readable in the Settings UI.
    message = message.strip()
    if len(message) > 300:
        message = message[:297] + "..."
    return message


async def _fetch_openai_compatible_models(
    base_url: str, api_key: str | None
) -> list[CustomProviderModelInfo]:
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    async with httpx.AsyncClient(timeout=_MODELS_FETCH_TIMEOUT_SECONDS) as client:
        response = await client.get(_openai_models_url(base_url), headers=headers)
    if response.status_code != 200:
        raise HTTPException(
            status_code=400, detail=_provider_error_detail(response)
        )
    return _extract_model_ids(response.json())


async def _fetch_anthropic_compatible_models(
    base_url: str, api_key: str | None
) -> list[CustomProviderModelInfo]:
    headers = {"anthropic-version": _ANTHROPIC_VERSION}
    if api_key:
        headers["x-api-key"] = api_key
    async with httpx.AsyncClient(timeout=_MODELS_FETCH_TIMEOUT_SECONDS) as client:
        response = await client.get(_anthropic_models_url(base_url), headers=headers)
    if response.status_code != 200:
        raise HTTPException(
            status_code=400, detail=_provider_error_detail(response)
        )
    return _extract_model_ids(response.json())


@router.post("/api/custom-provider/models", response_model=CustomProviderModelsResponse)
async def list_custom_provider_models(
    body: CustomProviderModelsRequest,
) -> CustomProviderModelsResponse:
    """Fetch the model ids available on a custom provider endpoint."""
    provider_format = normalize_custom_provider_format(body.provider_format)
    config = CustomProviderConfig.from_values(
        base_url=body.base_url,
        api_key=body.api_key,
        provider_format=provider_format,
        model="probe",
    )
    base_url = config.effective_base_url
    if not base_url:
        raise HTTPException(
            status_code=400,
            detail=(
                "A Base URL is required for this provider format. "
                "Enter one (for example https://your-host/v1) and try again."
            ),
        )

    try:
        if config.wire_format == "anthropic":
            models = await _fetch_anthropic_compatible_models(base_url, config.api_key)
        else:
            models = await _fetch_openai_compatible_models(base_url, config.api_key)
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"Timed out reaching {base_url}. Check the Base URL and try again.",
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not reach {base_url}: {exc.__class__.__name__}.",
        )

    return CustomProviderModelsResponse(models=models, wire_format=config.wire_format)
