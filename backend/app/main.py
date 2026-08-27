import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.assessments import router
from app.config import get_settings
from app.services.jobs import JobStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.jobs = JobStore(settings)
    yield
    app.state.jobs.close()


app = FastAPI(title="Veda Assessment API", version="1.0.0", lifespan=lifespan)
settings = get_settings()
app.add_middleware(
    CORSMiddleware, allow_origins=settings.origins, allow_credentials=False,
    allow_methods=["GET", "POST"], allow_headers=["Content-Type"],
)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}

