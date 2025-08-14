import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))


def test_treatment_persists():
    pytest.importorskip("sqlalchemy")
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from app.db.models import Base, Project, gen_uuid
    import asyncio

    async def run() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with async_session() as session:
            project = Project(id=gen_uuid(), name="Test Project")
            session.add(project)
            await session.commit()
            project.treatment = "Sample treatment"
            await session.commit()
            refreshed = await session.get(Project, project.id)
            assert refreshed.treatment == "Sample treatment"

    asyncio.run(run())


def test_dummy():
    assert True

