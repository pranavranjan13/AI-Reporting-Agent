"""
db_setup.py
-----------
Creates the SQLite database and seeds it with 200 rows of realistic
sales data spanning the last 12 months.

Run this once before starting the Streamlit app:
    python db_setup.py
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

import os
DB_PATH = os.path.join("/tmp", "sales.db")

CUSTOMERS = [
    "Acme Corp", "BlueStar Inc", "CloudNine Ltd", "DataBridge Co",
    "EdgeTech Solutions", "Fusion Dynamics", "GlobalMart", "HorizonPro",
    "InnovateTech", "JetStream LLC", "KineticWorks", "LaunchPad Inc",
]

REGIONS = ["North", "South", "East", "West"]

PRODUCTS = [
    "Analytics Suite", "Cloud Storage Pro", "DataVault", "ERP Connector",
    "FieldSync Mobile", "Governance Hub", "HR Automation", "Insight Dashboard",
]

# Product → (avg_revenue, avg_margin%)
PRODUCT_ECONOMICS = {
    "Analytics Suite":    (12000, 0.38),
    "Cloud Storage Pro":  (4500,  0.55),
    "DataVault":          (8000,  0.42),
    "ERP Connector":      (15000, 0.30),
    "FieldSync Mobile":   (3200,  0.60),
    "Governance Hub":     (9500,  0.35),
    "HR Automation":      (6000,  0.45),
    "Insight Dashboard":  (7000,  0.40),
}


def generate_data(n: int = 200) -> pd.DataFrame:
    random.seed(42)
    np.random.seed(42)

    end_date   = datetime.today()
    start_date = end_date - timedelta(days=365)

    rows = []
    for _ in range(n):
        product  = random.choice(PRODUCTS)
        avg_rev, margin = PRODUCT_ECONOMICS[product]
        revenue  = round(avg_rev * np.random.lognormal(0, 0.25), 2)
        profit   = round(revenue * margin * np.random.uniform(0.80, 1.20), 2)

        days_offset = random.randint(0, (end_date - start_date).days)
        order_date  = (start_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")

        rows.append({
            "order_date": order_date,
            "customer":   random.choice(CUSTOMERS),
            "region":     random.choice(REGIONS),
            "product":    product,
            "revenue":    revenue,
            "profit":     profit,
        })

    df = pd.DataFrame(rows).sort_values("order_date").reset_index(drop=True)
    return df


def init_db():
    df = generate_data(200)
    con = sqlite3.connect(DB_PATH)
    df.to_sql("sales", con, if_exists="replace", index=False)

    # Quick sanity check
    count = pd.read_sql("SELECT COUNT(*) AS n FROM sales", con).iloc[0, 0]
    con.close()
    print(f"✅  Database ready — {count} rows written to {DB_PATH}")


if __name__ == "__main__":
    init_db()
