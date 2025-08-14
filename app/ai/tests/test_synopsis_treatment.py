import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.db.models import Base, User
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
async def client(session, monkeypatch):
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

    responses = ["FAKE SYNOPSIS", "FAKE TREATMENT"]

    async def fake_generate(self, model, prompt, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr("app.utils.ollama_client.OllamaClient.generate", fake_generate)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_generate_get_patch_synopsis_treatment(client):
    # create project
    resp = await client.post("/projects", json={"name": "My Project"})
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    # generate synopsis
    syn_payload = {
        "idea": "idea",
        "premise": "premise",
        "mainTheme": "theme",
        "genre": "genre",
        "project_id": project_id,
    }
    resp = await client.post("/ai/synopsis", json=syn_payload)
    assert resp.status_code == 200
    assert resp.json()["synopsis"] == "FAKE SYNOPSIS"

    # GET project to verify synopsis
    resp = await client.get(f"/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["synopsis"] == "FAKE SYNOPSIS"
    assert resp.json()["treatment"] is None

    # PATCH synopsis
    resp = await client.patch(
        f"/projects/{project_id}", json={"synopsis": "NEW SYNOPSIS"}
    )
    assert resp.status_code == 200
    assert resp.json()["synopsis"] == "NEW SYNOPSIS"

    # generate treatment
    treat_payload = {"logline": "line", "project_id": project_id}
    resp = await client.post("/ai/treatment", json=treat_payload)
    assert resp.status_code == 200
    assert resp.json()["treatment"] == "FAKE TREATMENT"

    # GET project to verify treatment
    resp = await client.get(f"/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["treatment"] == "FAKE TREATMENT"

    # PATCH treatment
    resp = await client.patch(
        f"/projects/{project_id}", json={"treatment": "NEW TREATMENT"}
    )
    assert resp.status_code == 200
    assert resp.json()["treatment"] == "NEW TREATMENT"
