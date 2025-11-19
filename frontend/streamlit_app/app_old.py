import streamlit as st
import requests
import pandas as pd
import random
from PIL import Image
import io
import json
from datetime import datetime
import time
import os

# Set the page configuration (must be the first Streamlit command)
st.set_page_config(
    page_title="Anything's Pawsible - Dog Dating", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="🐕"
)

# Add custom CSS for dog dating theme
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #ff6b6b, #ff8e53);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .dog-card {
        border-radius: 15px;
        padding: 20px;
        background: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
    }
    .swipe-button {
        border-radius: 50px;
        padding: 15px 30px;
        font-size: 1.2rem;
        font-weight: bold;
        border: none;
        margin: 10px;
    }
    .like-button {
        background: linear-gradient(45deg, #ff6b6b, #ff8e53);
        color: white;
    }
    .pass-button {
        background: linear-gradient(45deg, #74b9ff, #0984e3);
        color: white;
    }
    .compatibility-score {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Add title and description
st.markdown('<h1 class="main-header">🐕 Anything\'s Pawsible 🐾</h1>', unsafe_allow_html=True)
st.markdown(
    """
    <p style="font-size: 18px; color: gray; text-align: center;">
        ML-powered dog dating app - helping dogs find their perfect playmates!
    </p>
    """,
    unsafe_allow_html=True,
)

# Initialize session state for navigation
if "page" not in st.session_state:
    st.session_state.page = "home"
if "current_dog" not in st.session_state:
    st.session_state.current_dog = None
if "matches" not in st.session_state:
    st.session_state.matches = []

# Navigation
nav_col1, nav_col2, nav_col3 = st.columns(3)
with nav_col1:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = "home"
with nav_col2:
    if st.button("🐕 Create Profile", use_container_width=True):
        st.session_state.page = "create_profile"
with nav_col3:
    if st.button("💕 Find Matches", use_container_width=True):
        st.session_state.page = "swipe"

st.markdown("---")

# Page routing
if st.session_state.page == "home":
    st.markdown("## Welcome to Anything's Pawsible! 🎾")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 🐾 For Your Dog
        - Create an awesome profile with photos
        - Show off personality and preferences
        - Find compatible playmates nearby
        """)
        
    with col2:
        st.markdown("""
        ### 🤖 ML-Powered Matching
        - Advanced compatibility algorithms
        - Smart filtering and recommendations
        - Real-time compatibility scoring
        """)
    
    st.info("👆 Use the navigation buttons above to get started!")

elif st.session_state.page == "create_profile":
    st.markdown("## 🐕 Create Your Dog's Profile")
    
    with st.form("dog_profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Basic Information")
            dog_name = st.text_input("Dog's Name", placeholder="e.g., Buddy")
            dog_breed = st.selectbox("Breed", [
                "Golden Retriever", "Labrador Retriever", "German Shepherd",
                "Bulldog", "Poodle", "Beagle", "Rottweiler", "Yorkshire Terrier",
                "Dachshund", "Siberian Husky", "Mixed Breed", "Other"
            ])
            dog_age = st.slider("Age (years)", 0, 20, 3)
            dog_size = st.selectbox("Size", ["Small", "Medium", "Large", "Extra Large"])
            dog_gender = st.selectbox("Gender", ["Male", "Female"])
            
        with col2:
            st.markdown("### Personality & Preferences")
            energy_level = st.slider("Energy Level", 1, 10, 5, help="1=Couch Potato, 10=Hyperactive")
            friendliness = st.slider("Friendliness", 1, 10, 8, help="1=Shy, 10=Social Butterfly")
            playfulness = st.slider("Playfulness", 1, 10, 7, help="1=Calm, 10=Always Playing")
            
            preferred_activities = st.multiselect("Favorite Activities", [
                "Fetch", "Swimming", "Hiking", "Running", "Tug of War", 
                "Frisbee", "Agility", "Walks", "Dog Parks", "Beach Days"
            ])
            
            location = st.text_input("Location", placeholder="e.g., San Francisco, CA")
            
        st.markdown("### About Your Dog")
        description = st.text_area(
            "Tell us about your dog's personality!", 
            placeholder="My dog loves long walks on the beach and playing fetch...",
            height=100
        )
        
        # Photo upload (placeholder for now)
        st.markdown("### Photos")
        uploaded_files = st.file_uploader(
            "Upload photos of your dog", 
            accept_multiple_files=True, 
            type=['png', 'jpg', 'jpeg']
        )
        
        submitted = st.form_submit_button("Create Profile", use_container_width=True)
        
        if submitted and dog_name:
            # Create profile data
            profile_data = {
                "name": dog_name,
                "breed": dog_breed,
                "age": dog_age,
                "size": dog_size,
                "gender": dog_gender,
                "energy_level": energy_level,
                "friendliness": friendliness,
                "playfulness": playfulness,
                "activities": preferred_activities,
                "location": location,
                "description": description,
                "photos": len(uploaded_files) if uploaded_files else 0
            }
            
            # Store in session state (in real app would save to database)
            st.session_state.current_dog = profile_data
            st.success(f"🎉 Profile created for {dog_name}!")
            st.balloons()

elif st.session_state.page == "swipe":
    st.markdown("## 💕 Find Your Dog's Perfect Match")
    
    if not st.session_state.current_dog:
        st.warning("Please create your dog's profile first!")
        if st.button("Create Profile Now"):
            st.session_state.page = "create_profile"
            st.rerun()
    else:
        # Mock dog profiles for demonstration
        mock_dogs = [
            {
                "name": "Luna", "breed": "Border Collie", "age": 4, "size": "Medium",
                "energy_level": 9, "friendliness": 8, "playfulness": 9,
                "location": "San Francisco, CA", "description": "Love frisbee and hiking!"
            },
            {
                "name": "Max", "breed": "Golden Retriever", "age": 2, "size": "Large", 
                "energy_level": 7, "friendliness": 10, "playfulness": 8,
                "location": "Oakland, CA", "description": "Friendly giant who loves everyone!"
            },
            {
                "name": "Bella", "breed": "French Bulldog", "age": 3, "size": "Small",
                "energy_level": 4, "friendliness": 7, "playfulness": 6,
                "location": "Berkeley, CA", "description": "Chill pup who enjoys short walks."
            }
        ]
        
        if "swipe_index" not in st.session_state:
            st.session_state.swipe_index = 0
            
        if st.session_state.swipe_index < len(mock_dogs):
            current_match = mock_dogs[st.session_state.swipe_index]
            
            # Display current dog profile
            st.markdown('<div class="dog-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image("https://via.placeholder.com/300x300/FF6B6B/FFFFFF?text=🐕", 
                        caption=f"{current_match['name']}", width=250)
                        
            with col2:
                st.markdown(f"# {current_match['name']}, {current_match['age']}")
                st.markdown(f"**Breed:** {current_match['breed']}")
                st.markdown(f"**Size:** {current_match['size']}")
                st.markdown(f"**Location:** {current_match['location']}")
                
                # Compatibility score (mock calculation)
                compatibility = min(95, max(60, 
                    85 + (current_match['energy_level'] - st.session_state.current_dog['energy_level']) * -2))
                    
                st.markdown(f'<div class="compatibility-score" style="color: #ff6b6b;">💖 {compatibility}% Match</div>', 
                           unsafe_allow_html=True)
                
                st.markdown(f"**About:** {current_match['description']}")
                
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Swipe buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("👎 Pass", use_container_width=True, key="pass"):
                    st.session_state.swipe_index += 1
                    st.rerun()
                    
            with col3:
                if st.button("❤️ Like", use_container_width=True, key="like"):
                    st.session_state.matches.append(current_match)
                    st.session_state.swipe_index += 1
                    st.success(f"You liked {current_match['name']}! 🎉")
                    time.sleep(1)
                    st.rerun()
                    
        else:
            st.markdown("## 🎉 No more profiles to show!")
            st.markdown(f"**Your matches:** {len(st.session_state.matches)}")
            if st.session_state.matches:
                for match in st.session_state.matches:
                    st.success(f"💕 {match['name']} - {match['breed']}")
                    
            if st.button("Start Over"):
                st.session_state.swipe_index = 0
                st.session_state.matches = []
                st.rerun()

# Additional features section
st.markdown("---")
st.markdown("## 🛠️ Advanced Features")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    ### 🔍 Smart Filtering
    - Bloom filters prevent repeated profiles
    - Weekly refresh for new experiences
    - Optimized browsing
    """)
    
with col2:
    st.markdown("""
    ### 🧠 ML-Powered Matching
    - FAISS similarity search
    - Real-time compatibility scoring
    - Behavioral pattern analysis  
    """)
    
with col3:
    st.markdown("""
    ### 🔄 Duplicate Detection
    - LSH for spam prevention
    - Profile authenticity checks
    - Quality assurance
    """)

# Fetch version, hostname, and IP address
version = os.getenv("APP_VERSION", "1.0.0")
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

# Add footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div style="text-align: center; color: gray; margin-top: 20px;">
        <p><strong>🐕 Anything's Pawsible - ML-Powered Dog Dating</strong></p>
        <p>Created by <a href="mailto:tva7@georgetown.edu">Trevor Adriaanse</a></p>
        <p><strong>Version:</strong> {version}</p>
        <p><strong>Hostname:</strong> {hostname}</p>
        <p><strong>IP Address:</strong> {ip_address}</p>
        <p style="font-size: 12px; margin-top: 10px;">
            Built with MLOps best practices: FastAPI • Streamlit • FAISS • Bloom Filters • LSH
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
