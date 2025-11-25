import streamlit as st
from utils import style_fig, PLOT_CONFIG, calculate_score, show_description

def show_view():
    st.warning("⚠️ **NOTE:** This guide is WIP IGNORE EVERYTHING BELOW")
    st.header("📚 Libra Cup Preparation Guide")
    
    # --- 1. COURSE INFO ---
    with st.expander("📍 Track Details & Passive Skills", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            # Replace with your actual track image path
            # st.image("images/track_diagram.png", caption="Kyoto 3000m") 
            st.info("🖼️ (Add Track Image Here)")
        
        with c2:
            st.markdown("""
            ### **Kyoto 3000m (Long)**
            - **Surface:** Turf / Right / In
            - **Season:** Autumn 🍂
            - **Weather:** Sunny ☀️ / Good 🟢
            - **Course Constants:**
                - **Uphill:** No significant uphill
                - **Downhill:** Late downhill section
            """)
            
            st.markdown("#### ✅ Recommended Passives")
            st.markdown("""
            - **Right Turn** (右回り)
            - **Autumn Girl** (秋ウマ娘)
            - **Kyoto Racecourse** (京都レース場)
            - **Non-Heavy Track** (良バ場)
            """)

    # --- 2. STAT TARGETS ---
    st.subheader("📊 Stat Targets")
    tab1, tab2 = st.tabs(["🏆 Grade League (Uncapped)", "🔰 Open League (B+)"])
    
    with tab1:
        st.markdown("Targets for a competitive **UE / UD** rank build:")
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Speed", "1600+")
        s2.metric("Stamina", "1200+", "1 Gold Recov")
        s3.metric("Power", "1200+")
        s4.metric("Guts", "1000+")
        s5.metric("Wisdom", "1000+")
        st.warning("⚠️ **Stamina Note:** 3000m is very long. Ensure you have at least 1 Gold Recovery skill + 1200 Stamina.")

    with tab2:
        st.markdown("Targets for **B+ (Rank 8199)** cap:")
        st.markdown("- **Speed:** 1200 (Hard Cap)")
        st.markdown("- **Stamina:** Manage carefully to hit distance but stay under rank.")
        
    st.markdown("---")

    # --- 3. EXTERNAL RESOURCES ---
    st.subheader("🔗 Useful Resources")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("📖 GameTora Guide", "https://gametora.com/umamusume")
    with c2:
        st.link_button("📺 MooMooCows (YouTube)", "https://www.youtube.com/@MooMooCows")
    with c3:
        st.link_button("🐦 ULC Discord", "https://discord.gg/umamusume")