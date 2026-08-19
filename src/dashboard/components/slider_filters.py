
import streamlit as st

# Unrestricted defaults for filters
DEFAULTS = {
    "min_roe": 0.0,
    "max_debt_to_equity": 3.0,
    "min_fcf": -1000.0,
    "min_revenue_cagr_5yr": -20.0,
    "min_pat_cagr_5yr": -20.0,
    "min_operating_margin": -20.0,
    "max_pe": 150.0,
    "max_pb": 20.0,
    "min_dividend_yield": 0.0,
    "min_interest_coverage": 0.0,
}

# Preset mappings to overwrite defaults
PRESETS = {
    "Quality Compounder": {
        "min_roe": 15.0,
        "max_debt_to_equity": 1.0,
        "min_fcf": 0.0,
        "min_revenue_cagr_5yr": 10.0,
    },
    "Value Pick": {
        "max_pe": 20.0,
        "max_pb": 3.0,
        "max_debt_to_equity": 2.0,
        "min_dividend_yield": 1.0,
    },
    "Growth": {
        "min_pat_cagr_5yr": 20.0,
        "min_revenue_cagr_5yr": 15.0,
        "max_debt_to_equity": 2.0,
    },
    "Dividend": {
        "min_dividend_yield": 2.0,
        "min_fcf": 0.0,
    },
    "Debt-Free": {
        "max_debt_to_equity": 0.0,
        "min_roe": 12.0,
    },
    "Turnaround": {
        "min_fcf": 0.0,
    },
}


def init_filter_state():
    """Initializes the session state filter variables to unrestricted defaults."""
    for key, val in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = val


def apply_preset(name: str):
    """Resets to defaults and then overrides with preset configurations."""
    preset_vals = PRESETS[name]
    for key in DEFAULTS:
        st.session_state[key] = preset_vals.get(key, DEFAULTS[key])


def reset_all_filters():
    """Resets all filter keys to unrestricted defaults."""
    for key, val in DEFAULTS.items():
        st.session_state[key] = val


def render_slider_filters() -> dict[str, float]:
    """
    Renders preset buttons and sliders in the sidebar.
    Returns a dictionary of current slider filter values.
    """
    init_filter_state()

    st.sidebar.markdown(
        "<h3 style='margin-bottom:5px; font-weight:700;'>🎯 Preset Screeners</h3>",
        unsafe_allow_html=True,
    )

    # 6 presets in a 2x3 grid
    cols = st.sidebar.columns(2)
    preset_list = list(PRESETS.keys())
    for idx, name in enumerate(preset_list):
        col = cols[idx % 2]
        if col.button(name, key=f"btn_p_{idx}", use_container_width=True):
            apply_preset(name)
            st.rerun()

    if st.sidebar.button(
        "🔄 Reset All Filters",
        key="btn_reset_filters",
        use_container_width=True,
        type="secondary",
    ):
        reset_all_filters()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<h3 style='margin-bottom:5px; font-weight:700;'>🔍 Custom Filters</h3>",
        unsafe_allow_html=True,
    )

    # Render sliders
    min_roe = st.sidebar.slider("Min ROE (%)", 0.0, 100.0, key="min_roe", step=1.0)
    max_debt_to_equity = st.sidebar.slider(
        "Max Debt to Equity", 0.0, 5.0, key="max_debt_to_equity", step=0.1
    )
    min_fcf = st.sidebar.slider(
        "Min FCF (₹ Cr)", -5000.0, 15000.0, key="min_fcf", step=100.0
    )
    min_revenue_cagr_5yr = st.sidebar.slider(
        "Min Revenue CAGR (5y %)", -50.0, 100.0, key="min_revenue_cagr_5yr", step=1.0
    )
    min_pat_cagr_5yr = st.sidebar.slider(
        "Min PAT CAGR (5y %)", -50.0, 100.0, key="min_pat_cagr_5yr", step=1.0
    )
    min_operating_margin = st.sidebar.slider(
        "Min Operating Margin (%)", -50.0, 100.0, key="min_operating_margin", step=1.0
    )
    max_pe = st.sidebar.slider("Max PE", 0.0, 200.0, key="max_pe", step=1.0)
    max_pb = st.sidebar.slider("Max PB", 0.0, 50.0, key="max_pb", step=0.5)
    min_dividend_yield = st.sidebar.slider(
        "Min Dividend Yield (%)", 0.0, 20.0, key="min_dividend_yield", step=0.1
    )
    min_interest_coverage = st.sidebar.slider(
        "Min Interest Coverage", 0.0, 100.0, key="min_interest_coverage", step=0.5
    )

    return {
        "min_roe": min_roe,
        "max_debt_to_equity": max_debt_to_equity,
        "min_fcf": min_fcf,
        "min_revenue_cagr_5yr": min_revenue_cagr_5yr,
        "min_pat_cagr_5yr": min_pat_cagr_5yr,
        "min_operating_margin": min_operating_margin,
        "max_pe": max_pe,
        "max_pb": max_pb,
        "min_dividend_yield": min_dividend_yield,
        "min_interest_coverage": min_interest_coverage,
    }
