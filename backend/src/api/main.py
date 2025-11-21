from __future__ import annotations

import hashlib
import math
import re
from typing import Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Off-the-Beaten-Path Travel API")

# ----------------------------
# Config / Signals
# ----------------------------
POS_CUES = ["hidden gem", "locals only", "underrated", "rarely visited", "off the beaten path"]
NEG_CUES = ["bucket list", "must-see", "tourist hotspot", "crowded"]

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-']{2,}")

# ----------------------------
# Tiny in-memory "corpus"
# Replace with your IR index later
# popularity: larger -> more popular; used for penalties
# ----------------------------
CORPUS = [
    {
        "destination": "Langtang Side Valleys",
        "country": "Nepal",
        "lat": 28.208, "lon": 85.5,
        "tags": ["mountain", "quiet", "local", "hiking", "tea-houses"],
        "popularity": 120,  # low
        "snippets": [
            "A quiet valley beyond the popular circuits—locals-only tea houses.",
            "Yak pastures and dawn bells; rarely visited side routes.",
        ],
    },
    {
        "destination": "Ninh Binh Backwaters",
        "country": "Vietnam",
        "lat": 20.25, "lon": 105.9,
        "tags": ["karst", "kayak", "quiet", "river", "photography"],
        "popularity": 350,  # medium
        "snippets": [
            "Pre-sunrise kayak under limestone arches—no tour buses.",
            "Herons wake along quiet canals; underrated and serene.",
        ],
    },
    {
        "destination": "Svaneti Tower Villages",
        "country": "Georgia",
        "lat": 43.05, "lon": 42.7,
        "tags": ["alpine", "culture", "hiking", "medieval", "scenic"],
        "popularity": 500,  # medium-high
        "snippets": [
            "Stone towers, hay meadows, and trails stitched between clouds.",
            "A quieter alternative to crowded alpine circuits.",
        ],
    },
    {
        "destination": "Oaxaca Dawn Markets",
        "country": "Mexico",
        "lat": 17.065, "lon": -96.72,
        "tags": ["food", "markets", "culture", "local", "photography"],
        "popularity": 2000,  # high (to exercise Bloom/Zipf)
        "snippets": [
            "Corn griddles and chocolate steam; quiet courtyards before the day begins.",
            "Beloved by locals; avoid the bucket list crowds later in the day.",
        ],
    },
]

# Precompute a "bloomish" set: top-N by popularity
BLOOM_THRESHOLD = 1000  # anything above is considered too popular
BLOOM_SET = {row["destination"] for row in CORPUS if row["popularity"] >= BLOOM_THRESHOLD}


# ----------------------------
# Models
# ----------------------------
class Filters(BaseModel):
    geotype: List[str] = []
    culture: List[str] = []
    experience: List[str] = []
    min_confidence: float = 0.0


class Retrieval(BaseModel):
    model: str = Field(pattern="^(attribute\+context|bm25|tfidf)$")
    use_bloom: bool = True
    zipf_penalty: float = 0.35  # 0..1
    tier_bucketing: bool = True
    use_trends: bool = False
    date_range: str = "1y"  # "all" | "1y" | "90d" | "30d"
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
    why: Dict[str, object] = {}


class SearchResponse(BaseModel):
    query: str
    params: Dict[str, object]
    results: List[Result]


# ----------------------------
# Utility functions
# ----------------------------
def tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]


def cue_counts(texts: List[str]) -> Dict[str, Dict[str, int]]:
    text = " ".join(texts).lower()
    pos = {c: text.count(c) for c in POS_CUES}
    neg = {c: text.count(c) for c in NEG_CUES}
    # prune zeros for cleaner output
    pos = {k: v for k, v in pos.items() if v}
    neg = {k: v for k, v in neg.items() if v}
    return {"positive": pos, "negative": neg}


def attribute_score(filters: Filters, tags: List[str]) -> float:
    """Match user-selected attributes to destination tags."""
    want = set([*filters.geotype, *filters.culture, *filters.experience])
    if not want:
        return 0.5  # neutral if no explicit filters
    have = set(t.lower() for t in tags)
    inter = len(want & have)
    return inter / max(1, len(want))


def query_term_score(query: str, texts: List[str]) -> float:
    """Very light 'BM25/TF-IDF-ish' score = term overlap normalized."""
    q_tokens = set(tokenize(query))
    if not q_tokens:
        return 0.0
    doc_tokens = set()
    for s in texts:
        doc_tokens.update(tokenize(s))
    inter = len(q_tokens & doc_tokens)
    return inter / max(1, len(q_tokens))


