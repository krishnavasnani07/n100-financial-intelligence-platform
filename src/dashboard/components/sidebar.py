import streamlit as st
from pathlib import Path
from PIL import Image

def render_sidebar_header():
    """Renders the brand logo and application title in the sidebar."""
    logo_path = Path(__file__).parent.parent / "assets" / "logo.png"
    if logo_path.exists():
        try:
            image = Image.open(logo_path)
            st.sidebar.image(image, width=120)
        except Exception:
            pass
    st.sidebar.markdown(
        "<h2 style='color: #a29bfe; font-size: 1.4rem; margin-top: 10px; font-weight: 700;'>Nifty 100</h2>"
        "<p style='color: #8892b0; font-size: 0.85rem; margin-top: -10px;'>Financial Intelligence Platform</p>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")
