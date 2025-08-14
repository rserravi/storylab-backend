from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.security import get_current_user, UserPublic
from app.db.database import get_session
from app.db.models import Screenplay, Project

router = APIRouter(prefix="/screenplays", tags=["Screenplays"])

WorkflowState = Literal[
    "S1","S2","S3","S4","S5","S6","S7","S8","S9","DONE","ON_HOLD","RESUME"
]

class TurningPoint(BaseModel):
    id: str
    title: str
    description: str

class Character(BaseModel):
    id: str
    name: str
    bio: Optional[str] = None
    goal: Optional[str] = None
    conflict: Optional[str] = None
    arc: Optional[str] = None

class Subplot(BaseModel):
    id: str
    logline: str
    relevance: Optional[str] = None

class Location(BaseModel):
    id: str
    name: str
    details: Optional[str] = None

class Scene(BaseModel):
    id: str
    header: str
    content: str
    order: int

class ScreenplayCreate(BaseModel):
    project_id: str
    title: str
    logline: Optional[str] = None

class ScreenplayUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    logline: Optional[str] = None
    state: Optional[WorkflowState] = None
    turning_points: Optional[list[TurningPoint]] = None
    characters: Optional[list[Character]] = None
    subplots: Optional[list[Subplot]] = None
    locations: Optional[list[Location]] = None
    scenes: Optional[list[Scene]] = None

class ScreenplayOut(BaseModel):
    id: str
    project_id: str
    owner_id: str
    title: str
    logline: Optional[str]
    state: WorkflowState
    turning_points: list[TurningPoint]
    characters: list[Character]
    subplots: list[Subplot]
    locations: list[Location]
    scenes: list[Scene]
    created_at: str
    updated_at: str

def _iso(dt): return dt.isoformat()

@router.post("", response_model=ScreenplayOut, status_code=201)
async def create_screenplay(payload: ScreenplayCreate, me: Annotated[UserPublic, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_session)]):
    # Verifica que el proyecto es del usuario
    prj = await session.get(Project, payload.project_id)
    if not prj or prj.owner_id != me.id:
        raise HTTPException(404, "Project not found or forbidden.")
    sp = Screenplay(
        project_id=payload.project_id,
        owner_id=me.id,
        title=payload.title,
        logline=payload.logline,
        state="S1",
        turning_points=[],
        characters=[],
        subplots=[],
        locations=[],
        scenes=[],
    )
    session.add(sp)
    await session.commit()
    await session.refresh(sp)
    return ScreenplayOut(
        id=sp.id, project_id=sp.project_id, owner_id=sp.owner_id, title=sp.title, logline=sp.logline,
        state=sp.state, turning_points=sp.turning_points, characters=sp.characters, subplots=sp.subplots,
        locations=sp.locations, scenes=sp.scenes, created_at=_iso(sp.created_at), updated_at=_iso(sp.updated_at)
    )

@router.get("/{screenplay_id}", response_model=ScreenplayOut)
async def get_screenplay(screenplay_id: str, me: Annotated[UserPublic, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_session)]):
    sp = await session.get(Screenplay, screenplay_id)
    if not sp or sp.owner_id != me.id:
        raise HTTPException(404, "Screenplay not found.")
    return ScreenplayOut(
        id=sp.id, project_id=sp.project_id, owner_id=sp.owner_id, title=sp.title, logline=sp.logline,
        state=sp.state, turning_points=sp.turning_points, characters=sp.characters, subplots=sp.subplots,
        locations=sp.locations, scenes=sp.scenes, created_at=_iso(sp.created_at), updated_at=_iso(sp.updated_at)
    )

@router.patch("/{screenplay_id}", response_model=ScreenplayOut)
async def update_screenplay(screenplay_id: str, payload: ScreenplayUpdate, me: Annotated[UserPublic, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_session)]):
    sp = await session.get(Screenplay, screenplay_id)
    if not sp or sp.owner_id != me.id:
        raise HTTPException(404, "Screenplay not found.")
    for field in ["title","logline","state","turning_points","characters","subplots","locations","scenes"]:
        val = getattr(payload, field)
        if val is not None:
            setattr(sp, field, val)
    await session.commit()
    await session.refresh(sp)
    return ScreenplayOut(
        id=sp.id, project_id=sp.project_id, owner_id=sp.owner_id, title=sp.title, logline=sp.logline,
        state=sp.state, turning_points=sp.turning_points, characters=sp.characters, subplots=sp.subplots,
        locations=sp.locations, scenes=sp.scenes, created_at=_iso(sp.created_at), updated_at=_iso(sp.updated_at)
    )
