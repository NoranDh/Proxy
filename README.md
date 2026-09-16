# Proxy — AI-Powered Failure Analysis System

Proxy assists engineers with root-cause analysis (RCA) of equipment/material
failures. It combines a computer-vision classifier for damage photos with an
LLM agent pipeline (grounded in API 571 damage mechanisms, a reference
handbook, and prior case studies via RAG) to suggest failure mechanisms,
walk through a 5-whys root-cause chain, and generate recommendations.

## Project structure

```
app.py              Flask backend — single-shot /api/analyze endpoint and
                     the /api/_imgcv image classification endpoint (YOLO)
main.py             FastAPI backend — full case workflow (create project,
                     upload evidence, run the LangGraph RCA pipeline,
                     clarification/review loop, generate report)

agents/              Pydantic schemas + reasoner/recommender LLM agents
scripts/             RAG ingestion, API 571 parsing, and the LangGraph
                     pipeline nodes (scripts/nodes/)
utils/               Shared helpers (LLM client, PDF handling, prompts,
                     case-state persistence)
rag/                 RAG ingestion/store helpers
frontend/MECC/       Static frontend (Index/CV/Agent pages)
data/                Reference data placeholders (API 571 mechanisms,
                     handbook, case studies — generated locally, not
                     committed; see below)
tests/               Manual smoke-test scripts for the pipeline nodes,
                     with sample fixtures under tests/fixtures/

uploads/, states/, reports/, runs/, db/
                     Runtime-generated data (uploaded evidence, saved
                     case state, generated .docx reports, CV run output).
                     Not tracked in git — created automatically at runtime.
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

copy .env.example .env       # then fill in your API keys
```

## Running

```bash
# FastAPI case-workflow backend
uvicorn main:app --reload

# Flask single-shot agent + CV backend
python app.py
```

The `data/` reference sets (API 571 mechanisms, handbook, case studies) are
generated locally via the scripts in `scripts/` (e.g. `clean_api571.py`,
`parse_api571.py`) — they aren't checked into the repo.

## Tests

The scripts under `tests/` are manual smoke tests for individual pipeline
nodes (not a full pytest suite yet). Run them from the repo root, e.g.:

```bash
python -m tests.test_completeness
```
