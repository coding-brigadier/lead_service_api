import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.internal import router as internal_router
from app.api.public import router as public_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger(__name__).info("Starting up Alma lead management API")
    yield
    logging.getLogger(__name__).info("Shutting down")


app = FastAPI(title="Alma Lead Management", lifespan=lifespan)

app.include_router(public_router, tags=["public"])
app.include_router(internal_router, tags=["internal"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
