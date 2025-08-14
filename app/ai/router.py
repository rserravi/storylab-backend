import json
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.settings import settings
from app.utils.ollama_client import OllamaClient
from app.auth.security import get_current_user, UserPublic
from app.db.database import get_session
from app.db.models import Project
from .prompts import (
    SYNOPSIS_PROMPT, TREATMENT_PROMPT, TURNING_POINTS_PROMPT, CHARACTER_PROMPT,
    LOCATION_PROMPT, SCENE_PROMPT, DIALOGUE_POLISH_PROMPT, REVIEW_PROMPT
)

router = APIRouter(prefix="/ai", tags=["AI"])

# ---------- Helpers modelo ----------
def pick_text_model(screenwriter: bool = False):
    return settings.ai_text_screenwriter if screenwriter else settings.ai_text_default

def pick_scene_model(creative: bool = False):
    return settings.ai_text_scene_creative if creative else settings.ai_text_scene_default


async def save_synopsis(project_id: str, synopsis: str) -> None:
    """Persist the synopsis for the given project.

    Placeholder for future persistence logic.
    """

    return None

# ---------- Schemas ----------
class SynopsisIn(BaseModel):
    idea: str
    premise: str
    mainTheme: str
    genre: str
    subgenres: Optional[list[str]] = None
    project_id: str
    screenwriter: bool = False

class SynopsisOut(BaseModel):
    synopsis: str

