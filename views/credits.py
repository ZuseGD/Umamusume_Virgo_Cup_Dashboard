import streamlit as st
from PIL import Image
import os

def show_view():
    st.header("ℹ️ Credits & Team")
    st.markdown("### 🚀 The Team Behind Virgo Cup Analytics")
    
    st.markdown("---")
    
    # --- PROJECT LEADS ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Zuse")
        st.caption("Website Designer & Graphs Team")
        # Display Zuse's Logo
        if os.path.exists("image.png"):
            st.image("image.png", width=150)
        st.markdown("""
        - **Discord:** @zusethegoose
        - **GitHub:** [ZuseGD](https://github.com/ZuseGD)
        """)
        
    with col2:
        st.subheader("MooMooCows")
        st.caption("Project Lead, YouTuber & Community Lead")
        # Display MooMooCows Logo 1
        if os.path.exists("moologo1.jpg"):
            st.image("moologo1.jpg", width=150)
        st.markdown("Helped promote the project and leads the community.")
    
    st.markdown("---")
    
    # --- TEAM ROSTER ---
    st.subheader("🏆 The Team")
    
    # Using 2 columns for the team lists so it looks good on mobile
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 📝 Forms Team")
        st.markdown("- Ryan4Numbers\n- Karhumies\n- Ramen\n- Zuse")
        
        st.markdown("#### 📊 Public Sheets Team")
        st.markdown("- Cien\n- Ramen\n- Ryan4Numbers")
        
        st.markdown("#### 📉 Graphs Team")
        st.markdown("- Zuse\n- Jus\n- Clister")

    with c2:
        st.markdown("#### 🎨 Posters & Visuals")
        st.markdown("- Ramen\n- Ricetea\n- Mad0990")
        
        st.markdown("#### 🖼️ Canva Slides")
        st.markdown("- Ramen")

        st.markdown("#### 🔍 OCR & Testing")
        st.markdown("- Vali")

    st.markdown("---")
    
    # --- SUPPORT ---
    st.subheader("☕ Support the Project")
    st.markdown("""
    If you found this dashboard helpful, consider supporting the server costs and development!
    
    <a href="https://paypal.me/paypal.me/JgamersZuse" target="_blank" style="text-decoration: none;">
        <button style="background-color:#00457C; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer;">
            Paypal Donation
        </button>
    </a>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("*Data provided by the Umamusume Community. Built with Streamlit & Plotly.*")