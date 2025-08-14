import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.ai.router import TURNING_POINT_TITLES
from app.auth.security import UserPublic, get_current_user, hash_password
from app.db.database import get_session
from app.db.models import Base, User
from app.main import app
from app.turning_points import TURNING_POINT_TITLES


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

    responses = [
        "FAKE SYNOPSIS",
        "FAKE TREATMENT",
        json.dumps([{"id": "TP1", "description": "Desc"}]),
    ]

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
    # create screenplay
    sp_payload = {"project_id": project_id, "title": "My Script"}
    resp = await client.post("/screenplays", json=sp_payload)
    assert resp.status_code == 201
    screenplay_id = resp.json()["id"]

    # generate synopsis
    syn_payload = {
        "idea": "idea",
        "premise": "premise",
        "mainTheme": "theme",
        "genre": "genre",
        "screenplay_id": screenplay_id,
    }
    resp = await client.post("/ai/synopsis", json=syn_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["synopsis"] == "FAKE SYNOPSIS"
    assert data["iaLog"]["original_message"] == "FAKE SYNOPSIS"
    assert "time_thinking" in data["iaLog"]

    # GET screenplay to verify synopsis
    resp = await client.get(f"/screenplays/{screenplay_id}")
    assert resp.status_code == 200
    assert resp.json()["synopsis"] == "FAKE SYNOPSIS"
    assert resp.json()["treatment"] is None

    # PATCH synopsis
    resp = await client.patch(
        f"/screenplays/{screenplay_id}", json={"synopsis": "NEW SYNOPSIS"}
    )
    assert resp.status_code == 200
    assert resp.json()["synopsis"] == "NEW SYNOPSIS"

    # generate treatment
    treat_payload = {"logline": "line", "screenplay_id": screenplay_id}
    resp = await client.post("/ai/treatment", json=treat_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["treatment"] == "FAKE TREATMENT"
    assert data["iaLog"]["original_message"] == "FAKE TREATMENT"
    assert "model" in data["iaLog"]

    # GET screenplay to verify treatment
    resp = await client.get(f"/screenplays/{screenplay_id}")
    assert resp.status_code == 200
    assert resp.json()["treatment"] == "FAKE TREATMENT"

    # PATCH treatment
    resp = await client.patch(
        f"/screenplays/{screenplay_id}", json={"treatment": "NEW TREATMENT"}
    )
    assert resp.status_code == 200
    assert resp.json()["treatment"] == "NEW TREATMENT"

    # generate turning points
    tp_payload = {"screenplay_id": screenplay_id}
    resp = await client.post("/ai/turning-points", json=tp_payload)
    assert resp.status_code == 200
    data = resp.json()
    expected_title = TURNING_POINT_TITLES["TP1"]
    assert data["points"][0]["id"] == "TP1"
    assert data["points"][0]["title"] == expected_title
    assert data["points"][0]["description"] == "Desc"
    assert data["iaLog"]["original_message"] == json.dumps(
        [{"id": "TP1", "description": "Desc"}]
    )

    # verify persisted turning points
    resp = await client.get(f"/screenplays/{screenplay_id}")
    assert resp.status_code == 200
    assert resp.json()["turning_points"][0]["id"] == "TP1"
    assert resp.json()["turning_points"][0]["title"] == expected_title
    assert resp.json()["turning_points"][0]["description"] == "Desc"
