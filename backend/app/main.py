import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress

import httpx
import pymongo
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from app.classifier import Classification, ClassifierError, classify, warm_up
from app.config import settings
from app.db import client, ensure_indexes
from app.events import router as events_router
from app.events import watch_reports
from app.routes_read import router as read_router
from app.routes_write import router as write_router

log = logging.getLogger("dublinfix")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.media_dir, exist_ok=True)
    await ensure_indexes()
    try:
        await warm_up()
    except httpx.HTTPError as exc:
        log.warning("Could not warm up Ollaya model %s: %r", settings.ollaya_model, exc)
    watcher = asyncio.create_task(watch_reports())
    try:
        yield
    finally:
        watcher.cancel()
        with suppress(asyncio.CancelledError):
            await watcher


app = FastAPI(title="DublinFix AI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(write_router)
# check_dir=False: media_dir is created in lifespan, after this line runs.
app.mount("/media", StaticFiles(directory=settings.media_dir, check_dir=False), name="media")
app.include_router(read_router)
app.include_router(events_router)


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=3, max_length=2000)


@app.get("/health")
async def health():
    result = {"status": "ok", "model": settings.ollaya_model}
    try:
        # Bound the ping so /health answers fast instead of waiting out server selection.
        with pymongo.timeout(3):
            await client.admin.command("ping")
        result["mongodb"] = "reachable"
    except PyMongoError:
        result["mongodb"] = "unreachable"
        result["status"] = "degraded"
    try:
        async with httpx.AsyncClient(base_url=settings.ollaya_url, timeout=3) as ollaya:
            tags = (await ollaya.get("/api/tags")).json()
    except httpx.HTTPError:
        result["ollaya"] = "unreachable"
        result["status"] = "degraded"
        return result
    installed = {m["name"].removesuffix(":latest") for m in tags.get("models", [])}
    result["ollaya"] = "reachable"
    result["modelInstalled"] = settings.ollaya_model.removesuffix(":latest") in installed
    return result


@app.post("/classify", response_model=Classification)
async def classify_report(body: ClassifyRequest):
    try:
        return await classify(body.text)
    except ClassifierError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
