import streamlit as st
import pandas as pd

def render_report_links_table(df_docs: pd.DataFrame):
    """
    Renders a table displaying annual report links, years, and availability statuses.
    """
    if df_docs.empty:
        st.info("No annual reports found matching your criteria.")
        return

    df_formatted = df_docs.copy()
    
    # Check availability
    df_formatted['status'] = df_formatted['annual_report'].apply(
        lambda x: "🟢 Available" if pd.notnull(x) and str(x).strip().startswith(('http://', 'https://')) else "🔴 Unavailable"
    )
    
    # Set the report link (use None for unavailable reports to render empty cell in LinkColumn)
    df_formatted['report_link'] = df_formatted.apply(
        lambda r: r['annual_report'] if r['status'] == "🟢 Available" else None,
        axis=1
    )

    # Prepare display columns
    df_display = df_formatted[['year', 'status', 'report_link']].copy()
    df_display.rename(columns={
        'year': 'Financial Year',
        'status': 'Status',
        'report_link': 'Report Link'
    }, inplace=True)

    # Sort by financial year descending
    df_display.sort_values(by="Financial Year", ascending=False, inplace=True)

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Financial Year": st.column_config.TextColumn("Financial Year", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="medium"),
            "Report Link": st.column_config.LinkColumn("Download/View Link", display_text="Download PDF")
        }
    )
