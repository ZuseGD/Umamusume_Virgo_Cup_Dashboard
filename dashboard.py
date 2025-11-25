import streamlit as st
from utils import load_data, footer_html, DESCRIPTIONS, load_ocr_data
from PIL import Image
from cm_config import CM_LIST
import os

# 1. Page Config
page_icon = "🏆"
if os.path.exists("images/moologo2.png"):
    page_icon = Image.open("images/moologo2.png")

st.set_page_config(page_title="UM Dashboard", page_icon=page_icon, layout="wide", initial_sidebar_state="collapsed")

# 2. CSS

# 2. Hide Sidebar CSS
st.markdown("""
<style>
    [data-testid="collapsedControl"] {display: none;}
    div.stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: bold;
        border: 1px solid #444;
    }
    div.stButton > button:hover {
        border-color: #00CC96;
        color: #00CC96;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.header("📅 Event Selector")
event_names = list(CM_LIST.keys())
selected_event_name = st.sidebar.selectbox("Select Event", event_names, index=0)
current_config = CM_LIST[selected_event_name]
st.sidebar.markdown("---")



# 3. Load Data
try:
    df, team_df = load_data(current_config['sheet_url'])
except:
    st.error("Failed to load data for this event.")
    st.stop()

# FILTERS
st.sidebar.header("⚙️ Global Filters")
groups = list(df['Clean_Group'].unique())
selected_group = st.sidebar.multiselect("CM Group", groups, default=groups)

rounds = sorted(list(df['Round'].unique()))
selected_round = st.sidebar.multiselect("Round", rounds, default=rounds)

days = sorted(list(df['Day'].unique()))
selected_day = st.sidebar.multiselect("Day", days, default=days)

ocr_df = load_ocr_data()

# Group Filter
groups = list(df['Clean_Group'].unique())
selected_group = st.sidebar.multiselect("CM Group", groups, default=groups)

# Round/Day Filter
rounds = sorted(list(df['Round'].unique()))
days = sorted(list(df['Day'].unique()))
selected_round = st.sidebar.multiselect("Round", rounds, default=rounds)
selected_day = st.sidebar.multiselect("Day", days, default=days)

# APPLY FILTERS
if selected_group:
    df = df[df['Clean_Group'].isin(selected_group)]
    team_df = team_df[team_df['Clean_Group'].isin(selected_group)]
if selected_round:
    df = df[df['Round'].isin(selected_round)]
    team_df = team_df[team_df['Round'].isin(selected_round)]
if selected_day:
    df = df[df['Day'].isin(selected_day)]
    team_df = team_df[team_df['Day'].isin(selected_day)]

#  HEADER
st.title(f"{current_config['icon']} {selected_event_name} Dashboard")

# NAVIGATION
nav_cols = st.columns(6)
if 'current_page' not in st.session_state: st.session_state.current_page = "Home"
def set_page(p): st.session_state.current_page = p

with nav_cols[0]: 
    if st.button("🌍 Home"): set_page("Home")
with nav_cols[1]: 
    if st.button("⚔️ Teams"): set_page("Teams")
with nav_cols[2]: 
    if st.button("🐴 Umas"): set_page("Umas")
with nav_cols[3]: 
    if st.button("🃏 Resources"): set_page("Resources")
with nav_cols[4]: 
    if st.button("📸 OCR"): set_page("OCR")
with nav_cols[5]: 
    if st.button("📚 Guides"): set_page("Guides")

st.markdown("---")

# --- GLOBAL FILTERS (Visible on every page) ---
        # We use an expander so it is accessible but doesn't clutter the view
with st.expander("⚙️ Global Filters (Round, Day, Group)", expanded=False):
    f1, f2, f3 = st.columns(3)
        
        # 1. Group Filter
    with f1:
        # Get unique groups, sorted
        groups = sorted(list(df['Clean_Group'].unique()))
        selected_group = st.multiselect("Filter Group", groups, default=groups)
            
    # 2. Round Filter
    with f2:
        # Get unique rounds (e.g., Round 1, Round 2)
        rounds = sorted(list(df['Round'].unique()))
        selected_round = st.multiselect("Filter Round", rounds, default=rounds)
            
    # 3. Day Filter
    with f3:
        # Get unique days (e.g., Day 1, Day 2)
        days = sorted(list(df['Day'].unique()))
        selected_day = st.multiselect("Filter Day", days, default=days)

    # --- APPLY FILTERS TO DATA ---
    # This updates BOTH the individual data (df) and team data (team_df)
    # passing the filtered versions to your views.

    if selected_group:
        df = df[df['Clean_Group'].isin(selected_group)]
        team_df = team_df[team_df['Clean_Group'].isin(selected_group)]

    if selected_round:
        df = df[df['Round'].isin(selected_round)]
        team_df = team_df[team_df['Round'].isin(selected_round)]

    if selected_day:
        df = df[df['Day'].isin(selected_day)]
        team_df = team_df[team_df['Day'].isin(selected_day)]
    with st.expander("⚠️ Data Disclaimer (Survivorship Bias)"):
        st.markdown(DESCRIPTIONS["bias"])

# 7. ROUTING
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
elif st.session_state.current_page == "OCR":
    from views import ocr
    # Pass specific parquet file if needed, or update load_ocr_data to take arg
    from utils import load_ocr_data
    ocr_df = load_ocr_data(current_config['parquet_file'])
    ocr.show_view(ocr_df)
elif st.session_state.current_page == "Guides":
    from views import guides
    guides.show_view()
elif st.session_state.current_page == "Credits": # Hidden from top nav but reachable
    from views import credits
    credits.show_view()

st.markdown(footer_html, unsafe_allow_html=True)