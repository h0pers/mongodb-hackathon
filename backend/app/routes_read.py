from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from app.db import reports
from app.reports import Report, to_report

router = APIRouter()


def parse_bbox(bbox: str) -> tuple[float, float, float, float]:
    """Parse "minLng,minLat,maxLng,maxLat" and reject anything that is not a valid box."""
    try:
        min_lng, min_lat, max_lng, max_lat = (float(part) for part in bbox.split(","))
    except ValueError:
        raise HTTPException(422, "bbox must be four numbers: minLng,minLat,maxLng,maxLat")
    if not (-180 <= min_lng < max_lng <= 180 and -90 <= min_lat < max_lat <= 90):
        raise HTTPException(422, "bbox needs -180 <= minLng < maxLng <= 180 and -90 <= minLat < maxLat <= 90")
    return min_lng, min_lat, max_lng, max_lat


@router.get("/reports", response_model=list[Report])
async def list_reports(bbox: str | None = None, limit: int = Query(500, ge=1, le=500)):
    query = {}
    if bbox is not None:
        min_lng, min_lat, max_lng, max_lat = parse_bbox(bbox)
        # A GeoJSON polygon uses the 2dsphere index; the legacy $box operator does not.
        ring = [[min_lng, min_lat], [max_lng, min_lat], [max_lng, max_lat], [min_lng, max_lat], [min_lng, min_lat]]
        query["location"] = {"$geoWithin": {"$geometry": {"type": "Polygon", "coordinates": [ring]}}}
    docs = await reports.find(query).sort("_id", -1).limit(limit).to_list()
    return [to_report(doc) for doc in docs]


@router.get("/reports/{report_id}", response_model=Report)
async def get_report(report_id: str):
    if not ObjectId.is_valid(report_id):
        raise HTTPException(422, "Invalid report id")
    doc = await reports.find_one({"_id": ObjectId(report_id)})
    if doc is None:
        raise HTTPException(404, "Report not found")
    return to_report(doc)
