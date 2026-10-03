import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.classifier import Classification, ClassifierError, classify, warm_up
from app.config import settings

log = logging.getLogger("dublinfix")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await warm_up()
    except httpx.HTTPError as exc:
        log.warning("Could not warm up Ollaya model %s: %r", settings.ollaya_model, exc)
    yield


app = FastAPI(title="Dublin Fix API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=3, max_length=2000)


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(base_url=settings.ollaya_url, timeout=3) as client:
            tags = (await client.get("/api/tags")).json()
    except httpx.HTTPError:
        return {"status": "degraded", "ollaya": "unreachable", "model": settings.ollaya_model}
    installed = {m["name"].removesuffix(":latest") for m in tags.get("models", [])}
    return {
        "status": "ok",
        "ollaya": "reachable",
        "model": settings.ollaya_model,
        "modelInstalled": settings.ollaya_model.removesuffix(":latest") in installed,
    }


@app.post("/classify", response_model=Classification)
async def classify_report(body: ClassifyRequest):
    try:
        return await classify(body.text)
    except ClassifierError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
