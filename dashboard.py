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

# 2. CSS to Hide Sidebar & Add Navbar
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stRadio"]) {
        position: sticky; top: 0; z-index: 999; background: #0E1117; padding-bottom: 10px; border-bottom: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# 3. Load Data
try:
    df, team_df = load_data()
except:
    st.error("Database Connection Failed")
    st.stop()

# 4. TOP NAVIGATION
st.markdown("## 🏆 Virgo Cup Analytics")
# Using radio button horizontally as a navbar
page = st.radio(
    "Navigation", 
    ["🌍 Home", "⚔️ Teams", "🐴 Umas", "🃏 Resources", "ℹ️ Credits"], 
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")

# 5. ROUTING
if page == "🌍 Home":
    from views import home
    home.show_view(df, team_df)

elif page == "⚔️ Teams":
    from views import teams
    teams.show_view(df, team_df)

elif page == "🐴 Umas":
    from views import umas
    umas.show_view(df, team_df)

elif page == "🃏 Resources":
    from views import resources
    resources.show_view(df, team_df)

elif page == "ℹ️ Credits":
    from views import credits
    credits.show_view()

# 6. FOOTER
st.markdown(footer_html, unsafe_allow_html=True)