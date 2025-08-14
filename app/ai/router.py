import json
from time import perf_counter
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import UserPublic, get_current_user
from app.db.database import get_session
from app.db.models import Project, Screenplay
from app.settings import settings
from app.turning_points import TURNING_POINT_TITLES
from app.utils.ollama_client import OllamaClient

from .prompts import (
    CHARACTER_PROMPT,
    DIALOGUE_POLISH_PROMPT,
    LOCATION_PROMPT,
    REVIEW_PROMPT,
    SCENE_PROMPT,
    SYNOPSIS_PROMPT,
    TREATMENT_PROMPT,
    TURNING_POINTS_PROMPT,
)

router = APIRouter(prefix="/ai", tags=["AI"])


# Fixed titles for Turning Points keyed by their identifiers
TURNING_POINT_TITLES = {
    "TP1": "Inciting Incident",
    "TP2": "Break into Act Two",
    "TP3": "Midpoint",
    "TP4": "Break into Act Three",
    "TP5": "Climax",
}

# ---------- IA Log ----------


class IALog(BaseModel):
    time_thinking: float
    original_message: str
    model: str


async def run_ai(model: str, prompt: str, **kwargs) -> tuple[str, IALog]:
    start = perf_counter()
    async with OllamaClient() as client:
        text = await client.generate(model=model, prompt=prompt, **kwargs)
    duration = perf_counter() - start
    ia_log = IALog(time_thinking=duration, original_message=text, model=model)
    return text, ia_log


# ---------- Helpers modelo ----------
def pick_text_model(screenwriter: bool = False):
    return settings.ai_text_screenwriter if screenwriter else settings.ai_text_default


def pick_scene_model(creative: bool = False):
    return (
        settings.ai_text_scene_creative if creative else settings.ai_text_scene_default
    )


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
    iaLog: IALog


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
    text, ia_log = await run_ai(model=model, prompt=prompt)
    project = await session.get(Project, payload.project_id)
    if not project:
        raise HTTPException(404, "Project not found.")
    project.synopsis = text.strip()
    await session.commit()
    return {"synopsis": project.synopsis, "iaLog": ia_log}


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
    iaLog: IALog


