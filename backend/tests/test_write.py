from pathlib import Path

import pytest
from bson import ObjectId
from pymongo.errors import PyMongoError

from app import routes_write
from app.classifier import Classification, ClassifierError
from app.config import settings

# Smallest valid PNG header; the endpoint checks the content type, not the pixels.
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32

CLASSIFICATION = Classification(
    category="road_damage",
    department="Roads Maintenance",
    urgency=1.7,
    safetyHazard=0.8,
    confidence={"category": 0.9, "urgency": 0.5},
    model="laya:multilingual",
    latencyMs=500,
)


def form(**overrides):
    data = {"text": "Deep pothole on Dame Street", "lng": "-6.2654", "lat": "53.3441"}
    data.update(overrides)
    return data


def photo(content=PNG, content_type="image/png", name="pothole.png"):
    return {"photo": (name, content, content_type)}


def media_files():
    return sorted(Path(settings.media_dir).iterdir())


@pytest.fixture
def classify_ok(monkeypatch):
    async def fake(text):
        return CLASSIFICATION

    monkeypatch.setattr(routes_write, "classify", fake)


@pytest.fixture
def classify_down(monkeypatch):
    async def fake(text):
        raise ClassifierError("Ollaya is unreachable")

    monkeypatch.setattr(routes_write, "classify", fake)


def test_create_report_stores_classified_report(client, test_db, classify_ok):
    response = client.post("/reports", data=form(), files=photo())

    assert response.status_code == 201
    body = response.json()
    assert body["text"] == "Deep pothole on Dame Street"
    assert body["location"] == {"type": "Point", "coordinates": [-6.2654, 53.3441]}
    assert body["category"] == "road_damage"
    assert body["department"] == "Roads Maintenance"
    assert body["urgency"] == 1.7
    assert body["safetyHazard"] == 0.8
    assert body["confidence"] == {"category": 0.9, "urgency": 0.5}
    assert "model" not in body and "latencyMs" not in body

    doc = test_db.reports.find_one({"_id": ObjectId(body["_id"])})
    assert doc["text"] == body["text"]
    assert doc["location"]["coordinates"] == [-6.2654, 53.3441]
    assert doc["category"] == "road_damage"

    # Served under /media with a server-chosen name and an extension from the content type.
    assert body["photoUrl"].startswith("/media/") and body["photoUrl"].endswith(".png")
    assert "pothole" not in body["photoUrl"]
    served = client.get(body["photoUrl"])
    assert served.status_code == 200
    assert served.content == PNG


def test_create_report_survives_classifier_failure(client, test_db, classify_down):
    response = client.post("/reports", data=form(), files=photo())

    assert response.status_code == 201
    body = response.json()
    for field in ("category", "department", "urgency", "safetyHazard", "confidence"):
        assert body[field] is None
    doc = test_db.reports.find_one({"_id": ObjectId(body["_id"])})
    assert doc is not None
    assert doc["category"] is None


def test_client_cannot_set_model_fields(client, test_db, classify_down):
    response = client.post("/reports", data=form(category="other", urgency="2"), files=photo())

    assert response.status_code == 201
    assert response.json()["category"] is None
    assert response.json()["urgency"] is None


@pytest.mark.parametrize("content_type, extension", [("image/jpeg", ".jpg"), ("image/webp", ".webp")])
def test_extension_comes_from_content_type(client, classify_ok, content_type, extension):
    response = client.post(
        "/reports", data=form(), files=photo(content_type=content_type, name="evil.html")
    )

    assert response.status_code == 201
    assert response.json()["photoUrl"].endswith(extension)


@pytest.mark.parametrize(
    "overrides",
    [
        {"text": "hi"},
        {"text": "x" * 2001},
        {"lng": "-180.1"},
        {"lng": "180.1"},
        {"lat": "-90.1"},
        {"lat": "90.1"},
        {"lat": "north"},
    ],
)
def test_rejects_invalid_fields(client, test_db, classify_ok, overrides):
    before = media_files()
    response = client.post("/reports", data=form(**overrides), files=photo())

    assert response.status_code == 422
    assert media_files() == before
    assert test_db.reports.count_documents({}) == 0


def test_rejects_missing_photo(client, classify_ok):
    response = client.post("/reports", data=form())

    assert response.status_code == 422


@pytest.mark.parametrize("content_type", ["text/html", "image/gif", "application/octet-stream"])
def test_rejects_unsupported_photo_type(client, test_db, classify_ok, content_type):
    before = media_files()
    response = client.post("/reports", data=form(), files=photo(content_type=content_type))

    assert response.status_code == 422
    assert media_files() == before
    assert test_db.reports.count_documents({}) == 0


def test_rejects_empty_photo(client, classify_ok):
    response = client.post("/reports", data=form(), files=photo(content=b""))

    assert response.status_code == 422


def test_rejects_oversized_photo(client, test_db, classify_ok, monkeypatch):
    monkeypatch.setattr(settings, "max_photo_bytes", 10)
    before = media_files()
    response = client.post("/reports", data=form(), files=photo(content=b"x" * 11))

    assert response.status_code == 413
    assert media_files() == before
    assert test_db.reports.count_documents({}) == 0


def test_photo_at_size_limit_is_accepted(client, classify_ok, monkeypatch):
    monkeypatch.setattr(settings, "max_photo_bytes", len(PNG))
    response = client.post("/reports", data=form(), files=photo())

    assert response.status_code == 201


def test_insert_failure_removes_photo_and_returns_503(client, classify_ok, monkeypatch):
    class BrokenCollection:
        async def insert_one(self, doc):
            raise PyMongoError("Atlas is down")

    monkeypatch.setattr(routes_write, "reports", BrokenCollection())
    before = media_files()
    response = client.post("/reports", data=form(), files=photo())

    assert response.status_code == 503
    assert media_files() == before


def test_classify_endpoint_still_available(client, monkeypatch):
    async def fake(text):
        return CLASSIFICATION

    monkeypatch.setattr("app.main.classify", fake)
    response = client.post("/classify", json={"text": "Deep pothole on Dame Street"})

    assert response.status_code == 200
    assert response.json()["category"] == "road_damage"