@router.post("/synopsis", response_model=SynopsisOut)
async def generate_synopsis(
    payload: SynopsisIn,
    me: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    model = pick_text_model(payload.screenwriter)
    subgenres = ", ".join(payload.subgenres or [])
    prompt = SYNOPSIS_PROMPT.format(
        idea=payload.idea,
        premise=payload.premise,
        theme=payload.mainTheme,
        genre=payload.genre,
        subgenres=subgenres,
    )
    async with OllamaClient() as client:
        text = await client.generate(model=model, prompt=prompt)
    project = await session.get(Project, payload.project_id)
    if not project:
        raise HTTPException(404, "Project not found.")
    project.synopsis = text.strip()
    await session.commit()
    return {"synopsis": project.synopsis}


# ---------- Treatment ----------
class TreatmentIn(BaseModel):
    logline: str
    tone: Optional[str] = "cinematográfico"
    audience: Optional[str] = "adulto general"
    references: Optional[str] = None
    project_id: str
    screenwriter: bool = True

class TreatmentOut(BaseModel):
    treatment: str

@router.post("/treatment", response_model=TreatmentOut)
async def generate_treatment(payload: TreatmentIn, me: Annotated[UserPublic, Depends(get_current_user)]):
    model = pick_text_model(payload.screenwriter)
    prompt = TREATMENT_PROMPT.format(
        tone=payload.tone, audience=payload.audience, references=payload.references or "", logline=payload.logline
    )
    async with OllamaClient() as client:
        text = await client.generate(model=model, prompt=prompt)
    return {"treatment": text.strip()}

# ---------- Turning Points ----------
class TurningPointItem(BaseModel):
    id: str
    title: str
    description: str

class TurningPointsIn(BaseModel):
    genre: str
    theme: str
    premise: str
    project_id: str

class TurningPointsOut(BaseModel):
    points: list[TurningPointItem]

@router.post("/turning-points", response_model=TurningPointsOut)
async def generate_turning_points(payload: TurningPointsIn, me: Annotated[UserPublic, Depends(get_current_user)]):
    model = pick_text_model(True)
    prompt = TURNING_POINTS_PROMPT.format(genre=payload.genre, theme=payload.theme, premise=payload.premise)
    async with OllamaClient() as client:
        text = await client.generate(model=model, prompt=prompt)
    try:
        data = json.loads(text)
        items = [TurningPointItem(**tp) for tp in data]
    except Exception:
        raise HTTPException(502, "AI returned invalid JSON for turning points.")
    return {"points": items}

# ---------- Character ----------
class CharacterOut(BaseModel):
    id: str
    name: str
    bio: Optional[str] = None
    goal: Optional[str] = None
    conflict: Optional[str] = None
    arc: Optional[str] = None

class CharacterIn(BaseModel):
    seed_name: str
    role: str
    goal: Optional[str] = None
    conflict: Optional[str] = None
    project_id: str
    creative: bool = False

@router.post("/character", response_model=CharacterOut)
async def generate_character(payload: CharacterIn, me: Annotated[UserPublic, Depends(get_current_user)]):
    model = pick_scene_model(payload.creative)
    prompt = CHARACTER_PROMPT.format(
        seed_name=payload.seed_name, role=payload.role, goal=payload.goal or "", conflict=payload.conflict or ""
    )
    async with OllamaClient() as client:
        text = await client.generate(model=model, prompt=prompt)
    try:
        return CharacterOut(**json.loads(text))
    except Exception:
        raise HTTPException(502, "AI returned invalid JSON for character.")

# ---------- Location ----------
class LocationOut(BaseModel):
    id: str
    name: str
    details: Optional[str] = None

class LocationIn(BaseModel):
    seed_name: str
    genre: str
    notes: Optional[str] = None
    project_id: str
    creative: bool = False

@router.post("/location", response_model=LocationOut)
async def generate_location(payload: LocationIn, me: Annotated[UserPublic, Depends(get_current_user)]):
    model = pick_scene_model(payload.creative)
    prompt = LOCATION_PROMPT.format(seed_name=payload.seed_name, genre=payload.genre, notes=payload.notes or "")
    async with OllamaClient() as client:
        text = await client.generate(model=model, prompt=prompt)
    try:
        return LocationOut(**json.loads(text))
    except Exception:
        raise HTTPException(502, "AI returned invalid JSON for location.")

# ---------- Scene ----------
class SceneIn(BaseModel):
    header: str   # "INT. CASA DE LUIS - NOCHE"
    context: str
    goal: str
    style: Optional[str] = "Hollywood estándar"
    project_id: str
    creative: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class SceneOut(BaseModel):
    content: str

@router.post("/scene", response_model=SceneOut)
async def generate_scene(payload: SceneIn, me: Annotated[UserPublic, Depends(get_current_user)]):
    model = pick_scene_model(payload.creative)
    prompt = SCENE_PROMPT.format(
        header=payload.header, context=payload.context, goal=payload.goal,
        style=payload.style or "Hollywood estándar",
        creative_level="alto" if payload.creative else "moderado"
    )
    async with OllamaClient() as client:
        text = await client.generate(
            model=model, prompt=prompt,
            temperature=payload.temperature, max_tokens=payload.max_tokens
        )
    return {"content": text.strip()}

# ---------- Dialogue Polish ----------
class DialogueIn(BaseModel):
    raw: str
    project_id: str
    creative: bool = False

class DialogueOut(BaseModel):
    content: str

@router.post("/dialogue/polish", response_model=DialogueOut)
async def polish_dialogue(payload: DialogueIn, me: Annotated[UserPublic, Depends(get_current_user)]):
    model = pick_scene_model(payload.creative)
    prompt = DIALOGUE_POLISH_PROMPT.format(raw=payload.raw)
    async with OllamaClient() as client:
        text = await client.generate(model=model, prompt=prompt)
    return {"content": text.strip()}

# ---------- Review ----------
class ReviewIn(BaseModel):
    text: str
    project_id: str
    screenwriter: bool = True

class ReviewOut(BaseModel):
    report: str

@router.post("/review", response_model=ReviewOut)
async def review_script(payload: ReviewIn, me: Annotated[UserPublic, Depends(get_current_user)]):
    model = pick_text_model(payload.screenwriter)
    prompt = REVIEW_PROMPT.format(text=payload.text)
    async with OllamaClient() as client:
        text = await client.generate(model=model, prompt=prompt)
    return {"report": text.strip()}
