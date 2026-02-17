import os
from typing import Dict, Any
import logging
import sys
import uuid

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

import plotly.express as px
import plotly.graph_objects as go

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
    page_title="Off-the-Beaten-Path Travel Recommendation Application",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load styles from style.css
apply_custom_css()

# Backend config
API_URL = os.getenv("API_URL", "https://dcorcoran-travel-recommender-api.hf.space")


def _api_search(payload: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    headers = {"X-Request-ID": request_id}
    r = requests.post(f"{API_URL}/search", json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()


# Sidebar 
st.sidebar.markdown('<div class="sidebar-section-label">User Query</div>', unsafe_allow_html=True)

q1 = st.sidebar.text_area(
   "Describe generally what you want in a travel destination:",
   placeholder="e.g., Small and coastal Mediterranean towns with artisan markets",
   height=80,
)

q2 = st.sidebar.text_area(
   "Describe what activities you are interested in",
   placeholder ="e.g. Seeing local performances, attending museums, tasting unique foods, ect.",
   height=80,
)

q3 = st.sidebar.text_area(
   "Describe the desired geography of your destination:",
   placeholder ="e.g. coastal, mountain , urban, forest, ect.",
   height=80,
)


# combine text query fields into one
q = f"{q1}. {q2}. {q3}"

c1, c2 = st.sidebar.columns(2)
with c1:
    k = st.number_input("Number of Results", 3, 50, 12, 1)

run = st.sidebar.button("🔎 Search Destinations", use_container_width=True)

model = st.sidebar.selectbox(
    "Retrieval model",
    ["BM25", "FAISS"],
    index=0,
)


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
        chips = []
        score = r.get("score")
        if isinstance(score, (int, float)) and score > 0:
            chips.append(score_chip("Score", f"{score:.2f}"))
        distance = r.get("distance")
        if isinstance(distance, (int, float)) and distance > 0:
            chips.append(score_chip("Distance", f"{distance:.2f}"))

        st.markdown(" ".join(chips), unsafe_allow_html=True)
        st.link_button("Go to Blog Post", r.get("why", {}).get("page_url", ""))
        with st.expander("See full scoring breakdown", expanded=False):
            st.json(r.get("why", {}))
        st.markdown("</div>", unsafe_allow_html=True)


# Run search 
if "response" not in st.session_state:
    st.session_state["response"] = None

if run and q.strip():
    request_id = str(uuid.uuid4())
    logger.info(f"User search initiated: query='{q}', request_id='{request_id}', retrieval={{'k': {k}, 'model': '{model}'}}")
    
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

tabs = st.tabs(["Results", "Maps", "Explanations", "Database Stats", "About"])



# Results tab 
with tabs[0]:
    if not results:
        st.info("Run a search query from the sidebar to see recommendations.")
    else:
        res_list = results
        if res_list:
            scores = [r.get("score", 0) for r in res_list]
            distances = [r.get("distance", 0) for r in res_list]
            
            scores = [s for s in scores if s not in (None, "")]
            distances = [d for d in distances if d not in (None, "")]

            m1, m2 = st.columns(2)
            with m1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Destinations Returned", len(res_list))
                st.markdown("</div>", unsafe_allow_html=True)
            with m2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                if scores:
                    st.metric("Average Score", f"{sum(scores)/len(scores):.2f}")
                    st.markdown("</div>", unsafe_allow_html=True)
                if sum(distances) > 0:
                    st.metric("Average Distance", f"{sum(distances)/len(distances):.4f}")
                    st.markdown("</div>", unsafe_allow_html=True)
                # else:
                #     st.markdown("</div>", unsafe_allow_html=True)

            st.caption(
                f"Showing top {len(res_list)} results for: “{response.get('query','')}”"
            )
            for i, r in enumerate(res_list, start=1):
                render_result_card(r, i)
        else:
            st.info("No results were returned.")


# Map tab 
with tabs[1]:
    if not results:
        st.info("Run a search first to populate the map.")
    else:
        if r.get("score") is not None:
            SCORE_TRUE = True
        else:
            SCORE_TRUE = False

        df = pd.DataFrame(
            [
                {
                    "destination": r["destination"],
                    "country": r.get("country", ""),
                    "lat": r.get("lat"),
                    "lon": r.get("lon"),
                    # "score": r.get("score"),
                    "score": r.get("score") if r.get("score") is not None else r.get("distance"),
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

            def relative_score_to_color(score, reverse=False):
                relative = (score - min_score) / score_range
                # if distances, flip color
                if reverse:
                    relative = 1 - relative 
                r = int(255 * (1 - relative))
                g = int(255 * relative)
                b = 0
                a = 160
                return [r, g, b, a]

            if SCORE_TRUE:
                df["color"] = df["score"].apply(relative_score_to_color, reverse = False)
            else:
                df["color"] = df["score"].apply(relative_score_to_color, reverse = True)

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

            if SCORE_TRUE == True:
                st.pydeck_chart(
                    pdk.Deck(
                        layers=[layer],
                        initial_view_state=vs,
                        tooltip={
                            "text": "{destination}\n{country}\nScore: {score}\n"
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
            else:
                st.pydeck_chart(
                    pdk.Deck(
                        layers=[layer],
                        initial_view_state=vs,
                        tooltip={
                            "text": "{destination}\n{country}\nDistance: {score}\n"
                        },
                    )
                )
                st.markdown(
                """
            <div class="map-legend">
                <div class="map-legend-swatch" style="background-color:rgb(0,255,0);"></div> Lower distance
                <div class="map-legend-swatch" style="background-color:rgb(255,165,0);"></div> Medium distance
                <div class="map-legend-swatch" style="background-color:rgb(255,0,0);"></div> Higher distance
            </div>
            """,
                unsafe_allow_html=True,
            )


# Explanations tab
with tabs[2]:
    if not explanations:
        st.info("Run a search first to view result explanations.")
    else:
        st.markdown("Explanations for the top 3 destinations:")

        # for i in range(0,len(df)):
        for i in range(0,3):
            st.markdown(f"Destination: {df['destination'][i]}")
            st.markdown(f" Explanation: {explanations[i]}")

# Database Stats tab 
with tabs[3]:  # Database Stats tab
    st.subheader("📊 Database Statistics")
    
    try:
        # Fetch database stats from API
        db_stats = requests.get(f"{API_URL}/stats", timeout=10).json()
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Posts", db_stats.get("total_posts", "N/A"))
        with col2:
            st.metric("Unique Locations", db_stats.get("unique_locations", "N/A"))
        with col3:
            st.metric("Unique Blogs", db_stats.get("unique_blogs", "N/A"))
        with col4:
            st.metric("Unique Authors", db_stats.get("unique_authors", "N/A"))
        
        
        # Geographic Distribution using pydeck
        st.subheader("Geographic Distribution")
        geo_data = pd.DataFrame(db_stats.get("coordinates", []))
        
        if geo_data.empty:
            st.info("No coordinates available to plot.")
        else:
            # Data already grouped by location from backend
            
            # Create color based on post count with fixed thresholds
            def count_to_color(count):
                if count <= 20:
                    # Red (1-20 posts)
                    return [255, 0, 0, 160]
                elif count <= 40:
                    # Yellow (21-40 posts)
                    return [255, 255, 0, 160]
                else:
                    # Green (41+ posts)
                    return [0, 255, 0, 160]
            
            geo_data["color"] = geo_data["count"].apply(count_to_color)
            
            # Create pydeck layer
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=geo_data,
                get_position="[lon, lat]",
                get_radius=25000,
                pickable=True,
                radius_scale=1,
                radius_min_pixels=3,
                radius_max_pixels=30,
                get_fill_color="color",
            )
            
            # Set view to center of all points
            vs = pdk.ViewState(
                latitude=float(geo_data['lat'].mean()),
                longitude=float(geo_data['lon'].mean()),
                zoom=1.5,
            )
            
            # Render map with location names in tooltip
            st.pydeck_chart(
                pdk.Deck(
                    layers=[layer],
                    initial_view_state=vs,
                    tooltip={
                        "text": "{location}\nPosts: {count}"
                    },
                )
            )
            
            # Legend
            st.markdown(
                """
                <div class="map-legend">
                    <div class="map-legend-swatch" style="background-color:rgb(255,0,0);"></div> 1-20 posts
                    <div class="map-legend-swatch" style="background-color:rgb(255,255,0);"></div> 21-40 posts
                    <div class="map-legend-swatch" style="background-color:rgb(0,255,0);"></div> 41+ posts
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Show stats about the map
            st.caption(f"Showing {len(geo_data)} unique destinations")
            
    except Exception as e:
        st.error(f"Could not load database statistics: {e}")
        st.info("Add a /stats endpoint to your API to enable this feature")

# About tab 
with tabs[4]:
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




