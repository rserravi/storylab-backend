from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://storylab:storylab@localhost:5433/storylab")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False, autocommit=False)

async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
