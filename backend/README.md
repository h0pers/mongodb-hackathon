# DublinFix AI backend

FastAPI service that stores city issue reports in MongoDB Atlas, classifies them with a local [Ollaya](https://ollaya.dev) decision model, and streams new reports live to the map.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- The Ollaya daemon on `localhost:11435` with `laya:multilingual` pulled:
  ```bash
  curl -fsSL https://ollaya.dev/install.sh | sh   # Apple silicon (macOS 14+) or Linux
  ollaya serve                                    # in its own terminal
  ollaya pull laya:multilingual
  ```
- A MongoDB Atlas cluster (below)

## Atlas setup

1. Create a free **M0** cluster at [cloud.mongodb.com](https://cloud.mongodb.com). M0 supports change streams, which the live feed needs.
2. **Database Access**: add a database user with read and write access.
3. **Network Access**: add your IP address. If your IP changes often, `0.0.0.0/0` works for a demo, but remove it and rotate the password afterwards.
4. **Connect > Drivers**: copy the `mongodb+srv://...` connection string and put it in `backend/.env` as `MONGODB_URI`.

The app creates the `dublinfix.reports` collection and its `2dsphere` index on startup. Never commit `.env`.

## Run

```bash
cd backend
cp .env.example .env   # then set MONGODB_URI
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs

### With Docker

Ollaya keeps running on the host; the container reaches it through `host.docker.internal`.

```bash
cd backend
docker compose up --build
```

Photos are stored in `backend/media/` on the host, so they survive container rebuilds.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Status of MongoDB and the Ollaya model |
| `POST` | `/reports` | Submit a report (multipart: `text`, `photo`, `lng`, `lat`). Returns `201` and the stored report |
| `GET` | `/reports?bbox=minLng,minLat,maxLng,maxLat&limit=500` | Reports inside the box, newest first. Without `bbox`, all reports. `limit` is 1 to 500 |
| `GET` | `/reports/{id}` | One report, `404` if it does not exist |
| `GET` | `/media/{fileName}` | The photo of a report (the `photoUrl` field) |
| `GET` | `/events` | Server-sent events: one `data:` message per new report, `: ping` every 15 s |
| `POST` | `/classify` | Classify text without storing it (JSON `{"text": ...}`) |

Submit rules: `text` is 3 to 2000 characters, `lng` is -180 to 180, `lat` is -90 to 90, and `photo` is JPEG, PNG or WebP up to 5 MB (`MAX_PHOTO_BYTES`). Invalid input gets `422`, an oversized photo gets `413`. If the model is down, the report is still stored with the model fields set to `null`.

## Try it

```bash
curl localhost:8000/health

# Terminal 1: watch new reports arrive
curl -N localhost:8000/events

# Terminal 2: submit one
curl -F text="Deep pothole on Dame Street, cars swerving" -F photo=@pothole.jpg \
     -F lng=-6.2654 -F lat=53.3441 localhost:8000/reports

# Read them back
curl "localhost:8000/reports?bbox=-6.4,53.2,-6.0,53.5"
curl localhost:8000/reports/<id>
curl -I localhost:8000/media/<fileName>.jpg

# Classify only, nothing stored
curl -X POST localhost:8000/classify -H 'content-type: application/json' \
  -d '{"text": "Traffic lights on Dame Street stuck on red, cars running through"}'

# Classify from the command line, no server needed
uv run python -m app.classifier "Street light is out at the corner, very dark at night"
```

## Report

```json
{
  "_id": "6720f1c2a9e4b3d5c8f01234",
  "text": "Deep pothole on Dame Street, cars swerving",
  "photoUrl": "/media/3f9c0e6b2a4d4c1e9b7a8d5f6e2c1b0a.jpg",
  "location": {"type": "Point", "coordinates": [-6.2654, 53.3441]},
  "category": "road_damage",
  "department": "Roads Maintenance",
  "urgency": 1.6371,
  "safetyHazard": 0.5057,
  "confidence": {"category": 0.95, "urgency": 0.5149}
}
```

- `location.coordinates` is `[lng, lat]`, longitude first (GeoJSON)
- `urgency`: 0 = can wait, 1 = this week, 2 = today (expected value, so it can fall between levels)
- `safetyHazard`: probability that people could get hurt
- `confidence`: 0 to 1 per question; low values are candidates for a review step
- Insert time comes from `_id` (a MongoDB ObjectId); there is no `createdAt`

The questions sent to the model live in `QUESTIONS` in `app/classifier.py`.

## Tests

```bash
uv run pytest
```

Tests need `MONGODB_URI` and use the `dublinfix_test` database, which they wipe after each test.
