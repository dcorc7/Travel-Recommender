# Retrieval Models — BM25 vs ModernBERT

This project supports two retrieval engines:

1. **BM25 (Lexical Keyword-Based Retrieval)**
2. **ModernBERT (Semantic Vector Retrieval using Embeddings + FAISS)**

Both models serve different purposes depending on the type of user query.  
This page explains how each model works, how they differ, and when each should be used.

---

## BM25 — Keyword-Based Retrieval

BM25 ranks documents based on literal word overlap with the user query.  
It is lightweight, fast, and requires no embeddings or model inference at search time.

### How It Works

1. Tokenizes text using whitespace + regex
2. Assigns weights based on frequency (TF) + rarity (IDF)
3. Scores documents based on word overlap with the query
4. Returns top-k pages sorted by lexical similarity

### Pros

| Strength | Notes |
|---|---|
| Extremely fast | No GPU needed, pure CPU scoring |
| Transparent | Results easy to interpret |
| Great for precise keyword searches | `"surf spots bali"`, `"train routes italy"` |
| No embedding storage | Works directly on raw text |

### Limitations

| Limitation | Example |
|---|---|
| Fails on semantic meaning | `"quiet places to relax"` ≠ `"secluded beaches"` |
| No understanding of synonyms | `"hike"` ≠ `"trek"` unless explicitly present |
| Scores depend on exact token matches | Sensitive to phrasing changes |

---

## ModernBERT — Semantic Retrieval with Embeddings

ModernBERT encodes text into a dense vector representation** where similar ideas map close together in vector space.  
We store embeddings offline (precomputed) and query them using FAISS L2 similarity search.

### How It Works

1. Cleaned blog text → fed into ModernBERT encoder
2. Output embedding dimension: 768-d vector
3. Vectors stored in DB or S3 for fast lookup
4. Search query is encoded the same way → nearest vectors retrieved

### Pros

| Strength | Notes |
|---|---|
| Understands meaning, not just words | `"snowy mountain trip"` ≈ `"alpine winter getaway"` |
| Robust to rephrasing | Better for natural language queries |
| Great for inspiration & exploratory travel | non-specific prompts perform well |

### Limitations

| Limitation | Notes |
|---|---|
| Requires precomputed embeddings | Storage + preprocessing step |
| Slower inference vs BM25 | Must embed query text at runtime |
| Less interpretable scoring | Vectors represent latent meaning, not words |

---

## When To Use Which Model?

| Task Type | Best Model | Why |
|---|---|---|
| Precise keyword search | **BM25** | Fast, literal matching |
| Exploratory inspiration | **ModernBERT** | Understands natural language |
| Off-the-beaten-path discovery | **ModernBERT** | Better semantic generalization |
| Debug/search metadata quickly | **BM25** | Returns predictable results |
| You care about synonyms & meaning | **ModernBERT** | Semantic vector space search |

---

## Example Comparison

| Query | BM25 Output | ModernBERT Output |
|---|---|---|
| `"Hiking in Peru"` | Matches blogs with the phrase "hiking in Peru" | Also finds Machu Picchu treks & nearby regions |
| `"quiet coastal towns"` | Might miss articles without exact words | Finds "hidden beaches", "small fishing villages" |
| `"street food asia"` | Exact food + asia pages | Discovers related markets, night bazaars, cultural food tours |

---

## Usage in Code

```python
# BM25 keyword ranking
from off_the_path.retrieval import bm25_search
bm25_results = bm25_search("sunset beach greece", top_k=10)

# ModernBERT semantic search
from off_the_path.retrieval import semantic_search
bert_results = semantic_search("romantic seaside towns", top_k=10)
```

## Summary

| Feature                         | BM25          | ModernBERT                   |
| ------------------------------- | ------------- | ---------------------------- |
| Retrieval Type                  | Lexical       | Semantic                     |
| Requires Embeddings             | ❌            | ✔                            |
| Good for Exact Keywords         | ✔             | ~                            |
| Handles Synonyms / Concepts     | ~             | ✔                            |
| Ideal for Travel Recommendation | Good baseline | **Best performance overall** |

Both models together allow users to switch between precise keyword search (BM25) and meaning-aware travel recommendations (ModernBERT). This hybrid design enables a more flexible and powerful retrieval experience for diverse queries.