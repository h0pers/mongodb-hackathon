# DublinFix AI

Hackathon app: citizens report city issues (text + photo + location), a local model classifies them, and a live map shows them.

- `backend/`: FastAPI service, MongoDB Atlas, local Ollaya model. Python ≥3.12, managed with `uv`.
- `frontend/`: Vue 3 + Vite + Pinia + Tailwind 4 + shadcn-vue (reka-ui). Deployed to GitHub Pages on push to `main` (`.github/workflows/deploy-frontend.yml`, runs `npm run lint` then `npm run build`).

## Commands

```bash
# backend
cd backend && uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run python -m app.classifier "Street light is out"   # classify without the server

# frontend
cd frontend && npm ci
npm run dev
npm run lint
```

## Backend layout

- `app/config.py`: pydantic `Settings` loaded from `backend/.env`. `MONGODB_URI` is required, so the app won't start without it.
- `app/db.py`: the one `AsyncMongoClient` (native pymongo async; do not add Motor), the `reports` collection handle, `ensure_indexes()`.
- `app/reports.py`: `Report` model and `to_report(doc)`. Every endpoint and SSE message must go through `to_report`, so `_id`→string conversion lives in one place.
- `app/classifier.py`: `classify(text)`. All model-specific code stays behind this function. Department is derived from category, never asked of the model.
- `app/main.py`: app, CORS, lifespan (creates `media_dir`, runs `ensure_indexes()`, warms up the model). New routes go in their own router files and are wired in with `include_router`.

## Data rules

- One collection: `dublinfix.reports`. Tests use database `dublinfix_test`.
- `location` is a GeoJSON Point with coordinates `[lng, lat]` (longitude first), backed by a `2dsphere` index.
- No `createdAt`: insert time comes from the ObjectId. No `status` field: reports have no lifecycle.
- Model fields (`category`, `department`, `urgency`, `safetyHazard`, `confidence`) are null when the classifier failed. A submitted report must never be lost because the model is down.
- Clients never send model fields.

## Environment

- Model daemon is Ollaya on `localhost:11435` (not Ollama `:11434`), model `laya:multilingual`.
- Atlas cluster `cluster0.duikvv5` (AWS). Network Access is `0.0.0.0/0` because the owner's IP rotates. Tighten this and rotate the DB password after the hackathon.
- Never commit `.env` files or credentials. `.env.example` lists every setting; keep it in sync with `config.py`.
