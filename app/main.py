from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.ai.router import router as ai_router
from app.media.router import router as media_router
from app.auth.router import router as auth_router
from app.projects.router import router as projects_router
from app.screenplays.router import router as screenplays_router

app = FastAPI(title="StoryLab API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(screenplays_router)
app.include_router(ai_router)
app.include_router(media_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
