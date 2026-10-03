import pytest
from bson import ObjectId

from app.events import QUEUE_SIZE, Broadcaster


def make_doc(lng: float, lat: float, text: str) -> dict:
    return {
        "_id": ObjectId(),
        "text": text,
        "photoUrl": "/media/test.jpg",
        "location": {"type": "Point", "coordinates": [lng, lat]},
        "category": None,
        "department": None,
        "urgency": None,
        "safetyHazard": None,
        "confidence": None,
    }


@pytest.fixture
def dublin_docs(test_db):
    """Two reports in Dublin and one in Cork, inserted oldest first."""
    docs = [
        make_doc(-6.2654, 53.3441, "Pothole on Dame Street"),
        make_doc(-8.4706, 51.8985, "Bin overflowing in Cork"),
        make_doc(-6.2603, 53.3498, "Blocked drain on O'Connell Street"),
    ]
    test_db.reports.insert_many(docs)
    return docs


DUBLIN_BBOX = "-6.4,53.2,-6.0,53.5"


def test_bbox_returns_only_reports_inside_newest_first(client, dublin_docs):
    response = client.get("/reports", params={"bbox": DUBLIN_BBOX})
    assert response.status_code == 200
    ids = [r["_id"] for r in response.json()]
    assert ids == [str(dublin_docs[2]["_id"]), str(dublin_docs[0]["_id"])]


def test_report_shape_uses_string_id_and_lng_lat(client, dublin_docs):
    body = client.get(f"/reports/{dublin_docs[0]['_id']}").json()
    assert body["_id"] == str(dublin_docs[0]["_id"])
    assert body["location"] == {"type": "Point", "coordinates": [-6.2654, 53.3441]}
    assert body["category"] is None


def test_limit_caps_results(client, dublin_docs):
    response = client.get("/reports", params={"bbox": DUBLIN_BBOX, "limit": 1})
    assert [r["_id"] for r in response.json()] == [str(dublin_docs[2]["_id"])]


@pytest.mark.parametrize(
    "bbox",
    [
        "1,2,3",  # too few numbers
        "a,b,c,d",  # not numbers
        "-6.0,53.2,-6.4,53.5",  # minLng > maxLng
        "-6.4,53.5,-6.0,53.2",  # minLat > maxLat
        "-200,53.2,-6.0,53.5",  # lng out of range
        "-6.4,-91,-6.0,53.5",  # lat out of range
    ],
)
def test_invalid_bbox_is_rejected(client, bbox):
    assert client.get("/reports", params={"bbox": bbox}).status_code == 422


def test_limit_out_of_range_is_rejected(client):
    assert client.get("/reports", params={"limit": 0}).status_code == 422
    assert client.get("/reports", params={"limit": 501}).status_code == 422


def test_unknown_report_is_404(client):
    assert client.get(f"/reports/{ObjectId()}").status_code == 404


def test_invalid_report_id_is_422(client):
    assert client.get("/reports/not-an-object-id").status_code == 422


def test_broadcaster_delivers_to_every_subscriber():
    broadcaster = Broadcaster()
    first, second = broadcaster.subscribe(), broadcaster.subscribe()
    broadcaster.publish("hello")
    assert first.get_nowait() == "hello"
    assert second.get_nowait() == "hello"


def test_broadcaster_drops_slow_subscriber_and_ends_its_stream():
    broadcaster = Broadcaster()
    slow = broadcaster.subscribe()
    for i in range(QUEUE_SIZE + 1):
        broadcaster.publish(str(i))
    assert slow.get_nowait() is None
    assert slow.empty()
    broadcaster.publish("after")
    assert slow.empty()
