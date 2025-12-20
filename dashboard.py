import streamlit as st
import os
import pandas as pd
from virgo_utils import load_data, footer_html, load_ocr_data
from PIL import Image
from cm_config import CM_LIST
from views.timeline import render_timeline_tab

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

# 3. LOAD DATA (Robust Mode)
data_loaded = False
df = pd.DataFrame()
team_df = pd.DataFrame()

try:
    sheet_url = current_config.get('sheet_url', '')
    
    # Check if URL or local file exists
    file_exists = True
    if not sheet_url.startswith("http"):
        if not os.path.exists(sheet_url):
            file_exists = False
    
    if file_exists and sheet_url:
        df, team_df = load_data(sheet_url)
        if not df.empty:
            data_loaded = True
            
except Exception as e:
    print(f"Data load skipped or failed: {e}")
    # We do not stop execution here; we simply proceed with data_loaded = False

# 4. FILTERS (Only show if data exists)
if data_loaded:
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
else:
    # Optional: Sidebar message when no data
    st.sidebar.info("🚫 No data available for this event yet.")

# 5. HEADER
st.title(f"{current_config.get('icon', '🏆')} {selected_event_name} Dashboard")

# 6. NAVIGATION
if 'current_page' not in st.session_state: 
    st.session_state.current_page = "Home"

# Define available pages based on data status
if data_loaded:
    pages = [
        {"label": "Overview", "name": "Home", "icon": "🌍"},
        {"label": "Umas", "name": "Umas", "icon": "📊"},
        {"label": "Team Comps", "name": "Teams", "icon": "⚔️"},
        {"label": "Card Usage", "name": "Cards", "icon": "🗃️"},
        {"label": "Analysis", "name": "Analysis", "icon": "🏆"},
        {"label": "Timeline", "name": "Timeline", "icon": "📍"},
        {"label": "Guides", "name": "Guides", "icon": "📚"},
    ]
else:
    # LIMITED NAVIGATION: Only Home, Timeline, Guides
    pages = [
        {"label": "Overview", "name": "Home", "icon": "🌍"},
        {"label": "Timeline", "name": "Timeline", "icon": "📍"},
        {"label": "Guides", "name": "Guides", "icon": "📚"},
    ]

# Safety Check: If user was on a page that no longer exists (e.g. switched event), reset to Home
valid_page_names = [p['name'] for p in pages]
if st.session_state.current_page not in valid_page_names:
    st.session_state.current_page = "Home"

# Render Navigation Buttons
nav_cols = st.columns(len(pages))
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
            key=f"nav_btn_{i}"
        )

# 7. ROUTING & CONTENT
if st.session_state.current_page == "Home":
    if data_loaded:
        from views import home
        home.show_view(df, team_df, current_config)
    else:
        # --- LANDING PAGE FOR NO DATA ---
        st.markdown("---")
        st.header("👋 Welcome to the Dashboard!")
        st.warning("**Note:** Data for this event is not yet available.")
        
        st.info(f"⚠️ **Data collection for {selected_event_name} has not started or is currently processing.**")
        st.markdown("""
            ### 🔍 What can I do now?
            While we wait for the data to roll in, you can still access our strategy guides!
            
            1. Click the **Guides** tab above.
            2. View detailed course analysis and recommendations.
            3. Check back later once the event goes live!
            """)
            
        # If you have a submission link in your config, you can show it here
        if 'form_url' in current_config:
            st.markdown(f"**Got data?** [Submit your results here!]({current_config['form_url']})")

        

elif st.session_state.current_page == "Guides":
    from views import guides
    guides.show_view(current_config)
elif st.session_state.current_page == "Timeline":
    render_timeline_tab()

# Only allow loading these views if data is actually loaded
elif data_loaded:
    if st.session_state.current_page == "Teams":
        from views import teams
        teams.show_view(df, team_df)
    elif st.session_state.current_page == "Umas":
        from views import umas
        umas.show_view(df, team_df)
    elif st.session_state.current_page == "Cards":
        from views import cards
        cards.show_view(team_df)
    elif st.session_state.current_page == "Analysis":
        from views import analysis
        analysis.show_view(current_config)

st.markdown(footer_html, unsafe_allow_html=True)