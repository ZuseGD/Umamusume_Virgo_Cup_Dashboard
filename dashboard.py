import streamlit as st
from utils import load_data, footer_html, DESCRIPTIONS, load_ocr_data
from PIL import Image
from cm_config import CM_LIST
import os

# 1. Page Config
page_icon = "🏆"
if os.path.exists("images/moologo2.png"):
    page_icon = Image.open("images/moologo2.png")

st.set_page_config(page_title="UM Dashboard", page_icon=page_icon, layout="wide")

#  EVENT SELECTION
st.sidebar.header("📅 Event Selector")
event_names = list(CM_LIST.keys())
selected_event_name = st.sidebar.selectbox("Select Event", event_names, index=0, key="event_selector")
current_config = CM_LIST[selected_event_name]



st.markdown("""
<style>
    [data-testid="stSidebar"] {min-width: 250px;}
    
    /* Navigation Buttons Styling */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;       /* Softer corners */
        height: 3.5em;            /* Taller buttons */
        font-size: 1.1rem;        /* Bigger text */
        font-weight: bold;
        border: 1px solid #444;
        transition: all 0.2s ease-in-out;
    }
    
    /* Hover Effect */
    div.stButton > button:hover {
        border-color: #00CC96;
        color: #00CC96;
        transform: translateY(-2px); /* Slight lift effect */
    }
    
    /* Primary Button (Active Tab) Specifics */
    div.stButton > button[kind="primary"] {
        background-color: #FF4B4B; /* Or your theme color */
        border-color: #FF4B4B;
        color: white;
    }
</style>
""", unsafe_allow_html=True)
# -------------------------------

# 4. LOAD DATA
try:
    if not current_config['sheet_url'].startswith("http"):
        if not os.path.exists(current_config['sheet_url']):
            st.error(f"❌ File not found: **{current_config['sheet_url']}**")
            st.info("Please ensure the CSV file is in the same folder as `dashboard.py`.")
            st.stop()

    df, team_df = load_data(current_config['sheet_url'])
    
    if df.empty:
        st.error("⚠️ Data loaded but is empty. Check CSV format.")
        st.stop()
        
except Exception as e:
    st.error(f"❌ Critical Data Error: {e}")
    st.stop()

# 5. FILTERS
st.sidebar.header("⚙️ Global Filters")

if 'Clean_Group' in df.columns:
    groups = list(df['Clean_Group'].unique())
    selected_group = st.sidebar.multiselect("CM Group", groups, default=groups, key="filter_group") 
    if selected_group:
        df = df[df['Clean_Group'].isin(selected_group)]
        team_df = team_df[team_df['Clean_Group'].isin(selected_group)]

if 'Round' in df.columns:
    rounds = sorted(list(df['Round'].unique()))
    selected_round = st.sidebar.multiselect("Round", rounds, default=rounds, key="filter_round")
    if selected_round:
        df = df[df['Round'].isin(selected_round)]
        team_df = team_df[team_df['Round'].isin(selected_round)]

if 'Day' in df.columns:
    days = sorted(list(df['Day'].unique()))
    selected_day = st.sidebar.multiselect("Day", days, default=days, key="filter_day")
    if selected_day:
        df = df[df['Day'].isin(selected_day)]
        team_df = team_df[team_df['Day'].isin(selected_day)]

# 6. HEADER
st.title(f"{current_config['icon']} {selected_event_name} Dashboard")

# 7. NAVIGATION (Updated with Highlight Logic)
nav_cols = st.columns(6)
if 'current_page' not in st.session_state: st.session_state.current_page = "Home"

def set_page(p):
    st.session_state.current_page = p

def nav_btn(col, label, page_name):
    with col:
        # Determine style: Primary (Red/Filled) if active, Secondary (Ghost) if not
        btn_type = "primary" if st.session_state.current_page == page_name else "secondary"
        
        # Use on_click to update state BEFORE the re-run, ensuring instant highlight
        st.button(
            label, 
            type=btn_type, 
            on_click=set_page, 
            args=(page_name,), 
            use_container_width=True
        )

# Render Buttons
nav_btn(nav_cols[0], "🌍 Home", "Home")
nav_btn(nav_cols[1], "⚔️ Teams", "Teams")
nav_btn(nav_cols[2], "🐴 Umas", "Umas")
nav_btn(nav_cols[3], "🃏 Resources", "Resources")
nav_btn(nav_cols[4], "📸 OCR", "OCR")
nav_btn(nav_cols[5], "📚 Guides", "Guides")

st.markdown("---")

# 8. ROUTING
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
    from utils import load_ocr_data
    pq_file = current_config.get('parquet_file', '')
    ocr_df = load_ocr_data(pq_file)
    ocr.show_view(ocr_df)
elif st.session_state.current_page == "Guides":
    from views import guides
    guides.show_view(current_config)
elif st.session_state.current_page == "Credits":
    from views import credits
    credits.show_view()

st.markdown(footer_html, unsafe_allow_html=True)