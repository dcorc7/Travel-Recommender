import os
import json
from typing import Dict, Any, List

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

# ---------------- Page config & global styles ----------------
st.set_page_config(
    page_title="Off-the-Beaten-Path Travel Recommender",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
/* Typography & container */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
.main .block-container { padding-top: 1rem; padding-bottom: 4rem; max-width: 1200px; }

/* Hide Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Hero */
.app-hero {
  text-align:center; padding: 1.25rem 0 0.25rem 0;
}
.app-hero h1 {
  margin: 0; font-weight: 800; letter-spacing: -0.02em;
}
.app-hero p {
  color: #6b7280; margin: .25rem 0 0 0;
}

/* Pills & chips */
.pill {
  display:inline-block; padding: .2rem .6rem; border-radius: 999px;
  background: #eef2ff; color:#3730a3; font-size:.8rem; font-weight:600; margin-right:.35rem;
  border: 1px solid #e0e7ff;
}
.badge {
  display:inline-block; padding:.15rem .5rem; border-radius:8px; background:#f8fafc; border:1px solid #e5e7eb;
  font-size:.8rem; color:#334155; font-weight:600; margin-right:.25rem;
}

/* Card */
.card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 18px 18px 14px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.05); margin-bottom: 14px;
}
.card .title { font-size: 1.05rem; font-weight: 800; margin: 0; }
.card .subtitle { color:#64748b; margin:.15rem 0 .5rem; }

/* Score chips */
.scorechip { background:#f1f5f9; border:1px solid #e2e8f0; padding:.25rem .55rem; border-radius:10px; font-weight:700; }
.scorechip .label { color:#64748b; font-weight:600; margin-right:.25rem; }

/* Tabs underline accent */
.stTabs [data-baseweb="tab"] { font-weight:600; }
.stTabs [aria-selected="true"] { color:#111827 !important; }

/* CTA button */
.stButton > button {
  border-radius: 10px; padding: .6rem 1rem; font-weight:700;
  background: linear-gradient(135deg,#6366f1,#8b5cf6); border:0;
}
.stButton > button:hover { filter: brightness(1.02); transform: translateY(-1px); }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Backend config ----------------
API_URL = os.getenv("API_URL", "http://localhost:8081")

def _api_search(payload: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(f"{API_URL}/search", json=payload, timeout=25)
    r.raise_for_status()
    return r.json()

# ---------------- Sidebar ----------------
st.sidebar.header("Query & Filters")
q = st.sidebar.text_area(
    "Describe what you want:",
    placeholder="e.g., small coastal towns in Spain with artisan markets",
    height=80,
)
c1, c2 = st.sidebar.columns(2)
with c1: k = st.number_input("Results", 3, 50, 12, 1)
with c2: min_conf = st.slider("Min confidence", 0.0, 1.0, 0.0, 0.05)

st.sidebar.subheader("Attributes")
geo = st.sidebar.multiselect("Geographic type", ["coastal","mountain","island","urban","desert","forest","river","lake"])
cult = st.sidebar.multiselect("Cultural focus", ["food","art","history","music","markets","festivals","crafts"])
exp  = st.sidebar.multiselect("Experience tags", ["quiet","nightlife","adventure","local","hiking","kayak","wildlife","scenic","photography"])

st.sidebar.subheader("Model & Bias Controls")
model = st.sidebar.selectbox("Retrieval model", ["attribute+context (recommended)","BM25","TF-IDF"], index=0)
use_bloom = st.sidebar.checkbox("Exclude high-frequency locations (Bloom filter)", True)
zipf = st.sidebar.slider("Zipf penalty (popularity dampening)", 0.0, 1.0, 0.35, 0.05)
tier = st.sidebar.checkbox("Frequency tier bucketing", True)
use_trends = st.sidebar.checkbox("Use Google Trends", False)
horizon = st.sidebar.selectbox("Time horizon", ["all","1y","90d","30d"], index=1)

run = st.sidebar.button("🔎 Run search", use_container_width=True)

# ---------------- Hero ----------------
st.markdown(
    """
<div class="app-hero">
  <h1>🌍 Off-the-Beaten-Path Travel Recommender</h1>
  <p>Context-aware, attribute-driven suggestions with popularity-bias correction.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------- Helpers ----------------
def payload() -> Dict[str, Any]:
    m = "attribute+context" if model.startswith("attribute") else ("bm25" if model.lower().startswith("bm25") else "tfidf")
    return {
        "query": q.strip(),
        "filters": {"geotype": geo, "culture": cult, "experience": exp, "min_confidence": float(min_conf)},
        "retrieval": {
            "model": m, "use_bloom": bool(use_bloom), "zipf_penalty": float(zipf),
            "tier_bucketing": bool(tier), "use_trends": bool(use_trends),
            "date_range": horizon, "k": int(k)
        }
    }

def score_chip(label: str, value: str) -> str:
    return f'<span class="scorechip"><span class="label">{label}</span>{value}</span>'

def render_result_card(r: Dict[str, Any], i: int):
    left, right = st.columns([6, 3])
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<p class="title">{i}. {r["destination"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="subtitle">{r.get("country","")}</p>', unsafe_allow_html=True)

        # Tag pills
        tags = r.get("tags", [])
        if tags:
            st.markdown(" ".join([f'<span class="pill">{t}</span>' for t in tags]), unsafe_allow_html=True)

        # Snippets
        for s in r.get("snippets", [])[:2]:
            st.markdown(f"<div style='margin-top:.5rem;color:#334155;'>{s}</div>", unsafe_allow_html=True)

        # Context cues
        cues = r.get("context_cues", {})
        pos = ", ".join([f"{k} ×{v}" for k,v in (cues.get('positive') or {}).items()])
        neg = ", ".join([f"{k} ×{v}" for k,v in (cues.get('negative') or {}).items()])
        if pos or neg:
            st.markdown("<hr style='margin:.8rem 0;'>", unsafe_allow_html=True)
            if pos: st.markdown(f"**Context cues (positive):** {pos}")
            if neg: st.markdown(f"**Context cues (negative):** {neg}")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        chips = [
            score_chip("Score", f"{r.get('score',0):.2f}"),
            score_chip("Confidence", f"{r.get('confidence',0):.2f}"),
            score_chip("Trend", "📈" if (r.get('trend_delta') or 0) > 0.1 else ("📉" if (r.get('trend_delta') or 0) < -0.1 else "➖")),
        ]
        st.markdown(" ".join(chips), unsafe_allow_html=True)
        st.caption("Why this was recommended")
        st.json(r.get("why", {}))
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Run search ----------------
if "results" not in st.session_state: st.session_state["results"] = None

if run and q.strip():
    with st.spinner("Searching blogs and ranking destinations…"):
        try:
            st.session_state["results"] = _api_search(payload())
        except Exception as e:
            st.error(f"API call failed: {e}")
            st.session_state["results"] = None

results = st.session_state["results"]

tabs = st.tabs(["Results", "Map", "Diagnostics", "About"])

with tabs[0]:
    if not results:
        st.info("Run a search from the sidebar to see recommendations.")
    else:
        st.caption(f"Showing top {len(results.get('results', []))} for: “{results.get('query','')}”")
        for i, r in enumerate(results.get("results", []), start=1):
            render_result_card(r, i)

with tabs[1]:
    if not results:
        st.info("Run a search first to populate the map.")
    else:
        df = pd.DataFrame([
            {"destination": r["destination"], "country": r.get("country",""), "lat": r.get("lat"), "lon": r.get("lon"),
             "score": r.get("score"), "confidence": r.get("confidence")}
            for r in results.get("results", [])
            if r.get("lat") is not None and r.get("lon") is not None
        ])
        if df.empty:
            st.info("No coordinates available to plot.")
        else:
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position='[lon, lat]',
                get_radius=60000,
                pickable=True,
                radius_scale=1,
                radius_min_pixels=3,
                radius_max_pixels=30,
            )
            vs = pdk.ViewState(latitude=float(df.lat.mean()), longitude=float(df.lon.mean()), zoom=2.5)
            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=vs,
                                     tooltip={"text": "{destination}\n{country}\nscore: {score}\nconf: {confidence}"}))

with tabs[2]:
    if not results:
        st.info("Run a search first to view diagnostics.")
    else:
        st.write("**Resolved parameters**")
        st.json(results.get("params", {}))

with tabs[3]:
    st.write(
        "This prototype uses context cues (e.g., *hidden gem*, *locals only*), \
attribute matching (geotype/culture/experience), and popularity dampening \
(Bloom filter + Zipf-style penalty). Toggle controls in the sidebar and explore the map."
    )
    if API_URL:
        st.caption(f"API_URL: {API_URL}")
