import os
import tempfile

# Settings are read when app.config is imported, so these must be set first.
# Environment variables take precedence over backend/.env.
os.environ["MONGODB_DB"] = "dublinfix_test"
os.environ["MEDIA_DIR"] = tempfile.mkdtemp(prefix="dublinfix-media-")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pymongo import MongoClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    # One TestClient for the whole session: the app's AsyncMongoClient binds to
    # the event loop of the first client that uses it.
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def test_db():
    """Synchronous handle on dublinfix_test, for checking and cleaning up."""
    mongo = MongoClient(settings.mongodb_uri)
    yield mongo[settings.mongodb_db]
    mongo.close()


@pytest.fixture(autouse=True)
def clean_reports(test_db):
    yield
    test_db.reports.delete_many({})
