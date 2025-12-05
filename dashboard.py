import streamlit as st
import os
from virgo_utils import load_data, footer_html, load_ocr_data
from PIL import Image
from cm_config import CM_LIST


# 1. Page Config
page_icon = "🏆"
icon_path = "images/moologo2.png"
if os.path.exists(icon_path):
    page_icon = icon_path

st.set_page_config(page_title="Moomamusume Dashboard", page_icon=page_icon, layout="wide")

#  EVENT SELECTION
st.sidebar.header("📅 Event Selector")
event_names = list(CM_LIST.keys())
selected_event_name = st.sidebar.selectbox("Select Event", event_names, index=0, key="event_selector")
current_config = CM_LIST[selected_event_name]

st.markdown("""
<style>
    
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        font-size: 1.1rem;
        font-weight: bold;
        border: 1px solid #444;
        transition: all 0.2s ease-in-out;
    }
    
    div.stButton > button:hover {
        border-color: #00CC96;
        color: #00CC96;
        transform: translateY(-2px);
    }
    
    div.stButton > button[kind="primary"] {
        background-color: #FF4B4B;
        border-color: #FF4B4B;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

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
st.sidebar.warning("Adjusting filters will refresh data across all tabs other than finals.")

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

# 7. NAVIGATION
pages = [
    {"label": "Overview", "name": "Home", "icon": "🌍"},
    {"label": "Meta Tier List", "name": "Umas", "icon": "📊"},
    {"label": "Team Comps", "name": "Teams", "icon": "⚔️"},
    {"label": "Build Analysis", "name": "OCR", "icon": "🔬"},
    {"label": "Finals Results", "name": "Finals", "icon": "🏆"},
    {"label": "Library", "name": "Guides", "icon": "📚"},
]

nav_cols = st.columns(len(pages))
if 'current_page' not in st.session_state: st.session_state.current_page = "Home"

def set_page(p):
    st.session_state.current_page = p

for i, page in enumerate(pages):
    with nav_cols[i]:
        is_active = st.session_state.current_page == page["name"]
        st.button(
            f"{page['icon']} {page['label']}", 
            type="primary" if is_active else "secondary", 
            on_click=set_page, 
            args=(page["name"],), 
            width='stretch',
            key=f"nav_btn_{i}" # Unique keys are good practice
        )

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
elif st.session_state.current_page == "OCR":
    from views import ocr
    # Now handles Builds + Support Cards
    ocr.show_view(current_config)
elif st.session_state.current_page == "Finals":
    from views import finals
    finals.show_view(current_config)
elif st.session_state.current_page == "Guides":
    from views import guides
    guides.show_view(current_config)

st.markdown(footer_html, unsafe_allow_html=True)