# Dublin Fix backend

FastAPI service that classifies city issue reports with a local [Ollaya](https://ollaya.dev) decision model.

## Run

Requires [uv](https://docs.astral.sh/uv/) and the Ollaya daemon running on `localhost:11435` with `laya:multilingual` pulled (`ollaya pull laya:multilingual`).

```bash
cd backend
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

## Try it

```bash
# Classify one report from the command line, no server needed
uv run python -m app.classifier "Street light is out at the corner, very dark at night"

# Through the API
curl localhost:8000/health
curl -X POST localhost:8000/classify -H 'content-type: application/json' \
  -d '{"text": "Traffic lights on Dame Street stuck on red, cars running through"}'
```

Interactive docs: http://localhost:8000/docs

## Response

```json
{
  "category": "litter",
  "department": "Waste Management",
  "urgency": 1.6371,
  "safetyHazard": 0.5057,
  "confidence": {"category": 0.95, "urgency": 0.5149},
  "model": "laya:multilingual",
  "latencyMs": 2818
}
```

- `urgency`: 0 = can wait, 1 = this week, 2 = today (expected value, so it can fall between levels)
- `safetyHazard`: probability that people could get hurt
- `confidence`: 0 to 1 per question; low values are candidates for a review step

The questions sent to the model live in `QUESTIONS` in `app/classifier.py`.
