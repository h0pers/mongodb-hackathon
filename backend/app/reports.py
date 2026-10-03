from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Point(BaseModel):
    """GeoJSON Point. Coordinates are [lng, lat], as MongoDB 2dsphere expects."""

    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]


class Report(BaseModel):
    """One stored report, as returned by every endpoint and SSE message.

    Model fields are null when the classifier was unavailable at submit time.
    Insert time comes from the ObjectId, so there is no createdAt field.
    """

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: str = Field(alias="_id")
    text: str
    photoUrl: str
    location: Point
    category: str | None = None
    department: str | None = None
    urgency: float | None = None
    safetyHazard: float | None = None
    confidence: dict[str, float] | None = None


def to_report(doc: dict[str, Any]) -> Report:
    return Report.model_validate({**doc, "_id": str(doc["_id"])})