@router.post("/treatment", response_model=TreatmentOut)
async def generate_treatment(
    payload: TreatmentIn,
    me: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    model = pick_text_model(payload.screenwriter)
    project = await session.get(Project, payload.project_id)
    if not project or not project.synopsis:
        raise HTTPException(404, "Project not found or missing synopsis.")
    prompt = TREATMENT_PROMPT.format(
        tone=payload.tone,
        audience=payload.audience,
        references=payload.references or "",
        logline=payload.logline,
        synopsis=project.synopsis,
    )
    text, ia_log = await run_ai(model=model, prompt=prompt)
    project.treatment = text.strip()
    await session.commit()
    return {"treatment": project.treatment, "iaLog": ia_log}


# ---------- Turning Points ----------
class TurningPointItem(BaseModel):
    id: str
    description: str
    title: str


class TurningPointsIn(BaseModel):
    project_id: str
    screenplay_id: str
    screenwriter: bool = True


class TurningPointsOut(BaseModel):
    points: list[TurningPointItem]
    iaLog: IALog


@router.post("/turning-points", response_model=TurningPointsOut)
async def generate_turning_points(
    payload: TurningPointsIn,
    me: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    model = pick_text_model(payload.screenwriter)
    project = await session.get(Project, payload.project_id)
    if not project or not project.treatment:
        raise HTTPException(404, "Project not found or missing treatment.")
    screenplay = await session.get(Screenplay, payload.screenplay_id)
    if not screenplay or screenplay.owner_id != me.id:
        raise HTTPException(404, "Screenplay not found.")
    prompt = TURNING_POINTS_PROMPT.format(treatment=project.treatment)
    text, ia_log = await run_ai(model=model, prompt=prompt)
    try:
        data = json.loads(text)
        items = [
            TurningPointItem(
                id=tp["id"],
                title=TURNING_POINT_TITLES.get(tp["id"], tp.get("title", "")),
                description=tp["description"],
            )
            for tp in data
        ]

    except Exception:
        raise HTTPException(
            502,
            detail={
                "error": "AI returned invalid JSON for turning points.",
                "iaLog": ia_log.model_dump(),
            },
        )
    screenplay.turning_points = [tp.model_dump() for tp in items]
    await session.commit()
    await session.refresh(screenplay)
    return {"points": items, "iaLog": ia_log}


# ---------- Character ----------
class CharacterOut(BaseModel):
    id: str
    name: str
    bio: Optional[str] = None
    goal: Optional[str] = None
    conflict: Optional[str] = None
    arc: Optional[str] = None
    iaLog: IALog


class CharacterIn(BaseModel):
    seed_name: str
    role: str
    goal: Optional[str] = None
    conflict: Optional[str] = None
    project_id: str
    creative: bool = False


@router.post("/character", response_model=CharacterOut)
async def generate_character(
    payload: CharacterIn, me: Annotated[UserPublic, Depends(get_current_user)]
):
    model = pick_scene_model(payload.creative)
    prompt = CHARACTER_PROMPT.format(
        seed_name=payload.seed_name,
        role=payload.role,
        goal=payload.goal or "",
        conflict=payload.conflict or "",
    )
    text, ia_log = await run_ai(model=model, prompt=prompt)
    try:
        data = json.loads(text)
        return CharacterOut(**data, iaLog=ia_log)
    except Exception:
        raise HTTPException(
            502,
            detail={
                "error": "AI returned invalid JSON for character.",
                "iaLog": ia_log.model_dump(),
            },
        )


# ---------- Location ----------
class LocationOut(BaseModel):
    id: str
    name: str
    details: Optional[str] = None
    iaLog: IALog


class LocationIn(BaseModel):
    seed_name: str
    genre: str
    notes: Optional[str] = None
    project_id: str
    creative: bool = False


@router.post("/location", response_model=LocationOut)
async def generate_location(
    payload: LocationIn, me: Annotated[UserPublic, Depends(get_current_user)]
):
    model = pick_scene_model(payload.creative)
    prompt = LOCATION_PROMPT.format(
        seed_name=payload.seed_name, genre=payload.genre, notes=payload.notes or ""
    )
    text, ia_log = await run_ai(model=model, prompt=prompt)
    try:
        data = json.loads(text)
        return LocationOut(**data, iaLog=ia_log)
    except Exception:
        raise HTTPException(
            502,
            detail={
                "error": "AI returned invalid JSON for location.",
                "iaLog": ia_log.model_dump(),
            },
        )


# ---------- Scene ----------
class SceneIn(BaseModel):
    header: str  # "INT. CASA DE LUIS - NOCHE"
    context: str
    goal: str
    style: Optional[str] = "Hollywood estándar"
    project_id: str
    creative: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class SceneOut(BaseModel):
    content: str
    iaLog: IALog


@router.post("/scene", response_model=SceneOut)
async def generate_scene(
    payload: SceneIn, me: Annotated[UserPublic, Depends(get_current_user)]
):
    model = pick_scene_model(payload.creative)
    prompt = SCENE_PROMPT.format(
        header=payload.header,
        context=payload.context,
        goal=payload.goal,
        style=payload.style or "Hollywood estándar",
        creative_level="alto" if payload.creative else "moderado",
    )
    text, ia_log = await run_ai(
        model=model,
        prompt=prompt,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )
    return {"content": text.strip(), "iaLog": ia_log}


# ---------- Dialogue Polish ----------
class DialogueIn(BaseModel):
    raw: str
    project_id: str
    creative: bool = False


class DialogueOut(BaseModel):
    content: str
    iaLog: IALog


@router.post("/dialogue/polish", response_model=DialogueOut)
async def polish_dialogue(
    payload: DialogueIn, me: Annotated[UserPublic, Depends(get_current_user)]
):
    model = pick_scene_model(payload.creative)
    prompt = DIALOGUE_POLISH_PROMPT.format(raw=payload.raw)
    text, ia_log = await run_ai(model=model, prompt=prompt)
    return {"content": text.strip(), "iaLog": ia_log}


# ---------- Review ----------
class ReviewIn(BaseModel):
    text: str
    project_id: str
    screenwriter: bool = True


class ReviewOut(BaseModel):
    report: str
    iaLog: IALog


@router.post("/review", response_model=ReviewOut)
async def review_script(
    payload: ReviewIn, me: Annotated[UserPublic, Depends(get_current_user)]
):
    model = pick_text_model(payload.screenwriter)
    prompt = REVIEW_PROMPT.format(text=payload.text)
    text, ia_log = await run_ai(model=model, prompt=prompt)
    return {"report": text.strip(), "iaLog": ia_log}
