import streamlit as st
from utils import load_data, footer_html
from PIL import Image
import os

# 1. Page Config (Must be first)
page_icon = "🏆"
if os.path.exists("images/moologo2.png"):
    page_icon = Image.open("images/moologo2.png")

st.set_page_config(
    page_title="Virgo Cup CM5", 
    page_icon=page_icon, 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. CSS to Hide Sidebar & Style Buttons
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
    /* Make navigation buttons look like tabs */
    div.stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 3. Load Data Globally
try:
    df, team_df = load_data()
except:
    st.error("Database Connection Failed")
    st.stop()

# 4. TOP NAVIGATION BAR
st.markdown("## 🏆 Virgo Cup Analytics")
nav_cols = st.columns([1, 1, 1, 1, 1])

# State Management for Page Switching
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

def set_page(page_name):
    st.session_state.current_page = page_name

# Navigation Buttons
with nav_cols[0]:
    if st.button("🌍 Home", use_container_width=True): set_page("Home")
with nav_cols[1]:
    if st.button("⚔️ Teams", use_container_width=True): set_page("Teams")
with nav_cols[2]:
    if st.button("🐴 Umas", use_container_width=True): set_page("Umas")
with nav_cols[3]:
    if st.button("🃏 Resources", use_container_width=True): set_page("Resources")
with nav_cols[4]:
    if st.button("ℹ️ Credits", use_container_width=True): set_page("Credits")

st.markdown("---")

# 5. ROUTING LOGIC
if st.session_state.current_page == "Home":
    from views import home
    home.show_view(df, team_df)

elif st.session_state.current_page == "Teams":
    from views import teams
    teams.show_view(df, team_df)

elif st.session_state.current_page == "Umas":
    from views import umas
    umas.show_view(df, team_df)

elif st.session_state.current_page == "Resources":
    from views import resources
    resources.show_view(df, team_df)

elif st.session_state.current_page == "Credits":
    from views import credits
    credits.show_view()

# 6. FOOTER
st.markdown(footer_html, unsafe_allow_html=True)