def context_signal(texts: List[str]) -> float:
    """Positive cues boost; negative cues reduce. Normalize to 0..1."""
    counts = cue_counts(texts)
    pos = sum(counts["positive"].values()) if counts["positive"] else 0
    neg = sum(counts["negative"].values()) if counts["negative"] else 0
    raw = pos - 0.8 * neg
    # squash to 0..1 with tanh-like scaling
    return 0.5 + math.tanh(raw) * 0.25  # centered ~0.5


def zipf_penalty(popularity: int, strength: float, tier_bucketing: bool) -> float:
    """
    Penalty in [0,1], 0 = no penalty, 1 = severe.
    popularity is a proxy for rank/frequency (bigger => more popular).
    """
    # normalize popularity roughly (0..1) over corpus
    pops = [r["popularity"] for r in CORPUS]
    pmin, pmax = min(pops), max(pops)
    if pmax == pmin:
        base = 0.0
    else:
        base = (popularity - pmin) / (pmax - pmin)

    # Optional tier bucketing: push high pop into upper tiers
    if tier_bucketing:
        if base > 0.75:
            base = 0.95
        elif base > 0.5:
            base = 0.75
        elif base > 0.25:
            base = 0.55

    return strength * base  # scale by user control


def deterministic_trend(name: str, date_range: str) -> float:
    """
    Deterministic pseudo-trend in [-0.2, +0.2] per destination & horizon.
    Replace with real Google Trends later.
    """
    seed = f"{name}|{date_range}"
    h = hashlib.sha256(seed.encode()).hexdigest()
    val = int(h[:8], 16) / 0xFFFFFFFF  # 0..1
    return (val - 0.5) * 0.4  # -0.2..+0.2


# ----------------------------
# API
# ----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    """
    Ranking formula (simple but aligned with your write-up):

    base = w_attr * attribute_score
         + w_ctx  * context_signal
         + w_qry  * query_term_score

    Then apply penalties/filters:
      - Bloom filter: drop very popular destinations if user enabled it
      - Zipf penalty: score *= (1 - penalty)

    Confidence ~ clipped(base) for now.
    """
    # weights tuned lightly; tweak as you evaluate
    w_attr = 0.5 if req.retrieval.model == "attribute+context" else 0.2
    w_ctx  = 0.35 if req.retrieval.model == "attribute+context" else 0.2
    w_qry  = 0.15 if req.retrieval.model == "attribute+context" else 0.6  # BM25/TF-IDF lean on text

    results: List[Result] = []

    for row in CORPUS:
        # Bloom filter exclusion
        if req.retrieval.use_bloom and row["destination"] in BLOOM_SET:
            # allow through only if strong positive context present (escape hatch)
            cues = cue_counts(row["snippets"])
            pos_count = sum(cues["positive"].values()) if cues["positive"] else 0
            if pos_count < 1:
                # skip this row
                continue

        a = attribute_score(req.filters, row["tags"])
        c = context_signal(row["snippets"])
        q = query_term_score(req.query, row["snippets"])

        base = w_attr * a + w_ctx * c + w_qry * q  # 0..~1 (roughly)
        penalty = zipf_penalty(row["popularity"], req.retrieval.zipf_penalty, req.retrieval.tier_bucketing)
        score = max(0.0, base * (1.0 - penalty))

        conf = max(0.0, min(1.0, base))  # simple placeholder
        if conf < req.filters.min_confidence:
            continue

        trend = deterministic_trend(row["destination"], req.retrieval.date_range) if req.retrieval.use_trends else None
        cues = cue_counts(row["snippets"])

        results.append(
            Result(
                destination=row["destination"],
                country=row["country"],
                lat=row.get("lat"),
                lon=row.get("lon"),
                score=round(score, 4),
                confidence=round(conf, 4),
                trend_delta=round(trend, 3) if trend is not None else None,
                tags=row["tags"],
                context_cues=cues,
                snippets=row["snippets"],
                why={
                    "attribute_match": {k: 1.0 for k in set(req.filters.geotype + req.filters.culture + req.filters.experience) if k in row["tags"]},
                    "context_score": round(c, 3),
                    "term_overlap": round(q, 3),
                    "bloom_filtered": row["destination"] in BLOOM_SET and req.retrieval.use_bloom,
                    "zipf_penalty_applied": round(penalty, 3),
                },
            )
        )

    # sort by score desc and trim to k
    results.sort(key=lambda r: r.score, reverse=True)
    results = results[: max(1, req.retrieval.k)]

    # Build response
    return SearchResponse(
        query=req.query,
        params={
            "filters": req.filters.model_dump(),
            "retrieval": req.retrieval.model_dump(),
            "weights": {"attribute": w_attr, "context": w_ctx, "query": w_qry},
            "bloom_threshold": BLOOM_THRESHOLD,
        },
        results=results,
    )
