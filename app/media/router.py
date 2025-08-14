from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.settings import settings

router = APIRouter(prefix="/media", tags=["AI", "Media"])

class ImageIn(BaseModel):
    prompt: str
    style: str  # "fast" | "quality"
    screenplay_id: str

class ImageOut(BaseModel):
    url: str

@router.post("/image", response_model=ImageOut)
async def generate_image(payload: ImageIn):
    model = settings.ai_image_fast if payload.style == "fast" else settings.ai_image_quality
    # Aquí delegamos a ComfyUI (o servicio que decidas) con un workflow predefinido para SDXL/SDXL Turbo
    # Por ahora devolvemos un stub 501 si no está configurado
    if not settings.images_base_url:
        raise HTTPException(501, "Image service not configured.")
    # TODO: llamar al workflow y devolver URL final del asset
    raise HTTPException(501, f"Image generation not yet wired (model={model}).")
