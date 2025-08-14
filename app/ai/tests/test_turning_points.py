import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.db.models import Base, User, Project, Screenplay
from app.db.database import get_session
from app.auth.security import get_current_user, UserPublic, hash_password


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def client(session):
    user = User(email="tester@example.com", password_hash=hash_password("pw"))
    session.add(user)
    await session.commit()
    await session.refresh(user)

    async def override_get_session():
        yield session

    async def override_get_current_user():
        return UserPublic(id=user.id, email=user.email, full_name=None)

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(app=app, base_url="http://test") as ac:
        ac.user = user
        yield ac

    app.dependency_overrides.clear()


async def create_project_and_screenplay(session, user):
    project = Project(
        name="Proj", owner_id=user.id, synopsis="syn", treatment="treat"
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)

    screenplay = Screenplay(
        project_id=project.id,
        owner_id=user.id,
        title="Script",
        logline=None,
        state="S1",
        turning_points=[],
        characters=[],
        subplots=[],
        locations=[],
        scenes=[],
    )
    session.add(screenplay)
    await session.commit()
    await session.refresh(screenplay)
    return project, screenplay


@pytest.mark.asyncio
async def test_turning_points_valid_json(client, session, monkeypatch):
    project, screenplay = await create_project_and_screenplay(session, client.user)
    turning_points = [
        {"id": "TP1", "title": "Title", "description": "Desc"}
    ]

    async def fake_generate(self, model, prompt, **kwargs):
        return json.dumps(turning_points)

    monkeypatch.setattr(
        "app.utils.ollama_client.OllamaClient.generate", fake_generate
    )

    resp = await client.post(
        "/ai/turning-points",
        json={"project_id": project.id, "screenplay_id": screenplay.id},
    )
    assert resp.status_code == 200
    assert resp.json()["points"] == turning_points

    await session.refresh(screenplay)
    assert screenplay.turning_points == turning_points


@pytest.mark.asyncio
async def test_turning_points_invalid_json(client, session, monkeypatch):
    project, screenplay = await create_project_and_screenplay(session, client.user)

    async def fake_generate(self, model, prompt, **kwargs):
        return "invalid"

    monkeypatch.setattr(
        "app.utils.ollama_client.OllamaClient.generate", fake_generate
    )

    resp = await client.post(
        "/ai/turning-points",
        json={"project_id": project.id, "screenplay_id": screenplay.id},
    )
    assert resp.status_code == 502
    assert (
        resp.json()["detail"]
        == "AI returned invalid JSON for turning points."
    )

    await session.refresh(screenplay)
    assert screenplay.turning_points == []
