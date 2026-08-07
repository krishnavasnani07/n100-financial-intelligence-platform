import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import settings


def check_db_exists():
    """Checks if the SQLite database file exists."""
    db_path = Path(settings.DB_PATH)
    if not db_path.exists():
        st.error("Database not found. Please build the database first.")
        st.stop()


def get_connection() -> sqlite3.Connection:
    """Creates a connection to SQLite and configures foreign keys."""
    check_db_exists()
    try:
        conn = sqlite3.connect(str(settings.DB_PATH))
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error:
        st.error("Unable to load data.")
        st.stop()


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """Fetches all companies from the database."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM companies", conn)
        return df
    except sqlite3.Error:
        st.error("Unable to load data.")
        st.stop()
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_ratios() -> pd.DataFrame:
    """Fetches all financial ratios."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
        return df
    except sqlite3.Error:
        st.error("Unable to load data.")
        st.stop()
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_pl() -> pd.DataFrame:
    """Fetches Profit & Loss statements."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
        return df
    except sqlite3.Error:
        st.error("Unable to load data.")
        st.stop()
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_bs() -> pd.DataFrame:
    """Fetches Balance Sheet data."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM balancesheet", conn)
        return df
    except sqlite3.Error:
        st.error("Unable to load data.")
        st.stop()
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_cf() -> pd.DataFrame:
    """Fetches Cash Flow data."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM cashflow", conn)
        return df
    except sqlite3.Error:
        st.error("Unable to load data.")
        st.stop()
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Fetches Sector classifications."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM sectors", conn)
        return df
    except sqlite3.Error:
        st.error("Unable to load data.")
        st.stop()
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_peers() -> pd.DataFrame:
    """Fetches Peer Groups."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM peer_groups", conn)
        return df
    except sqlite3.Error:
        st.error("Unable to load data.")
        st.stop()
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_valuation() -> pd.DataFrame:
    """Fetches Stock Prices (Valuation data source)."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM stock_prices", conn)
        return df
    except sqlite3.Error:
        st.error("Unable to load data.")
        st.stop()
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_documents() -> pd.DataFrame:
    """Fetches all annual reports and documents."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM documents", conn)
        return df
    except sqlite3.Error:
        st.error("Unable to load data.")
        st.stop()
    finally:
        conn.close()
