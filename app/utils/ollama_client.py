# utils/ollama_client.py
from __future__ import annotations

import asyncio
import json
from typing import Optional

import httpx

from app.settings import settings


DEFAULT_TIMEOUT = getattr(settings, "ai_timeout_seconds", 120)
DEFAULT_TEMP = getattr(settings, "ai_temperature", 0.7)
DEFAULT_MAX_TOKENS = getattr(settings, "ai_max_tokens", 512)


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = base_url or settings.ollama_base_url
        self.timeout = timeout or DEFAULT_TIMEOUT
        # Un único AsyncClient reutilizable
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def __aenter__(self) -> "OllamaClient":
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self) -> None:
        if not self._client.is_closed:
            await self._client.aclose()

    def _build_payload(
        self,
        model: str,
        prompt: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        stream: bool,
    ) -> dict:
        return {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": float(temperature if temperature is not None else DEFAULT_TEMP),
                "num_predict": int(max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS),
            },
        }

    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        timeout: Optional[float] = None,
        retries: int = 2,
        retry_backoff: float = 1.5,
    ) -> str:
        """
        Llama a /api/generate de Ollama y devuelve el texto completo.
        - stream=False (por defecto): una única respuesta JSON.
        - stream=True: consume los fragmentos 'response' hasta 'done': true.
        """
        payload = self._build_payload(model, prompt, temperature, max_tokens, stream=stream)
        last_exc: Optional[Exception] = None
        per_request_timeout = timeout or self.timeout

        for attempt in range(retries + 1):
            try:
                if not stream:
                    r = await self._client.post("/api/generate", json=payload, timeout=per_request_timeout)
                    r.raise_for_status()
                    data = r.json()
                    return data.get("response", "")
                else:
                    # Streaming NDJSON: cada línea es un objeto con { "response": "...", "done": bool }
                    text_parts: list[str] = []
                    async with self._client.stream(
                        "POST", "/api/generate", json=payload, timeout=per_request_timeout
                    ) as r:
                        r.raise_for_status()
                        async for line in r.aiter_lines():
                            if not line:
                                continue
                            try:
                                obj = json.loads(line)
                            except json.JSONDecodeError:
                                # Algunas veces llega basura / keep-alives vacíos
                                continue
                            chunk = obj.get("response")
                            if chunk:
                                text_parts.append(chunk)
                            if obj.get("done"):
                                break
                    return "".join(text_parts)
            except (httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                last_exc = e
                if attempt >= retries:
                    break
                # pequeño backoff para modelos pesados (e.g., qwen2.5:32b)
                await asyncio.sleep(retry_backoff * (attempt + 1))
            except httpx.HTTPStatusError as e:
                # Errores 4xx/5xx: no solemos reintentar salvo 5xx
                if 500 <= e.response.status_code < 600 and attempt < retries:
                    last_exc = e
                    await asyncio.sleep(retry_backoff * (attempt + 1))
                    continue
                # Propagamos el detalle
                try:
                    detail = e.response.json()
                except Exception:
                    detail = e.response.text
                raise OllamaError(f"Ollama devolvió {e.response.status_code}: {detail}") from e
            except Exception as e:
                last_exc = e
                break

        # Si llegamos aquí, agotamos reintentos
        raise OllamaError(f"Fallo al generar con Ollama tras reintentos: {last_exc!r}")

    async def list_models(self) -> dict:
        r = await self._client.get("/api/tags")
        r.raise_for_status()
        return r.json()
