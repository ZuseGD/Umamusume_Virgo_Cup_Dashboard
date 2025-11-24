import streamlit as st
from PIL import Image
import os

def show_view():
    st.header("ℹ️ Credits & Team")
    st.markdown("### 🚀 The Team Behind Moomamusume Dashboard")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Zuse")
        st.caption("Website Designer & Graphs Team")
        st.markdown("- **Discord:** @zusethegoose\n- **GitHub:** [ZuseGD](https://github.com/ZuseGD)")
        
    with col2:
        st.subheader("MooMooCows")
        st.caption("Project Lead, YouTuber & Community Lead")
        st.markdown("Helped promote the project and leads the community.")
        if os.path.exists("images/moologo1.png"):
            st.image("images/moologo1.png", width=150)
    
    st.markdown("---")
    st.subheader("🏆 The Team")
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
    st.subheader("☕ Support the Project")
    st.markdown("""
    <a href="https://paypal.me/paypal.me/JgamersZuse" target="_blank" style="text-decoration: none;">
        <button style="background-color:#00457C; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer;">
            Paypal Donation
        </button>
    </a>
    """, unsafe_allow_html=True)
    st.caption("*Data provided by the Moomoocows Umamusume Community. Built with Streamlit & Plotly.*")