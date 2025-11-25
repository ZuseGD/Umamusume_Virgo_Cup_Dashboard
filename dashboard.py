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

# --- 🆕 ADD THIS SECTION HERE ---
st.sidebar.header("📝 Data Submission")
form_url = current_config.get('form_url')
status_msg = current_config.get('status_msg', "Forms are currently unavailable.")

if form_url:
    st.sidebar.link_button(
        "✍️ Fill Out Survey", 
        form_url, 
        type="primary", 
        use_container_width=True
    )
else:
    st.sidebar.info(f"🚫 {status_msg}")
# -------------------------------

st.sidebar.markdown("---")

#  LOAD DATA
try:
    # Check for local file existence if not a URL
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


st.sidebar.markdown("---")

#  FILTERS
st.sidebar.header("⚙️ Global Filters")

# Apply Filters (With Unique Keys to prevent DuplicateID Error)
if 'Clean_Group' in df.columns:
    groups = list(df['Clean_Group'].unique())
    # ADDED key="filter_group"
    selected_group = st.sidebar.multiselect("CM Group", groups, default=groups, key="filter_group") 
    if selected_group:
        df = df[df['Clean_Group'].isin(selected_group)]
        team_df = team_df[team_df['Clean_Group'].isin(selected_group)]

if 'Round' in df.columns:
    rounds = sorted(list(df['Round'].unique()))
    # ADDED key="filter_round"
    selected_round = st.sidebar.multiselect("Round", rounds, default=rounds, key="filter_round")
    if selected_round:
        df = df[df['Round'].isin(selected_round)]
        team_df = team_df[team_df['Round'].isin(selected_round)]

if 'Day' in df.columns:
    days = sorted(list(df['Day'].unique()))
    # ADDED key="filter_day"
    selected_day = st.sidebar.multiselect("Day", days, default=days, key="filter_day")
    if selected_day:
        df = df[df['Day'].isin(selected_day)]
        team_df = team_df[team_df['Day'].isin(selected_day)]

# 6. HEADER
st.title(f"{current_config['icon']} {selected_event_name} Dashboard")

# 7. NAVIGATION
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

# 8. ROUTING
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
    ocr.show_view(current_config)
elif st.session_state.current_page == "Guides":
    from views import guides
    guides.show_view(current_config)
elif st.session_state.current_page == "Credits":
    from views import credits
    credits.show_view()

st.markdown(footer_html, unsafe_allow_html=True)