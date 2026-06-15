"""
utils/sql_agent.py
------------------
Converts a plain-English question into a SQLite-compatible SQL query
using the OpenAI Chat Completions API.

The system prompt gives the model the exact schema so it never
hallucinates column names.
"""

from openai import OpenAI

SCHEMA = """
Table: sales
Columns:
  order_date  TEXT   -- format 'YYYY-MM-DD'
  customer    TEXT
  region      TEXT   -- one of: North, South, East, West
  product     TEXT
  revenue     REAL
  profit      REAL

Today's date is available via DATE('now') in SQLite.
"""

SYSTEM_PROMPT = f"""You are an expert SQL assistant. Given a user question, \
produce a single, correct SQLite query (no markdown fences, no explanation) \
that answers it using the table below.

{SCHEMA}

Rules:
- Output ONLY the SQL statement, nothing else.
- Use strftime for date formatting.
- Alias columns with readable names (e.g. total_revenue, month).
- Never use LIMIT unless the user asks for top-N results.
"""


def question_to_sql(question: str, api_key: str) -> str:
    """Return a SQL query string for the given natural-language question."""
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": question},
        ],
    )
    sql = response.choices[0].message.content.strip()
    # Strip accidental markdown fences in case the model slips
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql
