from pymongo import GEOSPHERE, AsyncMongoClient

from app.config import settings

client = AsyncMongoClient(settings.mongodb_uri)
reports = client[settings.mongodb_db]["reports"]


async def ensure_indexes() -> None:
    await reports.create_index([("location", GEOSPHERE)])
