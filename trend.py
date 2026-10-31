"""Trend detection. No AI here: plain arithmetic on payment history, so every number can be checked."""
import datetime as dt
from statistics import mean

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DROP_THRESHOLD = -0.10   # flag a weekday whose collections fell at least 10%
STABLE_LIMIT = 0.08      # other weekdays within +/-8% means the drop is day-specific


def daily_totals(conn, shop_id, start, end):
    """Collections per calendar day, with zeros for days that had no payments."""
    rows = conn.execute(
        """SELECT substr(ts, 1, 10), SUM(amount) FROM transactions
           WHERE shop_id = ? AND substr(ts, 1, 10) BETWEEN ? AND ? GROUP BY 1""",
        (shop_id, start.isoformat(), end.isoformat()),
    ).fetchall()
    totals = {dt.date.fromisoformat(d): t for d, t in rows}
    days = (end - start).days + 1
    return {start + dt.timedelta(days=i): totals.get(start + dt.timedelta(days=i), 0.0)
            for i in range(days)}


def detect(conn, shop_id, as_of):
    """Compare the last 3 weeks with the 3 weeks before, weekday by weekday."""
    prior_start = as_of - dt.timedelta(days=41)
    recent_start = as_of - dt.timedelta(days=20)
    prior_end = as_of - dt.timedelta(days=21)

    earliest = conn.execute(
        "SELECT MIN(substr(ts, 1, 10)) FROM transactions WHERE shop_id = ?", (shop_id,)
    ).fetchone()[0]
    if earliest is None or dt.date.fromisoformat(earliest) > prior_start:
        return {"status": "insufficient_history"}

    totals = daily_totals(conn, shop_id, prior_start, as_of)
    per_day = {}
    for wd in range(7):
        prior = [totals[d] for d in sorted(totals) if d <= prior_end and d.weekday() == wd]
        recent = [totals[d] for d in sorted(totals) if d >= recent_start and d.weekday() == wd]
        p_avg, r_avg = mean(prior), mean(recent)
        per_day[wd] = {
            "change": (r_avg - p_avg) / p_avg if p_avg else 0.0,
            "weeks_lower": sum(r < p for p, r in zip(prior, recent)),
            "prior_avg": p_avg,
            "recent_avg": r_avg,
        }

    # A weekday is flagged only if it fell 10% or more AND fell in at least 2 of the 3 weeks.
    flagged = [dict(weekday=WEEKDAYS[wd], **v) for wd, v in per_day.items()
               if v["change"] <= DROP_THRESHOLD and v["weeks_lower"] >= 2]
    flagged.sort(key=lambda f: f["change"])
    flagged_idx = {WEEKDAYS.index(f["weekday"]) for f in flagged}
    others = [abs(v["change"]) for wd, v in per_day.items() if wd not in flagged_idx]

    peak = conn.execute(
        """SELECT CAST(substr(ts, 12, 2) AS INTEGER) AS hour, SUM(amount) FROM transactions
           WHERE shop_id = ? AND substr(ts, 1, 10) BETWEEN ? AND ?
           GROUP BY hour ORDER BY SUM(amount) DESC LIMIT 2""",
        (shop_id, recent_start.isoformat(), as_of.isoformat()),
    ).fetchall()

    return {
        "status": "ok",
        "flagged": flagged,
        "others_max_abs_change": max(others) if others else 0.0,
        "peak_hours": [(h, round(t)) for h, t in peak],
    }
