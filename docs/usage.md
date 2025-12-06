# Usage Guide

This page explains how to run queries, access the retrieval models, interact with the API, and use the Streamlit web interface. Both BM25 (keyword-based) and ModernBERT (semantic embeddings) retrieval modes are supported.

---

## 1. Using the Streamlit UI (Primary User Interface)

The frontend provides an easy way to query travel blogs and compare retrieval models.

### Start UI

If running locally (without Docker):

```bash
uv run streamlit run frontend/streamlit_app/app.py
```

If using Docker:

```bash
docker compose up
```

### In the Browser

Go to: http://localhost:8501

| Feature                         | Description                                     |
| ------------------------------- | ----------------------------------------------- |
| Enter a travel query            | e.g., *"best hiking trails near Banff"*         |
| Select retrieval model          | **BM25** (lexical) or **ModernBERT** (semantic) |
| View ranked destination results | Title, snippet, link + metadata                 |
| Explore multiple suggestions    | Compare relevance between models                |


Example Query Inputs:

```
"hidden beaches in southeast asia"
"europe backpacking train routes"
"food culture tours in mexico city"
```

## 2. Using the FastAPI Backend Directly

The backend exposes endpoints for retrieval programmatically.

### Open Swagger UI

http://localhost:8000/docs

### Example Requests

#### BM25 Search

```bash
curl -X POST "http://localhost:8000/search/bm25" \
    -H "Content-Type: application/json" \
    -d '{"query": "camping in Iceland", "k": 5}'
```

#### ModernBERT Semantic Search

```bash
curl -X POST "http://localhost:8000/search/modernbert" \
    -H "Content-Type: application/json" \
    -d '{"query": "volcano hikes", "k": 5}'
```

### Data Structure Returned

Responses follow a consistent JSON format:

```json
[
  {
    "title": "Hidden Lakes near Banff",
    "snippet": "A quiet alpine trail away from tourists...",
    "url": "https://example.com/post123",
    "location": "Banff National Park",
    "distance": 0.124   // similarity score (lower = better)
  }
]
```