import streamlit as st
import os
import pandas as pd
import numpy as np
from virgo_utils import load_data, footer_html
from cm_config import CM_LIST

# Page Config
page_icon = "🏆"
if os.path.exists("images/moologo2.png"):
    page_icon = "images/moologo2.png"
st.set_page_config(page_title="UM Dashboard", page_icon=page_icon, layout="wide")

# CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] {min-width: 250px;}
    div.stButton > button {width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; border: 1px solid #444; transition: all 0.2s;}
    div.stButton > button:hover {border-color: #00CC96; color: #00CC96; transform: translateY(-2px);}
    div.stButton > button[kind="primary"] {background-color: #FF4B4B; border-color: #FF4B4B; color: white;}
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("📅 Event Selector")
event_names = list(CM_LIST.keys())
selected_event_name = st.sidebar.selectbox("Select Event", event_names, index=0)
current_config = CM_LIST[selected_event_name]

# Navigation State
if 'current_page' not in st.session_state: st.session_state.current_page = "Home"
def set_page(p): st.session_state.current_page = p

# Nav Buttons
nav_cols = st.columns(7) # Added 7th column for Finals
pages = ["Home", "Teams", "Umas", "Resources", "OCR", "🏆 Finals", "Guides"] # Added Finals
for col, p in zip(nav_cols, pages):
    with col:
        btn_type = "primary" if st.session_state.current_page == p else "secondary"
        # Strip emoji for logic check if needed, but here simple string match is fine
        st.button(p, type=btn_type, on_click=set_page, args=(p,))

# Data Loading (ONLY Standard Data here)
# We do NOT load finals data here to avoid breaking the main dashboard
try:
    df, team_df = load_data(current_config['sheet_url'])
except:
    df, team_df = pd.DataFrame(), pd.DataFrame()

# Global Filters (Only for Standard Views)
if st.session_state.current_page not in ["🏆 Finals", "Guides", "Credits"]:
    st.sidebar.header("⚙️ Filters")
    if 'Clean_Group' in df.columns:
        groups = list(df['Clean_Group'].unique())
        sel = st.sidebar.multiselect("Group", groups, default=groups)
        if sel: df = df[df['Clean_Group'].isin(sel)]

# Routing
if st.session_state.current_page == "Home":
    from views import home
    home.show_view(df, team_df, current_config)
elif st.session_state.current_page == "Teams":
    from views import teams
    teams.show_view(df, team_df)
elif st.session_state.current_page == "Umas":
    from views import umas
    umas.show_view(df, team_df)
elif st.session_state.current_page == "Resources":
    from views import resources
    resources.show_view(df, team_df)
elif st.session_state.current_page == "OCR":
    from views import ocr
    ocr.show_view(current_config)
elif st.session_state.current_page == "🏆 Finals":
    # NEW ROUTE
    from views import finals
    finals.show_view(current_config)
elif st.session_state.current_page == "Guides":
    from views import guides
    guides.show_view(current_config)
elif st.session_state.current_page == "Credits":
    from views import credits
    credits.show_view()

st.markdown(footer_html, unsafe_allow_html=True)