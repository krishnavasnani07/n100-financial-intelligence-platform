from pathlib import Path

import streamlit as st

from src.dashboard.components.sidebar import render_sidebar_header

# Set page configuration (must be the first Streamlit command)
st.set_page_config(
    page_title="Nifty 100 Analytics", layout="wide", initial_sidebar_state="expanded"
)

# Load custom CSS
css_path = Path(__file__).parent / "assets" / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Render brand assets and logo in sidebar
render_sidebar_header()

# Define pages relative to the app file directory
pages_dir = Path(__file__).parent / "pages"

home_page = st.Page(
    str(pages_dir / "01_home.py"), title="Home", icon="🏠", default=True
)
profile_page = st.Page(
    str(pages_dir / "02_profile.py"), title="Company Profile", icon="🏢"
)
screener_page = st.Page(str(pages_dir / "03_screener.py"), title="Screener", icon="🔍")
peers_page = st.Page(str(pages_dir / "04_peers.py"), title="Peer Comparison", icon="👥")
trends_page = st.Page(
    str(pages_dir / "05_trends.py"), title="Trend Analysis", icon="📈"
)
sectors_page = st.Page(
    str(pages_dir / "06_sectors.py"), title="Sector Analysis", icon="🏭"
)
capital_page = st.Page(
    str(pages_dir / "07_capital.py"), title="Capital Allocation", icon="💰"
)
reports_page = st.Page(
    str(pages_dir / "08_reports.py"), title="Annual Reports", icon="📄"
)

# Route the navigation
pg = st.navigation(
    [
        home_page,
        profile_page,
        screener_page,
        peers_page,
        trends_page,
        sectors_page,
        capital_page,
        reports_page,
    ]
)

pg.run()
