import os
import json
from typing import Dict, Any, List

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

# Page config & global styles 
st.set_page_config(
    page_title="Off-the-Beaten-Path Travel Recommender",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
/* ---------- Base typography & layout ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
}

.main {
  /* Softer, more "product" background */
  background:
    radial-gradient(circle at top left, rgba(129,140,248,0.18) 0, transparent 45%),
    radial-gradient(circle at bottom right, rgba(45,212,191,0.18) 0, transparent 50%),
    #f3f4f6;
}

.main .block-container {
  padding-top: 0.75rem;
  padding-bottom: 4rem;
  max-width: 1180px;
}

/* Hide Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* ---------- Hero ---------- */
.app-hero {
  padding: 1.6rem 0 0.9rem 0;
}
.app-hero-inner {
  background: radial-gradient(circle at top left, #eef2ff, #ffffff);
  border-radius: 22px;
  padding: 1.2rem 1.6rem;
  border: 1px solid rgba(148,163,184,0.45);
  box-shadow: 0 18px 45px rgba(15,23,42,0.15);
  display: flex;
  align-items: center;
  gap: 1.1rem;
}
.app-hero-icon {
  font-size: 2.4rem;
  filter: drop-shadow(0 6px 18px rgba(55,65,81,0.35));
}
.app-hero-title {
  margin: 0;
  font-weight: 800;
  letter-spacing: -0.03em;
  font-size: 1.6rem;
}
.app-hero-subtitle {
  margin: 0.3rem 0 0;
  color: #6b7280;
  font-size: 0.97rem;
}
.app-hero-badges {
  margin-top: 0.55rem;
}

/* ---------- Pills, badges, micro-UI ---------- */
.pill {
  display:inline-block;
  padding:.2rem .6rem;
  border-radius:999px;
  background: linear-gradient(135deg,#6366f1,#8b5cf6);
  color:#eef2ff;
  font-size:.76rem;
  font-weight:600;
  margin-right:.35rem;
  border: 0;
}
.badge {
  display:inline-flex;
  align-items:center;
  gap: 0.25rem;
  padding:.18rem .6rem;
  border-radius:999px;
  background:#f9fafb;
  border:1px solid #e5e7eb;
  font-size:.8rem;
  color:#334155;
  font-weight:500;
  margin-right:.25rem;
}
.badge-dot {
  width:8px;
  height:8px;
  border-radius:999px;
  background: #22c55e;
}

/* ---------- Cards ---------- */
.card {
  position: relative;
  background: #ffffff;
  border-radius: 18px;
  padding: 18px 18px 14px;
  margin-bottom: 16px;
  border: 1px solid rgba(203,213,225,0.85);
  box-shadow: 0 16px 40px rgba(15,23,42,0.1);
  overflow: hidden;
  transition: box-shadow 0.15s ease, transform 0.12s ease, border-color 0.15s ease;
}
.card::before {
  /* subtle colored accent bar */
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 18px;
  border-left: 4px solid #6366f1;
  opacity: 0.88;
  pointer-events: none;
}
.card:hover {
  box-shadow: 0 22px 60px rgba(15,23,42,0.18);
  transform: translateY(-1.5px);
  border-color: rgba(129,140,248,0.9);
}
.card .title {
  font-size: 1.05rem;
  font-weight: 800;
  margin: 0;
}
.card .subtitle {
  color:#6b7280;
  margin:.2rem 0 .45rem;
  font-size: 0.9rem;
}
.card-meta {
  font-size: 0.82rem;
  color: #6b7280;
  margin-bottom: 0.35rem;
}

/* ---------- Score chips & metrics ---------- */
.scorechip {
  background: #f9fafb;
  border:1px solid #e5e7eb;
  padding:.3rem .7rem;
  border-radius:999px;
  font-weight:600;
  font-size: 0.83rem;
}
.scorechip .label {
  color:#64748b;
  font-weight:600;
  margin-right:.25rem;
}

.metric-card {
  background: linear-gradient(135deg,#eef2ff,#f9fafb);
  border-radius: 16px;
  padding: 0.75rem 0.9rem;
  border: 1px solid rgba(199,210,254,0.9);
  box-shadow: 0 12px 32px rgba(129,140,248,0.25);
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab"] {
  font-weight:600;
  padding-bottom: 0.35rem;
}
.stTabs [aria-selected="true"] {
  color:#111827 !important;
  border-bottom: 2px solid #6366f1;
}

/* ---------- Buttons ---------- */
.stButton > button {
  border-radius: 999px;
  padding: .55rem 1rem;
  font-weight:700;
  background: linear-gradient(135deg,#6366f1,#8b5cf6);
  border:0;
  color: #ffffff;
  box-shadow: 0 12px 30px rgba(79,70,229,0.45);
}
.stButton > button:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
  background: #0f172a;
  color: #e5e7eb;
  border-right: 1px solid #1f2937;
}
section[data-testid="stSidebar"] .sidebar-content {
  padding-top: 0.5rem;
}
.sidebar-section-label {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: .09em;
  color: #9ca3af;
  font-weight: 600;
  margin: 0.3rem 0 0.1rem;
}

/* Adjust labels inside sidebar */
section[data-testid="stSidebar"] label {
  color: #e5e7eb !important;
}

/* ---------- Map legend ---------- */
.map-legend {
  display:flex;
  align-items:center;
  gap:10px;
  margin-top:10px;
  font-size: 0.85rem;
  color:#4b5563;
}
.map-legend-swatch {
  width:20px;
  height:20px;
  border-radius:999px;
}

/* Small helper text */
.helper-text {
  font-size: 0.8rem;
  color:#6b7280;
}
</style>
""",
    unsafe_allow_html=True,
)


# Backend config 
API_URL = os.getenv("API_URL", "http://localhost:8081")


def _api_search(payload: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(f"{API_URL}/search", json=payload, timeout=25)
    r.raise_for_status()
    return r.json()


# Sidebar 
st.sidebar.markdown('<div class="sidebar-section-label">Query</div>', unsafe_allow_html=True)
q = st.sidebar.text_area(
    "Describe what you want in a travel destination:",
    placeholder="e.g., small coastal towns in Spain with artisan markets",
    height=80,
)

c1, c2 = st.sidebar.columns(2)
with c1:
    k = st.number_input("Results", 3, 50, 12, 1)
with c2:
    min_conf = st.slider("Min confidence", 0.0, 1.0, 0.0, 0.05)

st.sidebar.markdown('<div class="sidebar-section-label">Attributes</div>', unsafe_allow_html=True)
geo = st.sidebar.multiselect(
    "Geographic type",
    ["coastal", "mountain", "island", "urban", "desert", "forest", "river", "lake"],
)
cult = st.sidebar.multiselect(
    "Cultural focus",
    ["food", "art", "history", "music", "markets", "festivals", "crafts"],
)
exp = st.sidebar.multiselect(
    "Experience tags",
    ["quiet", "nightlife", "adventure", "local", "hiking", "kayak", "wildlife", "scenic", "photography"],
)
# Location filter
st.sidebar.markdown('<div class="sidebar-section-label">Location</div>', unsafe_allow_html=True)
loc_col1, loc_col2 = st.sidebar.columns([2, 1])
with loc_col1:
    location_name = st.text_input(
        "Location name",
        placeholder="e.g., Jakarta, Belize, Coron",
    )
with loc_col2:
    location_match = st.selectbox(
        "Match",
        ["contains", "exact"],
        index=0,
        help="Use 'contains' for partial matches, 'exact' for precise name.",
    )


with st.sidebar.expander("Model & bias controls", expanded=True):
    model = st.selectbox(
        "Retrieval model",
        ["attribute+context (recommended)", "BM25", "TF-IDF"],
        index=0,
    )
    use_bloom = st.checkbox("Exclude high-frequency locations (Bloom filter)", True)
    zipf = st.slider("Zipf penalty (popularity dampening)", 0.0, 1.0, 0.35, 0.05)
    tier = st.checkbox("Frequency tier bucketing", True)

with st.sidebar.expander("Signals & time window", expanded=False):
    use_trends = st.checkbox("Use Google Trends", False)
    horizon = st.selectbox("Time horizon", ["all", "1y", "90d", "30d"], index=1)

run = st.sidebar.button("🔎 Run search", use_container_width=True)


# Hero 
st.markdown(
    """
<div class="app-hero">
  <div class="app-hero-inner">
    <div class="app-hero-icon">🌍</div>
    <div>
      <h1 class="app-hero-title">Off-the-Beaten-Path Travel Recommender</h1>
      <p class="app-hero-subtitle">
        Context-aware, attribute-first suggestions with popularity-bias correction.
      </p>
      <div class="app-hero-badges">
        <span class="badge">Blog & guidebook corpus</span>
        <span class="badge">Attribute matching</span>
        <span class="badge">Popularity dampening</span>
      </div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Helpers 
def payload() -> Dict[str, Any]:
    m = (
        "attribute+context"
        if model.startswith("attribute")
        else ("bm25" if model.lower().startswith("bm25") else "tfidf")
    )
    return {
        "query": q.strip(),
        "filters": {
            "geotype": geo,
            "culture": cult,
            "experience": exp,
            "min_confidence": float(min_conf),
        },
        "retrieval": {
            "model": m,
            "use_bloom": bool(use_bloom),
            "zipf_penalty": float(zipf),
            "tier_bucketing": bool(tier),
            "use_trends": bool(use_trends),
            "date_range": horizon,
            "k": int(k),
        },
    }


def score_chip(label: str, value: str) -> str:
    return f'<span class="scorechip"><span class="label">{label}</span>{value}</span>'


def render_result_card(r: Dict[str, Any], i: int):
    left, right = st.columns([6, 3])

    geotype = ", ".join(r.get("geotype", []) if isinstance(r.get("geotype"), list) else [r.get("geotype")] if r.get("geotype") else [])
    culture = ", ".join(r.get("culture", []) if isinstance(r.get("culture"), list) else [r.get("culture")] if r.get("culture") else [])

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<p class="title">{i}. {r["destination"]}</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="subtitle">{r.get("country","")}</p>',
            unsafe_allow_html=True,
        )

        meta_pieces = []
        if geotype:
            meta_pieces.append(f"🧭 {geotype}")
        if culture:
            meta_pieces.append(f"🎭 {culture}")
        if meta_pieces:
            st.markdown(
                f"<div class='card-meta'>{' · '.join(meta_pieces)}</div>",
                unsafe_allow_html=True,
            )

        # Tag pills
        tags = r.get("tags", [])
        if tags:
            st.markdown(
                " ".join([f'<span class="pill">{t}</span>' for t in tags]),
                unsafe_allow_html=True,
            )

        # Snippets
        for s in r.get("snippets", [])[:2]:
            st.markdown(
                f"<div style='margin-top:.6rem;color:#111827;font-size:0.93rem;'>{s}</div>",
                unsafe_allow_html=True,
            )

        # Context cues
        cues = r.get("context_cues", {})
        pos = ", ".join(
            [f"{k} ×{v}" for k, v in (cues.get("positive") or {}).items()]
        )
        neg = ", ".join(
            [f"{k} ×{v}" for k, v in (cues.get("negative") or {}).items()]
        )
        if pos or neg:
            st.markdown("<hr style='margin:.9rem 0 .5rem;'>", unsafe_allow_html=True)
            if pos:
                st.markdown(f"**Context cues (positive):** {pos}")
            if neg:
                st.markdown(f"**Context cues (negative):** {neg}")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        chips = [
            score_chip("Score", f"{r.get('score',0):.2f}"),
            score_chip("Confidence", f"{r.get('confidence',0):.2f}"),
            score_chip(
                "Trend",
                "📈"
                if (r.get("trend_delta") or 0) > 0.1
                else ("📉" if (r.get("trend_delta") or 0) < -0.1 else "➖"),
            ),
        ]
        st.markdown(" ".join(chips), unsafe_allow_html=True)
        st.caption("Why this destination surfaced")
        with st.expander("See full scoring breakdown", expanded=False):
            st.json(r.get("why", {}))
        st.markdown("</div>", unsafe_allow_html=True)


# Run search 
if "results" not in st.session_state:
    st.session_state["results"] = None

if run and q.strip():
    with st.spinner("Searching blogs and ranking destinations…"):
        try:
            st.session_state["results"] = _api_search(payload())
        except Exception as e:
            st.error(f"API call failed: {e}")
            st.session_state["results"] = None

results = st.session_state["results"]

tabs = st.tabs(["About", "Results", "Maps", "Diagnostics"])
# About tab 
with tabs[0]:
    st.subheader("About this prototype")
    st.markdown(
        """
This interface explores **context-aware travel discovery**:

- Combines blog & guidebook text with structured attributes (geotype, culture, experience).  
- Uses **retrieval models** (attribute+context, BM25, TF-IDF) to surface candidate places.  
- Applies **popularity dampening** (Bloom filter + Zipf-style penalty) to surface hidden gems.  

---

### **Team – Group 1**
- **Morgan Dreiss**  
- **Nadav Gerner**  
- **David Corcoran**  
- **Adam Stein**  
- **Walter Hall**

_DSAN 6700: Off-the-Beaten-Path Travel Recommender Project_

---
"""
    )
# Results tab 
with tabs[1]:
    if not results:
        st.info("Run a search from the sidebar to see recommendations.")
    else:
        res_list = results.get("results", [])
        if res_list:
            scores = [r.get("score", 0) for r in res_list]
            confs = [r.get("confidence", 0) for r in res_list]

            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Destinations returned", len(res_list))
                st.markdown("</div>", unsafe_allow_html=True)
            with m2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Average score", f"{sum(scores)/len(scores):.2f}")
                st.markdown("</div>", unsafe_allow_html=True)
            with m3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Average confidence", f"{sum(confs)/len(confs):.2f}")
                st.markdown("</div>", unsafe_allow_html=True)

            st.caption(
                f"Showing top {len(res_list)} results for: “{results.get('query','')}”"
            )
            for i, r in enumerate(res_list, start=1):
                render_result_card(r, i)
        else:
            st.info("No results were returned. Try relaxing your filters or lowering the minimum confidence.")


# Map tab 
with tabs[2]:
    if not results:
        st.info("Run a search first to populate the map.")
    else:
        df = pd.DataFrame(
            [
                {
                    "destination": r["destination"],
                    "country": r.get("country", ""),
                    "lat": r.get("lat"),
                    "lon": r.get("lon"),
                    "score": r.get("score"),
                    "confidence": r.get("confidence"),
                }
                for r in results.get("results", [])
                if r.get("lat") is not None and r.get("lon") is not None
            ]
        )

        if df.empty:
            st.info("No coordinates available to plot.")
        else:
            min_score = df["score"].min()
            max_score = df["score"].max()
            score_range = max_score - min_score if max_score != min_score else 1

            def relative_score_to_color(score):
                relative = (score - min_score) / score_range
                r = int(255 * (1 - relative))
                g = int(255 * relative)
                b = 0
                a = 160
                return [r, g, b, a]

            df["color"] = df["score"].apply(relative_score_to_color)

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[lon, lat]",
                get_radius=25000,
                pickable=True,
                radius_scale=1,
                radius_min_pixels=3,
                radius_max_pixels=30,
                get_fill_color="color",
            )

            vs = pdk.ViewState(
                latitude=float(df.lat.mean()),
                longitude=float(df.lon.mean()),
                zoom=2.5,
            )

            st.pydeck_chart(
                pdk.Deck(
                    layers=[layer],
                    initial_view_state=vs,
                    tooltip={
                        "text": "{destination}\n{country}\nscore: {score}\nconf: {confidence}"
                    },
                )
            )

            st.markdown(
                """
            <div class="map-legend">
                <div class="map-legend-swatch" style="background-color:rgb(255,0,0);"></div> Lower score
                <div class="map-legend-swatch" style="background-color:rgb(255,165,0);"></div> Medium score
                <div class="map-legend-swatch" style="background-color:rgb(0,255,0);"></div> Higher score
            </div>
            """,
                unsafe_allow_html=True,
            )

# Diagnostics tab 
with tabs[3]:
    if not results:
        st.info("Run a search first to view diagnostics.")
    else:
        st.subheader("Resolved parameters")
        st.json(results.get("params", {}))



    if API_URL:
        st.caption(f"Connected to API at `{API_URL}`")
