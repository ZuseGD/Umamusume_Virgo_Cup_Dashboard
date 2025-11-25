import streamlit as st
import os

def show_view(current_config):
    # 1. Header
    event_name = current_config.get('id', 'Champion Meeting').replace('_', ' ').title()
    st.header(f"📚 Guides: {event_name}")
    
    # 2. Load Images from Config
    images = current_config.get('guide_images', [])
    
    if not images:
        st.info("ℹ️ No guide images found for this event.")
        return

    # 3. Display Images
    for img_path in images:
        if os.path.exists(img_path):
            st.image(img_path, use_column_width=True)
        else:
            # Helpful error message for you
            st.warning(f"⚠️ Missing Image: `{img_path}`")
            st.caption("Please upload your Canva image to the `images/` folder and ensure the name matches `cm_config.py`.")

    st.markdown("---")
    
    # 4. External Resources (Static Footer)
    st.subheader("🔗 Useful Resources")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("📖 GameTora Wiki", "https://gametora.com/umamusume")
    with c2:
        st.link_button("📺 MooMooCows", "https://www.youtube.com/@MooMooCows")
    with c3:
        st.link_button("🐦 MooMooCows Discord", "https://discord.gg/SY2aWGu53S")