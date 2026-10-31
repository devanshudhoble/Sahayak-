"""AI-powered credit scoring from Sahayak usage and transaction patterns."""
import datetime as dt
import math


def compute_credit_signal(conn, shop_id, as_of: dt.date):
    """
    Generate a merchant credit signal from transaction patterns.

    Score components:
    1. Revenue consistency (30%) — low variance = stable business
    2. Growth trend (25%) — month-over-month revenue growth
    3. Transaction frequency (20%) — regular daily activity
    4. Experiment adoption (15%) — approved Sahayak suggestions
    5. Business tenure (10%) — months of data history
    """
    scores = {}

    # 1. Revenue consistency — coefficient of variation of weekly revenue
    weeks_data = _weekly_revenue(conn, shop_id, as_of, weeks=12)
    if len(weeks_data) < 4:
        return {"status": "insufficient_data", "message": "Need at least 4 weeks of data"}

    avg = sum(weeks_data) / len(weeks_data)
    if avg == 0:
        return {"status": "no_revenue", "message": "No revenue recorded"}

    std = math.sqrt(sum((x - avg) ** 2 for x in weeks_data) / len(weeks_data))
    cv = std / avg  # coefficient of variation
    consistency_score = max(0, min(100, round((1 - cv) * 100)))
    scores["consistency"] = {"score": consistency_score, "weight": 0.30,
                              "detail": f"Weekly revenue variance: {cv:.1%}"}

    # 2. Growth trend — compare last 4 weeks vs prior 4 weeks
    if len(weeks_data) >= 8:
        recent = sum(weeks_data[-4:]) / 4
        prior = sum(weeks_data[-8:-4]) / 4
        growth = (recent - prior) / prior if prior > 0 else 0
        growth_score = max(0, min(100, round(50 + growth * 200)))  # 0% = 50, +25% = 100
    else:
        growth = 0
        growth_score = 50
    scores["growth"] = {"score": growth_score, "weight": 0.25,
                         "detail": f"4-week growth: {growth:+.1%}"}

    # 3. Transaction frequency — avg daily transactions
    daily_counts = _daily_transaction_counts(conn, shop_id, as_of, days=30)
    active_days = sum(1 for c in daily_counts if c > 0)
    freq_score = max(0, min(100, round(active_days / 30 * 100)))
    scores["frequency"] = {"score": freq_score, "weight": 0.20,
                            "detail": f"Active {active_days}/30 days"}

    # 4. Experiment adoption — did they engage with Sahayak suggestions?
    try:
        row = conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) FROM actions WHERE shop_id=?",
            (shop_id,)
        ).fetchone()
        total_actions, approved = row[0] or 0, row[1] or 0
        adopt_score = 100 if approved > 0 else (30 if total_actions > 0 else 0)
    except Exception:
        adopt_score = 50  # no actions table yet
        total_actions, approved = 0, 0
    scores["adoption"] = {"score": adopt_score, "weight": 0.15,
                           "detail": f"{approved}/{total_actions} experiments approved"}

    # 5. Business tenure — months of data
    try:
        earliest = conn.execute(
            "SELECT MIN(substr(ts,1,10)) FROM transactions WHERE shop_id=?", (shop_id,)
        ).fetchone()[0]
        if earliest:
            tenure_days = (as_of - dt.date.fromisoformat(earliest)).days
            tenure_months = tenure_days / 30
            tenure_score = min(100, round(tenure_months / 6 * 100))  # 6 months = full score
        else:
            tenure_score = 0
            tenure_months = 0
    except Exception:
        tenure_score = 0
        tenure_months = 0
    scores["tenure"] = {"score": tenure_score, "weight": 0.10,
                         "detail": f"{tenure_months:.1f} months of data"}

    # Weighted total
    total = sum(s["score"] * s["weight"] for s in scores.values())
    total = round(total)

    # Lending recommendation
    if total >= 75:
        recommendation = "Strong candidate for Paytm Merchant Loan"
        risk = "Low"
        max_loan = round(avg * 4 * 12)  # ~12 months of weekly revenue
    elif total >= 50:
        recommendation = "Moderate candidate — consider small working capital loan"
        risk = "Medium"
        max_loan = round(avg * 4 * 6)
    else:
        recommendation = "Build more history before lending"
        risk = "High"
        max_loan = 0

    return {
        "status": "ok",
        "credit_score": total,
        "max_score": 100,
        "risk_level": risk,
        "recommendation": recommendation,
        "suggested_loan_limit": max_loan,
        "avg_weekly_revenue": round(avg),
        "components": scores,
    }


def _weekly_revenue(conn, shop_id, as_of, weeks=12):
    """Get weekly revenue totals."""
    start = as_of - dt.timedelta(days=weeks * 7)
    rows = conn.execute(
        """SELECT CAST((julianday(substr(ts,1,10)) - julianday(?)) / 7 AS INTEGER) AS week_num,
                  SUM(amount)
           FROM transactions
           WHERE shop_id = ? AND substr(ts,1,10) BETWEEN ? AND ?
           GROUP BY week_num ORDER BY week_num""",
        (start.isoformat(), shop_id, start.isoformat(), as_of.isoformat()),
    ).fetchall()
    return [r[1] for r in rows]


def _daily_transaction_counts(conn, shop_id, as_of, days=30):
    """Count transactions per day for the last N days."""
    start = as_of - dt.timedelta(days=days)
    rows = conn.execute(
        """SELECT substr(ts,1,10), COUNT(*)
           FROM transactions
           WHERE shop_id = ? AND substr(ts,1,10) BETWEEN ? AND ?
           GROUP BY 1""",
        (shop_id, start.isoformat(), as_of.isoformat()),
    ).fetchall()
    counts = {r[0]: r[1] for r in rows}
    return [counts.get((start + dt.timedelta(days=i)).isoformat(), 0) for i in range(days)]
