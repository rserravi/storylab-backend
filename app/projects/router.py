from datetime import datetime, timezone
from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.security import get_current_user, UserPublic
from app.db.database import get_session
from app.db.models import Project

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    description: Optional[str] = None
    treatment: Optional[str] = None



class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=128)
    description: Optional[str] = None
    treatment: Optional[str] = None



class ProjectOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    treatment: Optional[str]
    owner_id: str
    created_at: str
    updated_at: str

class TreatmentPatch(BaseModel):
    treatment: str


class TreatmentOut(BaseModel):
    treatment: str
class SynopsisPatch(BaseModel):
    synopsis: Optional[str] = None


class SynopsisOut(BaseModel):
    synopsis: Optional[str]

def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_owner(p: Project, user_id: str):
    if not p:
        raise HTTPException(404, "Project not found.")
    if p.owner_id != user_id:
        raise HTTPException(403, "Forbidden.")


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    me: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    q: Optional[str] = Query(default=None),
):
    stmt = select(Project).where(Project.owner_id == me.id)
    if q:
        stmt = stmt.where(Project.name.ilike(f"%{q}%"))
    rows = (await session.execute(stmt)).scalars().all()
    return [
        ProjectOut(
            id=r.id,
            name=r.name,
            description=r.description,
            treatment=r.treatment,
            owner_id=r.owner_id,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
        )
        for r in rows
    ]


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    payload: ProjectCreate,
    me: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    p = Project(
        name=payload.name,
        description=payload.description,
        treatment=payload.treatment,
        owner_id=me.id,
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return ProjectOut(
        id=p.id,
        name=p.name,
        description=p.description,
        owner_id=p.owner_id,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    me: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    p = await session.get(Project, project_id)
    _ensure_owner(p, me.id)
    return ProjectOut(
        id=p.id,
        name=p.name,
        description=p.description,
        treatment=p.treatment,
        owner_id=p.owner_id,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    me: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    p = await session.get(Project, project_id)
    _ensure_owner(p, me.id)
    if payload.name is not None:
        p.name = payload.name
    if payload.description is not None:
        p.description = payload.description
    if payload.treatment is not None:
        p.treatment = payload.treatment
    await session.commit()
    await session.refresh(p)
    return ProjectOut(
        id=p.id,
        name=p.name,
        description=p.description,
        owner_id=p.owner_id,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    me: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    p = await session.get(Project, project_id)
    _ensure_owner(p, me.id)
    await session.delete(p)
    await session.commit()


@router.get("/{project_id}/treatment", response_model=TreatmentOut)
async def get_treatment(
@router.get("/{project_id}/synopsis", response_model=SynopsisOut)
async def get_synopsis(
    project_id: str,
    me: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    p = await session.get(Project, project_id)
    _ensure_owner(p, me.id)
    if not p.treatment:
        raise HTTPException(404, "Treatment not found.")
    return {"treatment": p.treatment}


@router.patch("/{project_id}/treatment", response_model=TreatmentOut)
async def patch_treatment(
    project_id: str,
    payload: TreatmentPatch,
    return {"synopsis": p.synopsis}


@router.patch("/{project_id}/synopsis", response_model=SynopsisOut)
async def patch_synopsis(
    project_id: str,
    payload: SynopsisPatch,
    me: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    p = await session.get(Project, project_id)
    _ensure_owner(p, me.id)
    p.treatment = payload.treatment
    await session.commit()
    return {"treatment": p.treatment}
    if "synopsis" in payload.model_fields_set:
        p.synopsis = payload.synopsis
        await session.commit()
        await session.refresh(p)
    return {"synopsis": p.synopsis}
