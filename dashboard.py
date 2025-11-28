import streamlit as st
import os
from virgo_utils import  footer_html
from cm_config import CM_LIST
# dashboard.py (Update)
from data_manager import get_data # Import the new manager

# 1. Page Config
page_icon = "🏆"
icon_path = "images/moologo2.png"
if os.path.exists(icon_path):
    page_icon = icon_path

st.set_page_config(page_title="Moomamusume Dashboard", page_icon=page_icon, layout="wide")

# 2. CSS STYLING
st.markdown("""
<style>
    [data-testid="stSidebar"] {min-width: 250px;}
    div.stButton > button {
        width: 100%; border-radius: 8px; height: 3.0em; font-weight: bold;
        border: 1px solid #444; transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        border-color: #00CC96; color: #00CC96; transform: translateY(-2px);
    }
    div.stButton > button[kind="primary"] {
        background-color: #FF4B4B; border-color: #FF4B4B; color: white;
    }
</style>
""", unsafe_allow_html=True)

# 3. SIDEBAR CONTROLS
st.sidebar.header("📅 Event & Stage")
event_names = list(CM_LIST.keys())
selected_event_name = st.sidebar.selectbox("Select Event", event_names, index=0)
current_config = CM_LIST[selected_event_name]

# Stage Selector (Prelims vs Finals)
data_stage = st.sidebar.radio("Select Stage", ["Prelims (R1 & R2)", "Finals"], index=0)
mode_key = "Finals" if "Finals" in data_stage else "Prelims"

# 4. LOAD DATA (Centralized & Cached)
try:
    df, team_df, ocr_df = get_data(mode_key, current_config)
    
    if df.empty and mode_key == "Finals":
        st.warning("⚠️ No Finals data found for this event yet.")
        st.stop()
        
except Exception as e:
    st.error(f"❌ Data Loading Error: {e}")
    st.stop()

# 5. GLOBAL FILTERS
st.sidebar.header("⚙️ Filters")
if not df.empty and 'Clean_Group' in df.columns:
    groups = list(df['Clean_Group'].unique())
    selected_group = st.sidebar.multiselect("Group", groups, default=groups)
    if selected_group:
        df = df[df['Clean_Group'].isin(selected_group)]
        team_df = team_df[team_df['Clean_Group'].isin(selected_group)]

# 6. HEADER
st.title(f"{current_config['icon']} {selected_event_name} ({mode_key})")

# 7. NAVIGATION
if 'current_page' not in st.session_state: st.session_state.current_page = "Home"

def set_page(p): st.session_state.current_page = p

nav_cols = st.columns(6)
pages = ["Home", "Teams", "Umas", "Resources", "OCR", "Guides"]
icons = ["🌍", "⚔️", "🐴", "🃏", "📸", "📚"]

for col, page, icon in zip(nav_cols, pages, icons):
    with col:
        btn_type = "primary" if st.session_state.current_page == page else "secondary"
        st.button(f"{icon} {page}", type=btn_type, on_click=set_page, args=(page,))

# 8. ROUTING
# We pass the pre-loaded DataFrames to views so they don't have to load anything
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
    # Pass DataFrames directly! Efficient!
    ocr.show_view(ocr_df, df) 
elif st.session_state.current_page == "Guides":
    from views import guides
    guides.show_view(current_config)

st.markdown(footer_html, unsafe_allow_html=True)