import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

# PRINCIPLE: Efficiency & Resource Safety
# Caching this function prevents the app from opening files on every single re-run.
# This is crucial for preventing "OSError: Too many open files".
@st.cache_data
def load_timeline_assets(base_path: Path):
    """
    Loads timeline assets (CSS, JS, HTML) from the specified directory.
    """
    assets = {}
    errors = []
    
    # Define expected filenames
    files = {
        "css": "style.css",
        "js": "script.js",
        "html": "index.html"
    }

    for key, filename in files.items():
        file_path = base_path / filename
        try:
            # PRINCIPLE: Explicit Encoding
            # Always specify encoding to avoid platform-specific UnicodeDecodeErrors
            with open(file_path, "r", encoding="utf-8") as f:
                assets[key] = f.read()
        except FileNotFoundError:
            errors.append(f"Missing critical resource: {filename} at {file_path}")
        except Exception as e:
            errors.append(f"Error reading {filename}: {str(e)}")
    
    return assets, errors

def render_timeline_tab():
    """
    Main function to render the Timeline component tab.
    """
    # PRINCIPLE: Robust Pathing
    # Calculate paths relative to THIS file (views/timeline.py), not the user's CWD.
    # Structure: .../views/timeline.py -> parent is 'views' -> parent is 'root' -> 'timeline_assets'
    current_dir = Path(__file__).parent
    assets_dir = current_dir.parent / "timeline_assets"

    # Load assets via the cached function
    assets, errors = load_timeline_assets(assets_dir)

    # Handle errors gracefully without crashing the whole dashboard
    if errors:
        for error in errors:
            st.error(error)
        st.stop()

    css_content = assets["css"]
    js_content = assets["js"]
    html_content = assets["html"]

    # Extract body content (Simple parsing to isolate the Timeline container)
    try:
        body_start = html_content.find("<body>")
        if body_start != -1:
            body_start += 6  # Skip length of <body> tag
            body_end = html_content.find("</body>")
            body_html = html_content[body_start:body_end]
        else:
            body_html = html_content # Fallback
    except Exception as e:
        st.error(f"Error parsing HTML content: {e}")
        return

    # Construct the final HTML component
    # We inject CSS and JS directly to ensure they work within the iframe context
    full_html = f"""
    <!DOCTYPE html>
    <html style="overflow-x: auto; overflow-y: auto;">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans&display=swap" rel="stylesheet">
    <style>
    /* Streamlit Iframe Scrollbar Overrides */
    body {{
      overflow-x: auto;
      overflow-y: auto;
      margin: 0;
      padding: 0;
    }}
    ::-webkit-scrollbar {{ width: 12px; height: 12px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(136, 136, 136, 0.3); border-radius: 6px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: rgba(136, 136, 136, 0.5); }}
    * {{ scrollbar-width: thin; scrollbar-color: rgba(136, 136, 136, 0.3) transparent; }}
    
    /* Injected Timeline CSS */
    {css_content}
    </style>
    </head>
    <body style="overflow-x: auto; overflow-y: auto;">
    {body_html}

    <script>
    {js_content}
    </script>
    </body>
    </html>
    """

    # Dashboard UX Elements
    st.info("The timeline visualization is best viewed on larger screens. For optimal experience, please use a desktop or laptop.")
    st.warning("This timeline is not linear; it is dynamic based on user filters. The filters use an \"AND\" operation.")

    # Render Component
    components.html(full_html, height=800, scrolling=True)