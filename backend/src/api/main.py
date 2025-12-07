from __future__ import annotations

import hashlib
import math
import re
import time
from typing import Dict, List, Optional
import uuid

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from .logging_utils import get_logger

logger = get_logger("api")

# Import BM25 utilities
try:
    from .bm25_utils import search_bm25
    BM25_AVAILABLE = True
except ImportError as e:
    logger.warning(f"BM25 not available: {e}")
    BM25_AVAILABLE = False

# Import LLM link for explanations
try:
    from .llm_utils import explain_results
except ImportError as e:
    logger.warning(f"LLM not available: {e}")


app = FastAPI(title="Off-the-Beaten-Path Travel API")

# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    log_data = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": round(process_time, 2)
    }
    
    logger.info("Request processed", extra={"props": log_data})
    
    return response

# Add event handler to preload bm25 index data to limit search time
@app.on_event("startup")
async def startup_event():
    """Preload BM25 index on API startup."""
    if BM25_AVAILABLE:
        logger.info("Preloading BM25 index...")
        try:
            from .bm25_utils import _load_blogs_from_db
            _load_blogs_from_db()
            logger.info("✓ BM25 index preloaded and ready!")
        except Exception as e:
            logger.error(f"✗ Failed to preload BM25 index: {e}")


# ----------------------------
# Models
# ----------------------------
class Filters(BaseModel):
    min_confidence: float = 0.0


class Retrieval(BaseModel):
    model: str = Field(pattern="^(bm25|faiss)$")
    k: int = 12


class SearchRequest(BaseModel):
    query: str
    filters: Filters
    retrieval: Retrieval
    ui: Optional[Dict] = None


class Result(BaseModel):
    destination: str
    country: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    score: float
    confidence: Optional[float] = None
    trend_delta: Optional[float] = None
    tags: List[str] = []
    context_cues: Dict[str, Dict[str, int]] = {}
    snippets: List[str] = []
    full_content: str
    why: Dict[str, object] = {}


class SearchResponse(BaseModel):
    query: str
    params: Dict[str, object]
    results: List[Result]
    explanations: List[str]


# ----------------------------
# Utility functions
# ----------------------------

def generate_explanations(req: SearchRequest, results):
    q = req.query
    explanations = []
    for r in results[0:3]:
        content = r.full_content
        try:
            gen_text = explain_results(q, content)
            explanations.append(gen_text)
        except Exception as e:
            logger.error(f"LLM explanation failed: {e}")
            explanations.append("Explanation unavailable.")
    
    return explanations


# ----------------------------
# Search functions
# ----------------------------

# BM25 Search Handler
def bm25_search(req: SearchRequest) -> List[Result]:
    """Handle BM25 search using the database."""
    if not BM25_AVAILABLE:
        # Return empty results if BM25 not available
        logger.warning("BM25 search requested but model is not available.")
        return []
    
    logger.info(f"Executing BM25 search for query: '{req.query}'")
    # Call the BM25 utility function
    raw_results = search_bm25(req.query, top_n = req.retrieval.k)
    
    logger.info(f"BM25 found {len(raw_results)} raw results")

    results = []
    for r in raw_results:
        if "destination" not in r:
            logger.error("BM25 result missing required field 'destination'", extra={"props": r})
            continue
        # Create snippets from content preview and description
        snippets = []
        if r.get("description"):
            snippets.append(r["description"])
        if r.get("content_preview"):
            snippets.append(r["content_preview"])
        
        # Calculate confidence based on score (normalize to 0-1)
        # BM25 scores are unbounded, so we use a sigmoid-like function
        confidence = min(1.0, r["score"] / 10.0)  # Adjust divisor based on your score range
        
        results.append(
            Result(
                destination = r["destination"],
                country = r.get("country", ""),
                lat = r.get("lat"),
                lon = r.get("lon"),
                score = round(r["score"], 4),
                confidence = round(confidence, 4),
                trend_delta = None,
                tags = [],  # BM25 results don't have structured tags
                context_cues = {},
                snippets = snippets[:2],  # Limit to 2 snippets
                full_content = r.get('full_content'),
                why = {
                    "model": "BM25",
                    "page_title": r.get("page_title", ""),
                    "page_url": r.get("page_url", ""),
                    "blog_url": r.get("blog_url", ""),
                    "author": r.get("author", ""),
                },
            )
        )
    
    return results

# FAISS Search Handler
def faiss_search(req: SearchRequest) -> List[Result]:
    """Handle FAISS search using the database."""

    logger.info(f"Executing FAISS search for query: '{req.query}'")
    ### UPDATE HERE *******
    
    # Call the FAISS utility function
    # raw_results = search_faiss(req.query, top_n = req.retrieval.k)
    raw_results = []  # Placeholder until FAISS utility is implemented
    
    logger.info(f"FAISS found {len(raw_results)} raw results")

    results = []
    for r in raw_results:
        # Create snippets from content preview and description
        snippets = []
        if r.get("description"):
            snippets.append(r["description"])
        if r.get("content_preview"):
            snippets.append(r["content_preview"])
        
        # Calculate confidence based on score (normalize to 0-1)
        # BM25 scores are unbounded, so we use a sigmoid-like function
        confidence = min(1.0, r["score"] / 10.0)  # Adjust divisor based on your score range
        
        results.append(
            Result(
                destination = r["destination"],
                country = r.get("country", ""),
                lat = r.get("lat"),
                lon = r.get("lon"),
                score = round(r["score"], 4),
                confidence = round(confidence, 4),
                trend_delta = None,
                tags = [],  # BM25 results don't have structured tags
                context_cues = {},
                snippets = snippets[:2],  # Limit to 2 snippets
                full_content = r.get('full_content'),
                why = {
                    "model": "FAISS",
                    "page_title": r.get("page_title", ""),
                    "page_url": r.get("page_url", ""),
                    "blog_url": r.get("blog_url", ""),
                    "author": r.get("author", ""),
                },
            )
        )
    
    return results

# ----------------------------
# API
# ----------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "bm25_model_available": BM25_AVAILABLE,
    }


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    """
    Return a search result based on type of search
    Either BM25 or FAISS
    """
    
    # Route to BM25 if selected
    if req.retrieval.model == "bm25":
        results = bm25_search(req)
        explanations = generate_explanations(req, results)

        return SearchResponse(
            query = req.query,
            params = {
                "filters": req.filters.model_dump(),
                "retrieval": req.retrieval.model_dump(),
                "model_used": "bm25",
            },
            results = results,
            explanations = explanations,
        )
    # Route to FAISS if selected
    if req.retrieval.model == "faiss":
        results = faiss_search(req)
        explanations = generate_explanations(req, results)

        return SearchResponse(
            query = req.query,
            params = {
                "filters": req.filters.model_dump(),
                "retrieval": req.retrieval.model_dump(),
                "model_used": "faiss",
            },
            results = results,
            explanations = explanations,
        )
    