"""
utils/summariser.py
-------------------
Takes a DataFrame (the SQL result) and a user question,
then generates a concise business-analyst-style summary via OpenAI.
"""

from openai import OpenAI


def summarise_results(question: str, df_markdown: str, api_key: str) -> str:
    """
    Parameters
    ----------
    question    : original user question
    df_markdown : the result DataFrame formatted as a markdown table
    api_key     : OpenAI API key

    Returns
    -------
    A 3-5 sentence plain-English summary a business user would appreciate.
    """
    client = OpenAI(api_key=api_key)

    prompt = f"""You are a senior business analyst. A user asked:
"{question}"

Here is the query result:
{df_markdown}

Write a concise 3–5 sentence summary highlighting:
- The key trend or finding
- The highest and lowest values if applicable
- One actionable insight or recommendation

Use plain English. No bullet points. No markdown headers."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()
