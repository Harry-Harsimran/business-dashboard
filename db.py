
import sqlite3
from pathlib import Path

import generate_data

DB_PATH = Path(__file__).parent / "dashboard.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

OTHER_OPEX_RATE = 0.08  


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and generate a fresh sample dataset. Safe to re-run."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text())
        generate_data.populate(conn)
    print(f"Initialized {DB_PATH} with sample data")


def get_monthly_metrics():
    """Revenue, COGS, marketing spend, other opex, net profit and margin per month."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            WITH order_agg AS (
                SELECT strftime('%Y-%m', order_date) AS month,
                       SUM(quantity * unit_price) AS revenue,
                       SUM(quantity * unit_cost)  AS cogs
                FROM orders
                GROUP BY month
            )
            SELECT o.month, o.revenue, o.cogs, COALESCE(m.spend, 0) AS marketing_spend
            FROM order_agg o
            LEFT JOIN marketing_spend m ON m.month = o.month
            ORDER BY o.month
            """
        ).fetchall()

    result = []
    for r in rows:
        other_opex = r["revenue"] * OTHER_OPEX_RATE
        total_cost = r["cogs"] + r["marketing_spend"] + other_opex
        profit = r["revenue"] - total_cost
        margin = round(profit * 100.0 / r["revenue"], 1) if r["revenue"] else 0
        result.append({
            "month": r["month"],
            "revenue": round(r["revenue"] / 1e5, 2),   # ₹ lakh
            "cost": round(total_cost / 1e5, 2),        # ₹ lakh
            "profit": round(profit / 1e5, 2),          # ₹ lakh
            "margin_pct": margin,
        })
    return result


def get_growth_series():
    """MoM % change in revenue, computed with a window function (LAG)."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            WITH order_agg AS (
                SELECT strftime('%Y-%m', order_date) AS month,
                       SUM(quantity * unit_price) AS revenue
                FROM orders
                GROUP BY month
            )
            SELECT month, revenue,
                   LAG(revenue) OVER (ORDER BY month) AS prev_revenue
            FROM order_agg
            ORDER BY month
            """
        ).fetchall()

    out = []
    for r in rows:
        if r["prev_revenue"]:
            growth = round((r["revenue"] - r["prev_revenue"]) * 100.0 / r["prev_revenue"], 1)
        else:
            growth = None
        out.append({
            "month": r["month"],
            "revenue": round(r["revenue"] / 1e5, 2),
            "mom_growth_pct": growth,
        })
    return out


def get_summary():
    """Headline KPI cards: total revenue, total profit, margin, latest MoM growth."""
    data = get_monthly_metrics()
    growth = get_growth_series()

    total_revenue = round(sum(r["revenue"] for r in data), 2)
    total_profit = round(sum(r["profit"] for r in data), 2)
    net_margin = round(total_profit * 100.0 / total_revenue, 1) if total_revenue else 0
    latest_growth = growth[-1]["mom_growth_pct"] if growth else None

    return {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "net_margin": net_margin,
        "latest_growth": latest_growth,
    }


def _revenue_growth_q1_q4(conn):
    rows = conn.execute(
        """
        SELECT strftime('%Y-%m', order_date) AS month,
               SUM(quantity * unit_price) AS revenue
        FROM orders GROUP BY month ORDER BY month
        """
    ).fetchall()
    months = [r["revenue"] for r in rows]
    if len(months) < 6:
        return 0
    q1_avg = sum(months[:3]) / 3
    q4_avg = sum(months[-3:]) / 3
    return round((q4_avg - q1_avg) * 100.0 / q1_avg, 1) if q1_avg else 0


def _gross_and_net_margin(conn):
    row = conn.execute(
        "SELECT SUM(quantity*unit_price) AS revenue, SUM(quantity*unit_cost) AS cogs FROM orders"
    ).fetchone()
    spend_row = conn.execute("SELECT SUM(spend) AS total_spend FROM marketing_spend").fetchone()
    revenue, cogs = row["revenue"], row["cogs"]
    total_spend = spend_row["total_spend"] or 0
    gross_margin = round((revenue - cogs) * 100.0 / revenue, 1) if revenue else 0
    other_opex = revenue * OTHER_OPEX_RATE
    net_profit = revenue - cogs - total_spend - other_opex
    net_margin = round(net_profit * 100.0 / revenue, 1) if revenue else 0
    return gross_margin, net_margin


def _churn_rate(conn):
    """Avg % of customers active in month M-1 who placed no order in month M."""
    rows = conn.execute(
        """
        SELECT DISTINCT customer_id, strftime('%Y-%m', order_date) AS month
        FROM orders
        """
    ).fetchall()
    active_by_month = {}
    for r in rows:
        active_by_month.setdefault(r["month"], set()).add(r["customer_id"])

    months = sorted(active_by_month.keys())
    churn_rates = []
    for prev, cur in zip(months, months[1:]):
        prev_customers = active_by_month[prev]
        if not prev_customers:
            continue
        churned = prev_customers - active_by_month[cur]
        churn_rates.append(len(churned) * 100.0 / len(prev_customers))
    return round(sum(churn_rates) / len(churn_rates), 1) if churn_rates else 0


def _cac(conn):
    total_spend = conn.execute("SELECT SUM(spend) AS s FROM marketing_spend").fetchone()["s"] or 0
    new_customers = conn.execute("SELECT COUNT(*) AS c FROM customers").fetchone()["c"] or 1
    return round(total_spend / new_customers, 0)


def _ltv(conn):
    row = conn.execute(
        """
        SELECT SUM(quantity*unit_price) * 1.0 / COUNT(DISTINCT customer_id) AS ltv
        FROM orders
        """
    ).fetchone()
    return round(row["ltv"] or 0, 0)


def _aov(conn):
    row = conn.execute(
        "SELECT SUM(quantity*unit_price) * 1.0 / COUNT(*) AS aov FROM orders"
    ).fetchone()
    return round(row["aov"] or 0, 0)


def get_kpis():
    """Target vs actual for the core KPI set, all computed from live tables."""
    with get_connection() as conn:
        targets = {r["name"]: r for r in conn.execute("SELECT * FROM kpi_targets").fetchall()}

        gross_margin, net_margin = _gross_and_net_margin(conn)
        cac = _cac(conn)
        ltv = _ltv(conn)

        actuals = {
            "Revenue growth (Q1 → Q4)": _revenue_growth_q1_q4(conn),
            "Net margin": net_margin,
            "Gross margin": gross_margin,
            "Monthly churn": _churn_rate(conn),
            "LTV : CAC ratio": round(ltv / cac, 1) if cac else 0,
            "Customer Acquisition Cost": cac,
            "Customer LTV": ltv,
            "Average Order Value": _aov(conn),
        }

    out = []
    for name, t in targets.items():
        actual = actuals.get(name, 0)
        lower_is_better = bool(t["lower_is_better"])
        good = actual <= t["target"] if lower_is_better else actual >= t["target"]
        out.append({
            "name": name,
            "target": t["target"],
            "actual": actual,
            "unit": t["unit"],
            "status": "good" if good else "watch",
        })
    return out


if __name__ == "__main__":
    init_db()
