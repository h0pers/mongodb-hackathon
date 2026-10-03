"""Write path: submitting a report (FR1) and classifying it (FR2)."""

import logging
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pymongo.errors import PyMongoError

from app.classifier import ClassifierError, classify
from app.config import settings
from app.db import reports
from app.reports import MODEL_FIELDS, Report, to_report

log = logging.getLogger("dublinfix")

router = APIRouter()

# The stored extension comes from the content type, never the client file name.
PHOTO_EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@router.post("/reports", status_code=status.HTTP_201_CREATED, response_model=Report)
async def create_report(
    text: Annotated[str, Form(min_length=3, max_length=2000)],
    lng: Annotated[float, Form(ge=-180, le=180)],
    lat: Annotated[float, Form(ge=-90, le=90)],
    photo: Annotated[UploadFile, File()],
):
    extension = PHOTO_EXTENSIONS.get(photo.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"photo must be one of {', '.join(PHOTO_EXTENSIONS)}",
        )
    # Read one byte past the limit so an oversized upload is detected without
    # holding more than that in memory.
    data = await photo.read(settings.max_photo_bytes + 1)
    if len(data) > settings.max_photo_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"photo is larger than {settings.max_photo_bytes} bytes",
        )
    if not data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="photo is empty")

    file_name = uuid4().hex + extension
    photo_path = Path(settings.media_dir) / file_name
    photo_path.write_bytes(data)

    try:
        classification = (await classify(text)).model_dump(include=set(MODEL_FIELDS))
    except ClassifierError as exc:
        # The report is still stored: a resident's report is never lost because
        # the model is down.
        log.warning("Storing report without classification: %s", exc)
        classification = dict.fromkeys(MODEL_FIELDS)

    doc = {
        "text": text,
        "photoUrl": f"/media/{file_name}",
        "location": {"type": "Point", "coordinates": [lng, lat]},
        **classification,
    }
    try:
        await reports.insert_one(doc)
    except PyMongoError as exc:
        photo_path.unlink(missing_ok=True)
        log.error("Could not store report: %r", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not store the report, please try again",
        )
    return to_report(doc)
