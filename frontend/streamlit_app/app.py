import os
import json
from typing import Dict, Any, List

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

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
