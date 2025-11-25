import streamlit as st
import plotly.express as px
from PIL import Image
import requests
from io import BytesIO
import os

def show_view(current_config):
    # 1. Header
    cm_id = current_config.get('id', 'Champion Meeting')
    event_name = cm_id.replace('_', ' ').title()
    st.header(f"📚 Guides: {event_name}")
    
    # 2. Load Images
    images = current_config.get('guide_images', [])
    
    if not images:
        st.info("ℹ️ No guide images found for this event.")
    else:
        # 3. Display Interactive Images
        for img_path in images:
            render_interactive_image(img_path)

    st.markdown("---")

    # CREDITS SECTION
    st.subheader("🙏 Credits")
    st.markdown("""
    A huge thank you to the team behind these resources:
    - **Strategy & Guide:** [MooMooCows](https://www.youtube.com/@MooMooCows)
    - **Graphics & Visuals:** MooMooCows' Canva Helpers
    """)
    
    # External Resources (Static Footer)
    st.subheader("🔗 Useful Resources")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("📖 GameTora Wiki", "https://gametora.com/umamusume")
    with c2:
        st.link_button("📺 MooMooCows", "https://www.youtube.com/@MooMooCows")
    with c3:
        st.link_button("🐦 MooMooCows Discord", "https://discord.gg/SY2aWGu53S")


def render_interactive_image(path):
    """
    Loads an image and displays it using Plotly to enable
    Pan (Drag) and Zoom (Scroll) capabilities.
    """
    image = path
    
    # A. Load Image Data (Local or Web)
    if image:
        st.markdown(f"### 🖼️ {os.path.basename(path)}")
        
        # --- 1. ADD DIRECT LINK (Best for readability) ---
        if path.startswith("http"):
            st.link_button("🔍 Open Full Resolution Image (New Tab)", path)
        
        st.caption("🔍 **Controls:** Scroll to Zoom • Drag to Pan • Double-Click to Reset")

        # --- 2. CREATE HIGH-QUALITY FIGURE ---
        # binary_format="png" prevents JPEG artifacts on text
        # binary_compression_level=0 ensures maximum quality
        fig = px.imshow(
            image, 
            binary_string=True, 
            binary_format="png", 
            binary_compression_level=0
    )
        
        # C. Configure Layout
        fig.update_layout(
            xaxis={'showticklabels': False, 'visible': False},
            yaxis={'showticklabels': False, 'visible': False},
            margin=dict(l=0, r=0, t=0, b=0),
            dragmode='pan',
            height=800, 
            hovermode=False
        )
        
        # D. Render
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})