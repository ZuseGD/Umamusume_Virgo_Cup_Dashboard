import streamlit as st
import streamlit.components.v1 as components
import base64
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
            render_custom_viewer(img_path)

    st.markdown("---")

    # 4. CREDITS
    st.subheader("🙏 Credits")
    st.markdown("""
    A huge thank you to the team behind these resources:
    - **Strategy & Guide:** [MooMooCows](https://www.youtube.com/@MooMooCows)
    - **Graphics & Visuals:** MooMooCows' Canva Helpers
    """)
    
    st.markdown("---")
    
    # 5. External Resources
    st.subheader("🔗 Useful Resources")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("📖 GameTora Wiki", "https://gametora.com/umamusume")
    with c2:
        st.link_button("📺 MooMooCows", "https://www.youtube.com/@MooMooCows")
    with c3:
        st.link_button("🐦 MooMooCows Discord", "https://discord.gg/SY2aWGu53S")

def get_image_src(path):
    """
    Helper to get the correct source string for the HTML img tag.
    - If it's a URL, return it directly (Let the browser fetch it).
    - If it's a local file, convert to Base64.
    """
    if path.startswith("http"):
        return path
    
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            mime_type = "image/png" if path.endswith("png") else "image/jpeg"
            return f"data:{mime_type};base64,{b64}"
    return ""

def render_custom_viewer(path):
    """
    Renders a high-performance HTML/JS Image Viewer.
    Uses CSS Transforms for GPU-accelerated Pan/Zoom (No Lag).
    """
    src = get_image_src(path)
    
    if not src:
        st.error(f"⚠️ Could not load image: `{path}`")
        return

    
    if path.startswith("http"):
        st.link_button("🔍 Open Full Resolution Image (New Tab)", path)

    st.caption("🖱️ **Controls:** Scroll to Zoom • Click & Drag to Pan")

    # --- CUSTOM HTML/JS VIEWER ---
    html_code = f"""
    <!DOCTYPE html>
    <html style="margin: 0; padding: 0; overflow: hidden;">
    <head>
        <style>
            body {{ margin: 0; background-color: #0e1117; display: flex; justify-content: center; align-items: center; height: 100vh; }}
            #container {{ 
                width: 100%; 
                height: 100%; 
                overflow: hidden; 
                cursor: grab; 
                display: flex;
                justify-content: center;
                align-items: center;
                border: 1px solid #333;
                border-radius: 5px;
            }}
            #container:active {{ cursor: grabbing; }}
            img {{ 
                max-width: 95%; 
                max-height: 95%; 
                transition: transform 0.05s ease-out; 
                transform-origin: 0 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }}
        </style>
    </head>
    <body>
        <div id="container">
            <img id="pan-zoom-image" src="{src}" draggable="false">
        </div>
        <script>
            const container = document.getElementById('container');
            const img = document.getElementById('pan-zoom-image');
            
            let scale = 1;
            let panning = false;
            let pointX = 0;
            let pointY = 0;
            let startX = 0;
            let startY = 0;
            
            // Transform coordinates
            let x = 0;
            let y = 0;

            function setTransform() {{
                img.style.transform = `translate(${{x}}px, ${{y}}px) scale(${{scale}})`;
            }}

            container.addEventListener('mousedown', (e) => {{
                e.preventDefault();
                startX = e.clientX - x;
                startY = e.clientY - y;
                panning = true;
            }});

            container.addEventListener('mouseup', () => {{
                panning = false;
            }});
            
            container.addEventListener('mouseleave', () => {{
                panning = false;
            }});

            container.addEventListener('mousemove', (e) => {{
                if (!panning) return;
                e.preventDefault();
                x = e.clientX - startX;
                y = e.clientY - startY;
                setTransform();
            }});

            container.addEventListener('wheel', (e) => {{
                e.preventDefault();
                
                const xs = (e.clientX - x) / scale;
                const ys = (e.clientY - y) / scale;
                const delta = -e.deltaY;
                
                // Zoom factor
                (delta > 0) ? (scale *= 1.1) : (scale /= 1.1);
                
                // Limit Zoom
                scale = Math.min(Math.max(0.5, scale), 10); // Min 0.5x, Max 10x
                
                // Zoom towards mouse pointer
                x = e.clientX - xs * scale;
                y = e.clientY - ys * scale;
                
                setTransform();
            }});
        </script>
    </body>
    </html>
    """
    
    # Render the component with a fixed height of 750px
    components.html(html_code, height=750)