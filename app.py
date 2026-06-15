"""
app.py
------
Main Streamlit application — the only file users need to run.

    streamlit run app.py

Workflow
--------
1. User pastes their OpenAI key in the sidebar (stored in session state only)
2. User types a question in plain English
3. App calls OpenAI → SQL → SQLite → DataFrame
4. App renders: data table + Plotly chart + AI summary
5. "Email Weekly Report" button triggers HTML report generation / send
"""

import sqlite3
import os

import pandas as pd
import streamlit as st

from db_setup import init_db, DB_PATH
from utils.sql_agent    import question_to_sql
from utils.summariser   import summarise_results
from utils.chart_builder import build_chart
from utils.email_report  import send_email_report

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Reporting Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject custom CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── global ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* ── sidebar ── */
  [data-testid="stSidebar"] {
    background: #1e1b4b;
  }
  [data-testid="stSidebar"] * { color: #e0e7ff !important; }
  [data-testid="stSidebar"] .stTextInput input {
    background: #312e81; border: 1px solid #4338ca; color: #fff;
  }
  [data-testid="stSidebar"] label { color: #c7d2fe !important; font-size: 12px; }

  /* ── metric cards ── */
  [data-testid="stMetric"] {
    background: #f5f3ff;
    border: 1px solid #ddd6fe;
    border-radius: 12px;
    padding: 16px 20px;
  }
  [data-testid="stMetricValue"] { color: #4f46e5; font-size: 28px; font-weight: 700; }
  [data-testid="stMetricLabel"] { color: #6b7280; font-size: 12px; }

  /* ── SQL box ── */
  .sql-box {
    background: #1e1b4b;
    color: #a5b4fc;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
    white-space: pre-wrap;
    word-break: break-all;
  }

  /* ── summary card ── */
  .summary-card {
    background: linear-gradient(135deg, #ede9fe 0%, #dbeafe 100%);
    border-left: 4px solid #6366f1;
    border-radius: 10px;
    padding: 18px 22px;
    color: #1e1b4b;
    line-height: 1.75;
  }

  /* ── email preview ── */
  .email-preview-label {
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: .05em;
    margin-bottom: 6px;
  }

  /* ── button ── */
  div.stButton > button {
    background: #6366f1;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 10px 22px;
    font-weight: 600;
    transition: background .2s;
  }
  div.stButton > button:hover { background: #4f46e5; }

  /* ── header gradient ── */
  .hero-header {
    background: linear-gradient(120deg, #6366f1, #8b5cf6);
    border-radius: 14px;
    padding: 28px 32px;
    margin-bottom: 28px;
    color: white;
  }
  .hero-header h1 { margin: 0; font-size: 28px; font-weight: 700; }
  .hero-header p  { margin: 6px 0 0; opacity: .85; font-size: 14px; }
</style>
""", unsafe_allow_html=True)


# ── Bootstrap DB (idempotent) ─────────────────────────────────────────────
if not os.path.exists(DB_PATH):
    init_db()


# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    _secret_key = st.secrets.get("OPENAI_API_KEY", "")
    api_key = st.text_input(
        "OpenAI API Key",
        value=_secret_key,
        type="password",
        placeholder="sk-...",
        help="Auto-filled from Streamlit secrets if set, otherwise paste your key here.",
    )
    st.markdown("---")
    st.markdown("### 📩 Email Settings")
    recipient = st.text_input("Recipient email", placeholder="analyst@company.com")
    st.caption("Set SMTP_HOST / SMTP_USER / SMTP_PASS env vars to enable sending.")
    st.markdown("---")
    st.markdown("### 💡 Try these questions")
    example_questions = [
        "Show revenue trend for the last 6 months",
        "Which region had the highest profit this year?",
        "Top 5 customers by total revenue",
        "Revenue vs profit by product",
        "Monthly revenue breakdown by region",
    ]
    for q in example_questions:
        if st.button(q, key=f"ex_{q[:20]}"):
            st.session_state["question"] = q


# ── Hero header ───────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
  <h1>📊 AI Reporting Agent</h1>
  <p>Ask a plain-English question → get SQL, a chart, and an AI summary instantly.</p>
</div>
""", unsafe_allow_html=True)


# ── KPI bar ───────────────────────────────────────────────────────────────
con = sqlite3.connect(DB_PATH)
kpi_df = pd.read_sql("""
    SELECT
        ROUND(SUM(revenue), 0)   AS total_revenue,
        ROUND(SUM(profit),  0)   AS total_profit,
        COUNT(DISTINCT customer) AS customers,
        COUNT(*)                 AS orders
    FROM sales
""", con)
con.close()

k = kpi_df.iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue",  f"${k.total_revenue:,.0f}")
c2.metric("Total Profit",   f"${k.total_profit:,.0f}")
c3.metric("Customers",      int(k.customers))
c4.metric("Total Orders",   int(k.orders))

st.markdown("---")


# ── Question input ────────────────────────────────────────────────────────
default_q = st.session_state.get("question", "Show revenue trend for the last 6 months")
question  = st.text_input(
    "🔍 Ask your question",
    value=default_q,
    placeholder="e.g. Show revenue trend for the last 6 months",
)

run_col, email_col = st.columns([1, 5])
with run_col:
    run_clicked = st.button("▶ Run", use_container_width=True)
with email_col:
    email_clicked = st.button("📧 Email Weekly Report", use_container_width=False)


# ── Main logic ────────────────────────────────────────────────────────────
if run_clicked or email_clicked:

    # ── Guard: API key ───────────────────────────────────────────────────
    if not api_key:
        st.warning("Please enter your OpenAI API key in the sidebar first.")
        st.stop()

    if not question.strip():
        st.warning("Please type a question.")
        st.stop()

    # ── Step 1 : Natural language → SQL ─────────────────────────────────
    with st.spinner("🤖 Converting question to SQL…"):
        try:
            sql = question_to_sql(question, api_key)
        except Exception as e:
            st.error(f"SQL generation failed: {e}")
            st.stop()

    with st.expander("🔎 Generated SQL", expanded=True):
        st.markdown(f'<div class="sql-box">{sql}</div>', unsafe_allow_html=True)

    # ── Step 2 : Execute SQL ─────────────────────────────────────────────
    try:
        con = sqlite3.connect(DB_PATH)
        result_df = pd.read_sql(sql, con)
        con.close()
    except Exception as e:
        st.error(f"Query execution failed: {e}")
        st.stop()

    if result_df.empty:
        st.info("The query returned no rows. Try rephrasing your question.")
        st.stop()

    # ── Step 3 : Display data table ──────────────────────────────────────
    st.markdown("### 📋 Results")
    st.dataframe(
        result_df.style.format(
            {c: "{:,.2f}" for c in result_df.select_dtypes("number").columns}
        ),
        use_container_width=True,
        height=min(400, 60 + len(result_df) * 36),
    )

    # ── Step 4 : Plotly chart ────────────────────────────────────────────
    st.markdown("### 📈 Chart")
    fig = build_chart(result_df, title=question)
    st.plotly_chart(fig, use_container_width=True)

    # ── Step 5 : AI summary ──────────────────────────────────────────────
    with st.spinner("✍️ Generating summary…"):
        try:
            summary = summarise_results(question, result_df.to_markdown(index=False), api_key)
        except Exception as e:
            summary = f"(Summary unavailable: {e})"

    st.markdown("### 💬 AI Summary")
    st.markdown(f'<div class="summary-card">{summary}</div>', unsafe_allow_html=True)

    # ── Step 6 : Email report ────────────────────────────────────────────
    if email_clicked:
        with st.spinner("📤 Preparing report…"):
            result = send_email_report(
                df=result_df,
                summary=summary,
                question=question,
                to_address=recipient or "",
            )

        if result["sent"]:
            st.success(result["message"])
        else:
            st.info(result["message"])

        # Always render the HTML preview
        st.markdown('<p class="email-preview-label">Email Preview</p>', unsafe_allow_html=True)
        st.components.v1.html(result["html"], height=600, scrolling=True)
