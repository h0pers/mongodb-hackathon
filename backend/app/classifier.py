"""Report classification with a local Ollaya decision model.

Everything model-specific lives behind `classify()`, so it can be swapped for
a regular LLM on the day without touching the rest of the backend.
"""

import json
import sys

import httpx
from pydantic import BaseModel, Field

from app.config import settings

CATEGORY_QUESTION = {
    "type": "choice",
    "instructions": "What kind of city problem does this report describe?",
    "criteria": {
        "road_damage": "Potholes, broken footpaths or damaged road surface",
        "dirt": "Mud, spills, stains, dust or fallen leaves on a street or footpath that need cleaning",
        "litter": "Rubbish, overflowing bins, dumped bags or illegally dumped items that need collecting",
        "water_drainage": "Flooding, blocked drains or water leaks",
        "unsafe_area": "A place that feels unsafe because of anti-social behaviour, harassment, suspected drug dealing or other threatening activity",
        "other": "Anything that fits none of the other options",
    },
}

# Department is looked up from the category, not asked of the model, so the
# two can never contradict each other.
DEPARTMENTS = {
    "road_damage": "Roads Maintenance",
    "dirt": "Street Cleaning",
    "litter": "Waste Management",
    "water_drainage": "Drainage and Water",
    "unsafe_area": "Community Safety",
    "other": "General Enquiries",
}

QUESTIONS = {
    "category": CATEGORY_QUESTION,
    "urgency": {
        "type": "score",
        "instructions": "How urgently does this problem need to be fixed?",
        "criteria": ["Can wait", "This week", "Today"],
    },
    "safetyHazard": {
        "type": "noul",
        "instructions": "People could get hurt because of this problem.",
        "criteria": {
            "true": "The problem is a danger to people",
            "false": "The problem is not dangerous",
        },
    },
}


class Classification(BaseModel):
    category: str
    department: str
    urgency: float = Field(description="0 = can wait, 1 = this week, 2 = today")
    safetyHazard: float = Field(description="Probability that people could get hurt")
    confidence: dict[str, float] = Field(
        description="Model confidence per choice question, for flagging unsure answers"
    )
    model: str
    latencyMs: int


class ClassifierError(RuntimeError):
    pass


_client = httpx.AsyncClient(base_url=settings.ollaya_url, timeout=settings.ollaya_timeout)


async def classify(text: str) -> Classification:
    try:
        response = await _client.post(
            "/api/decide",
            json={
                "model": settings.ollaya_model,
                "state": text,
                "questions": QUESTIONS,
                "keep_alive": "30m",
            },
        )
    except httpx.HTTPError as exc:
        raise ClassifierError(f"Ollaya is unreachable at {settings.ollaya_url}: {exc!r}") from exc
    if response.is_error:
        raise ClassifierError(f"Ollaya error {response.status_code}: {response.text}")

    body = response.json()
    answers = body["answers"]
    return Classification(
        category=answers["category"]["choice"],
        department=DEPARTMENTS[answers["category"]["choice"]],
        urgency=answers["urgency"]["score"],
        safetyHazard=answers["safetyHazard"]["noul"],
        confidence={
            "category": answers["category"]["confidence"],
            "urgency": answers["urgency"]["confidence"],
        },
        model=body["model"],
        latencyMs=round(body["total_duration"] / 1_000_000),
    )


async def warm_up() -> None:
    """Load the model into memory so the first real report is not slow."""
    await _client.post("/api/decide", json={"model": settings.ollaya_model, "keep_alive": "30m"})


if __name__ == "__main__":
    import asyncio

    report = " ".join(sys.argv[1:]) or "Street light is out at the corner, very dark at night"
    result = asyncio.run(classify(report))
    print(json.dumps(result.model_dump(), indent=2))
