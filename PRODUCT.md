# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Dublin residents** who notice a city problem (pothole, broken street light, faulty traffic signal, litter, water leak) and want to report it in seconds, usually standing on the street with a phone in one hand. _(Phone-first is inferred from the brief's "location assigned automatically" and the reporting scene; not confirmed.)_
- **Council staff** who watch the same map as a live, urgency-sorted work queue. _(Secondary audience on this surface; inferred.)_
- **Hackathon judges** watching a two-minute demo on a laptop or projector.

## Product Purpose

Dublin Fix — "AI triage for city issue reports". Residents report problems in plain text with an optional photo; location is attached automatically. A local decision model classifies each report in about a second, and MongoDB turns the reports into a live, de-duplicated work queue for the council. Success: a report takes seconds to file, appears on the map immediately, and dangerous problems rise to the top instead of waiting behind minor ones.

## Positioning

A decision model with fixed answers and probabilities, not a chatbot: every report gets a category, urgency, safety-hazard probability and department. Duplicates (same category within 150 m, or semantically similar via Vector Search) merge into one issue whose counter goes up.

## Operating Context

- Map of Dublin is the primary surface: report pins, later heatmaps and clusters.
- Reporting flow: describe the problem, optionally attach a photo, location defaults to the device's current position; the user can pick another spot instead.
- Pins are coloured by urgency once the model has answered.
- The board updates live (MongoDB change streams) without a page refresh.

## Capabilities and Constraints

Model answers (fixed vocabulary — use these exact terms):

| Question | Options |
|---|---|
| Category | Road, lighting, traffic signal, waste, water, other |
| Urgency | 0 = can wait, 1 = this week, 2 = today |
| Safety hazard | yes/no with probability |
| Department | Roads, public lighting, waste management, water services |

- Stack: Vue 3, Vite, Tailwind v4, shadcn-vue (JS, not TS), Pinia, vue-router; deployed to GitHub Pages under `/mongodb-hackathon/`.
- Map: MapLibre GL — chosen because the roadmap needs points, clusters and heatmaps from one GeoJSON source.
- Backend: built by teammates in the same repo; the API contract is **not yet confirmed**. The frontend defines `POST /api/reports` (multipart) and `GET /api/reports`, base URL from `VITE_API_URL`, with mock data when the backend is unavailable. _(Inferred.)_
- Uncertain model answers go to a human review queue (later surface).

## Brand Commitments

- Name: **Dublin Fix**. Tagline in the brief: "AI triage for city issue reports".

## Evidence on Hand

- `MongoDB Hackathon.pdf` — the technical brief.
- No real reports, photos or statistics exist yet. Any reports shown before the backend is live are synthetic demo data and must be labelled as such.

## Product Principles

1. Reporting must take seconds: one primary action, sensible defaults, location filled in for you.
2. The map is the product: everything else floats over it and gets out of its way.
3. Urgency is the signal: colour and order always express how urgent something is, never decoration.
4. Show the triage working: category, urgency and department are visible, not hidden.