import streamlit as st
import streamlit.components.v1 as components
import base64
from pathlib import Path

def render_timeline_tab():

  st.set_page_config(page_title="Unc Timeline", layout="wide", initial_sidebar_state="collapsed")
  
  st.markdown("""
      <style>
          .main {
              background-color: #0e1117;
          }
          [data-testid="stAppViewContainer"] {
              background-color: #0e1117;
          }
          [data-testid="stHeader"] {
              background-color: #0e1117;
          }
      </style>
  """, unsafe_allow_html=True)
  st.info("The timeline visualization is best viewed on larger screens. For optimal experience, please use a desktop or laptop. ")
  st.warning("This timeline is not linear; it is dynamic based on user filters. The filters are \"AND\" operation, not \"OR\" operation.")

  # 2. Error Handling & Resource Loading
  try:

    with open("timeline_assets/style.css", "r") as f:
        css_content = f.read()

    with open("timeline_assets/script.js", "r") as f:
        js_content = f.read()

    with open("timeline_assets/index.html", "r") as f:
        html_content = f.read()
  except FileNotFoundError as e:
    st.error(f"Error loading timeline assets: {e}")
    st.stop()

  body_start = html_content.find("<body>") + 6
  body_end = html_content.find("</body>")
  body_html = html_content[body_start:body_end]

  def get_image_base64(image_path):
      try:
          with open(image_path, "rb") as f:
              return base64.b64encode(f.read()).decode()
      except:
          return None

  full_html = f"""
  <!DOCTYPE html>
  <html style="overflow-x: auto; overflow-y: auto;">
  <head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans&display=swap" rel="stylesheet">
  <style>
  body {{
    overflow-x: auto;
    overflow-y: auto;
    margin: 0;
    padding: 0;
  }}
  html {{
    overflow-x: auto;
    overflow-y: auto;
  }}
  ::-webkit-scrollbar {{
    width: 12px;
    height: 12px;
  }}
  ::-webkit-scrollbar-track {{
    background: transparent;
  }}
  ::-webkit-scrollbar-thumb {{
    background: rgba(136, 136, 136, 0.3);
    border-radius: 6px;
  }}
  ::-webkit-scrollbar-thumb:hover {{
    background: rgba(136, 136, 136, 0.5);
  }}
  * {{
    scrollbar-width: thin;
    scrollbar-color: rgba(136, 136, 136, 0.3) transparent;
  }}
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

  components.html(full_html, height=800, scrolling=True)
