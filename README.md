# 📊 AI Reporting Agent

A lightweight weekend project that lets anyone query a sales database in plain
English and instantly get a data table, a Plotly chart, and an AI-written
summary — no SQL knowledge required.

---

## Project Structure

```
ai_reporting_agent/
│
├── app.py               ← Streamlit UI (the only file you run)
├── db_setup.py          ← Creates SQLite DB + 200 rows of sample data
├── requirements.txt     ← Python dependencies
├── .env.example         ← Template for SMTP email config
├── sales.db             ← Auto-created on first run
│
└── utils/
    ├── sql_agent.py     ← Natural language → SQL  (OpenAI)
    ├── summariser.py    ← DataFrame → AI narrative (OpenAI)
    ├── chart_builder.py ← Auto-selects best Plotly chart type
    └── email_report.py  ← Builds HTML report, optional SMTP send
```

---

## Quickstart (5 minutes)

### 1. Install dependencies

```bash
cd ai_reporting_agent
pip install -r requirements.txt
```

### 2. (Optional) Seed the database manually

The app auto-seeds on first launch, but you can also run:

```bash
python db_setup.py
```

### 3. Start the app

```bash
streamlit run app.py
```

### 4. Use it

1. Paste your **OpenAI API key** in the sidebar.
2. Type a question like `Show revenue trend for the last 6 months` and click **▶ Run**.
3. View the data table, chart, and AI summary.
4. Optionally click **📧 Email Weekly Report** (configure SMTP first — see below).

---

## How it works (full workflow)

```
User question (plain English)
        │
        ▼
 utils/sql_agent.py
   OpenAI gpt-4o-mini
   converts question → SQL
        │
        ▼
  SQLite (sales.db)
   SQL executes →  DataFrame
        │
        ├──► Streamlit data table
        │
        ├──► utils/chart_builder.py
        │     auto-picks line / bar / scatter
        │     returns Plotly Figure
        │
        └──► utils/summariser.py
              OpenAI gpt-4o-mini
              DataFrame → 3-5 sentence summary
                    │
                    └──► utils/email_report.py
                          builds HTML report
                          optional SMTP send
```

---

## Sample questions to try

| Question | Chart type produced |
|---|---|
| Show revenue trend for the last 6 months | Line |
| Which region had the highest profit this year? | Bar |
| Top 5 customers by total revenue | Bar |
| Revenue vs profit by product | Bar |
| Monthly revenue breakdown by region | Line (multi-series) |

---

## Sales table schema

| Column | Type | Notes |
|---|---|---|
| order_date | TEXT | `YYYY-MM-DD` |
| customer | TEXT | 12 companies |
| region | TEXT | North / South / East / West |
| product | TEXT | 8 SaaS products |
| revenue | REAL | Lognormal distribution |
| profit | REAL | Margin varies by product |

---

## Email setup (optional)

Copy `.env.example` to `.env` and fill in your SMTP credentials:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASS=your_app_password   # Gmail: use an App Password, not your login password
SMTP_FROM=you@gmail.com
```

Load the file before starting the app:

```bash
# Linux / macOS
export $(cat .env | xargs)
streamlit run app.py

# Windows PowerShell
Get-Content .env | ForEach-Object { $k,$v = $_ -split '=',2; [System.Environment]::SetEnvironmentVariable($k,$v) }
streamlit run app.py
```

If SMTP is not configured, clicking **Email Weekly Report** still shows an
HTML preview of the report inside the app.

---

## Extending the project

| Idea | Where to change |
|---|---|
| Add more tables | `db_setup.py` + update `SCHEMA` in `sql_agent.py` |
| Support Claude / Gemini | Swap `client.chat.completions` in `sql_agent.py` |
| Persist query history | Add a `history` table in `db_setup.py` |
| Schedule weekly emails | Wrap `email_report.py` in a cron job / GitHub Action |
| Deploy to cloud | `streamlit run app.py` works on Streamlit Community Cloud out of the box |

---

## Requirements

- Python 3.10+
- OpenAI API key (gpt-4o-mini, very low cost — typical session < $0.01)
- SQLite (built into Python, nothing to install)
