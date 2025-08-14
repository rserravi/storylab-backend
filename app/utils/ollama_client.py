import httpx
from app.settings import settings

class OllamaClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.ollama_base_url
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=60)

    async def generate(self, model: str, prompt: str, temperature: float | None = None, max_tokens: int | None = None):
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature or settings.ai_temperature,
                "num_predict": max_tokens or settings.ai_max_tokens
            }
        }
        r = await self._client.post("/api/generate", json=payload)
        r.raise_for_status()
        # Streaming simple: devolvemos todo el texto concatenado
        txt = ""
        for line in r.iter_text():
            if not line:
                continue
            try:
                obj = httpx.Response.json  # placeholder: httpx no expone método estático
            except Exception:
                pass
        # Para simplificar: usamos /api/generate no-stream
        r = await self._client.post("/api/generate", json={**payload, "stream": False})
        r.raise_for_status()
        data = r.json()
        return data.get("response", "")

    async def list_models(self) -> dict:
        r = await self._client.get("/api/tags")
        r.raise_for_status()
        return r.json()
