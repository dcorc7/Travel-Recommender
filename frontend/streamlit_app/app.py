import os
from typing import Dict, Any
import logging
import sys
import uuid

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "frontend", "message": "%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("frontend")

BASE_DIR = os.path.dirname(__file__)

def apply_custom_css(filename: str = "style.css") -> None:
    """Load a CSS file from disk and inject it into the Streamlit app."""
    css_path = os.path.join(BASE_DIR, filename)
    with open(css_path) as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Page config 
st.set_page_config(
    page_title="Off-the-Beaten-Path Travel Recommender",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load styles from style.css
apply_custom_css()

# Backend config 
API_URL = os.getenv("API_URL", "http://localhost:8081")


def _api_search(payload: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    headers = {"X-Request-ID": request_id}
    r = requests.post(f"{API_URL}/search", json=payload, headers=headers, timeout=25)
    r.raise_for_status()
    return r.json()


# Sidebar 
st.sidebar.markdown('<div class="sidebar-section-label">Query</div>', unsafe_allow_html=True)

q1 = st.sidebar.text_area(
   "Describe what you want in a travel destination:",
   placeholder="e.g., small coastal towns in Spain with artisan markets",
   height=80,
)

q2 = st.sidebar.text_area(
   "What sort of activities are you interested in?",
   placeholder ="e.g. seeing a local performance, attending an interesting museum, tasting unique foods, ect.",
   height=80,
)

q3 = st.sidebar.text_area(
   "Descirbe the geographic type desired:",
   placeholder ="e.g. coastal, mountain , urban, ect.",
   height=80,
)


# combine text query fields into one
q = f"{q1}. {q2}. {q3}"

c1, c2 = st.sidebar.columns(2)
with c1:
    k = st.number_input("Results", 3, 50, 12, 1)
with c2:
    min_conf = st.slider("Min confidence", 0.0, 1.0, 0.0, 0.05)

run = st.sidebar.button("🔎 Run search", use_container_width=True)

model = st.sidebar.selectbox(
    "Retrieval model",
    ["BM25", "FAISS"],
    index=0,
)

    # use_bloom = st.checkbox("Exclude high-frequency locations (Bloom filter)", True)
    # zipf = st.slider("Zipf penalty (popularity dampening)", 0.0, 1.0, 0.35, 0.05)
    # tier = st.checkbox("Frequency tier bucketing", True)

# with st.sidebar.expander("Signals & time window", expanded=False):
#     use_trends = st.checkbox("Use Google Trends", False)
#     horizon = st.selectbox("Time horizon", ["all", "1y", "90d", "30d"], index=1)


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
        else ("bm25" if model.lower().startswith("bm25") else "faiss")
    )
    return {
        "query": q.strip(),
        "filters": {
            "min_confidence": float(min_conf),
        },
        "retrieval": {
            "model": m,
            "k": int(k),
        },
    }


def score_chip(label: str, value: str) -> str:
    return f'<span class="scorechip"><span class="label">{label}</span>{value}</span>'


def render_result_card(r: Dict[str, Any], i: int):
    left, right = st.columns([6, 3])

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<p class="title">{i}. {r["destination"]}</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="subtitle">{r.get("country","")}</p>',
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
        ]
        st.markdown(" ".join(chips), unsafe_allow_html=True)
        # st.caption("Why this destination surfaced")
        with st.expander("See full scoring breakdown", expanded=False):
            st.json(r.get("why", {}))
        st.markdown("</div>", unsafe_allow_html=True)


# Run search 
if "response" not in st.session_state:
    st.session_state["response"] = None

if run and q.strip():
    request_id = str(uuid.uuid4())
    logger.info(f"User search initiated: query='{q}', request_id='{request_id}', filters={{'k': {k}, 'min_conf': {min_conf}, 'model': '{model}'}}")
    
    with st.spinner("Searching blogs and ranking destinations…"):
        try:
            st.session_state["response"] = _api_search(payload(), request_id)

            # Logging Success
            res_count = len(st.session_state["response"].get("results", []))
            logger.info(f"Search completed successfully: returned {res_count} results")
        except Exception as e:
            logger.error(f"API call failed: {e}")
            st.error(f"API call failed: {e}")
            st.session_state["response"] = None

response = st.session_state["response"]
# print(response.keys)

# parse the response
if response:
    results = response.get("results") if isinstance(response, dict) else response.results
    explanations = response.get("explanations") if isinstance(response, dict) else response.explanations
else:
    results = []
    explanations = []

tabs = st.tabs(["About", "Results", "Maps", "Explanations", "Diagnostics"])
# About tab 
with tabs[0]:
    st.subheader("About this prototype")
    st.markdown(
        """
This interface explores **context-aware travel discovery**:

Uses **retrieval models** (BM25 or FAISS) to surface candidate places.  

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
    if API_URL:
        st.caption(f"Connected to API at `{API_URL}`")


# Results tab 
with tabs[1]:
    if not results:
        st.info("Run a search from the sidebar to see recommendations.")
    else:
        res_list = results
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
                f"Showing top {len(res_list)} results for: “{response.get('query','')}”"
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
                for r in response.get("results", [])
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

# Explanations tab
with tabs[3]:
    if not explanations:
        st.info("Run a search first to view result explanations.")
    else:
        st.markdown("Explanations for the top 3 destinations:")

        # for i in range(0,len(df)):
        for i in range(0,3):
            st.markdown(f"Destination: {df['destination'][i]}")
            st.markdown(f" Explanation: {explanations[i]}")

# Diagnostics tab 
with tabs[4]:
    if not results:
        st.info("Run a search first to view diagnostics.")




