"""
utils/chart_builder.py
----------------------
Inspects the result DataFrame and picks the most appropriate
Plotly chart type automatically.

Heuristics
----------
- 1 date/month column + 1 numeric column  → line chart
- 1 categorical column + 1 numeric column → bar chart
- 2 numeric columns                       → scatter plot
- Anything else                           → bar chart (safe default)
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Brand-ish colour palette
PALETTE = ["#6366F1", "#10B981", "#F59E0B", "#EF4444", "#3B82F6", "#8B5CF6"]


def _looks_like_date(series: pd.Series) -> bool:
    return series.dtype == object and series.str.match(r"\d{4}-\d{2}").any()


def build_chart(df: pd.DataFrame, title: str = "Query Results") -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="No data returned")
        return fig

    date_cols    = [c for c in df.columns if _looks_like_date(df[c])]
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols     = [c for c in df.columns if c not in date_cols and c not in numeric_cols]

    # ── Line chart ──────────────────────────────────────────────────────────
    if date_cols and numeric_cols:
        x_col = date_cols[0]
        y_col = numeric_cols[0]
        color_col = cat_cols[0] if cat_cols else None

        fig = px.line(
            df.sort_values(x_col),
            x=x_col,
            y=y_col,
            color=color_col,
            markers=True,
            title=title,
            color_discrete_sequence=PALETTE,
        )
        fig.update_traces(line_width=2.5, marker_size=7)

    # ── Bar chart ─────────────────────────────────────────────────────────
    elif cat_cols and numeric_cols:
        x_col = cat_cols[0]
        y_col = numeric_cols[0]
        color_col = cat_cols[1] if len(cat_cols) > 1 else None

        fig = px.bar(
            df.sort_values(y_col, ascending=False),
            x=x_col,
            y=y_col,
            color=color_col,
            title=title,
            color_discrete_sequence=PALETTE,
            text_auto=".2s",
        )
        fig.update_traces(textposition="outside")

    # ── Scatter ──────────────────────────────────────────────────────────
    elif len(numeric_cols) >= 2:
        fig = px.scatter(
            df,
            x=numeric_cols[0],
            y=numeric_cols[1],
            title=title,
            color_discrete_sequence=PALETTE,
        )

    # ── Safe fallback ────────────────────────────────────────────────────
    else:
        fig = px.bar(df, title=title, color_discrete_sequence=PALETTE)

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=13),
        title_font_size=16,
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e5e7eb")

    return fig
