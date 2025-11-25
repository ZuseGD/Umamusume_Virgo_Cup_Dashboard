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
    image = None
    
    # A. Load Image Data (Local or Web)
    try:
        if path.startswith("http"):
            response = requests.get(path)
            image = Image.open(BytesIO(response.content))
        elif os.path.exists(path):
            image = Image.open(path)
    except Exception as e:
        st.error(f"⚠️ Could not load image: `{path}`")
        return

    if image:
        # B. Create Plotly Figure
        # 'binary_string=True' is efficient for large images
        fig = px.imshow(image, binary_string=True)
        
        # C. Configure Layout for "Map-like" feel
        fig.update_layout(
            # Remove axes and ticks
            xaxis={'showticklabels': False, 'visible': False},
            yaxis={'showticklabels': False, 'visible': False},
            # Remove margins so image fills the container
            margin=dict(l=0, r=0, t=0, b=0),
            # Enable Panning by default
            dragmode='pan',
            # Set a fixed height for the "viewport" (User scrolls inside this window)
            height=800, 
            hovermode=False
        )
        
        # D. Render
        st.markdown(f"### 🖼️ {os.path.basename(path)}")
        st.caption("🔍 **Controls:** Scroll to Zoom • Drag to Pan • Double-Click to Reset")
        
        # config={'scrollZoom': True} is the key to enabling mouse wheel zoom
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})