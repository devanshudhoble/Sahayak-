"""Test planner and approval. Rules set the cap and duration; the owner decides whether a test runs."""
import datetime as dt

from trend import WEEKDAYS, daily_totals

MAX_CAP = 1500  # rule: no suggestion may exceed this, whatever the owner asks for


def init(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY,
        shop_id TEXT NOT NULL,
        weekday TEXT NOT NULL,
        suggestion TEXT NOT NULL,
        budget_cap REAL NOT NULL,
        test_start TEXT NOT NULL,
        test_end TEXT NOT NULL,
        status TEXT NOT NULL)""")
    conn.commit()


def propose(conn, shop_id, finding, as_of, cap=1000):
    day = finding["flagged"][0]["weekday"]
    cap = min(cap, MAX_CAP)
    test_start = as_of + dt.timedelta(days=1)
    test_end = as_of + dt.timedelta(days=21)  # three weeks, so three of that weekday
    text = f"Try a tea-and-snacks bundle offer on {day}s for three weeks. Maximum budget ₹{cap:,}."
    cur = conn.execute(
        """INSERT INTO actions (shop_id, weekday, suggestion, budget_cap, test_start, test_end, status)
           VALUES (?, ?, ?, ?, ?, ?, 'proposed')""",
        (shop_id, day, text, cap, test_start.isoformat(), test_end.isoformat()),
    )
    conn.commit()
    return {"id": cur.lastrowid, "text": text, "budget_cap": cap}


def decide(conn, action_id, decision, new_cap=None):
    """The owner's decision. Nothing runs unless the status becomes 'approved'."""
    if decision == "approve":
        conn.execute("UPDATE actions SET status = 'approved' WHERE id = ?", (action_id,))
    elif decision == "change":
        cap = min(new_cap, MAX_CAP)
        conn.execute("UPDATE actions SET budget_cap = ?, status = 'approved' WHERE id = ?", (cap, action_id))
    elif decision == "skip":
        conn.execute("UPDATE actions SET status = 'skipped' WHERE id = ?", (action_id,))
    else:
        raise ValueError(f"unknown decision: {decision}")
    conn.commit()


def _avg_on_weekday(conn, shop_id, start, end, wd):
    totals = daily_totals(conn, shop_id, start, end)
    vals = [v for d, v in totals.items() if d.weekday() == wd]
    return sum(vals) / len(vals)


def measure(conn, shop_id, action_id):
    row = conn.execute(
        "SELECT weekday, test_start, test_end, status FROM actions WHERE id = ?", (action_id,)
    ).fetchone()
    if row is None:
        return "No such action."
    weekday, t_start, t_end, status = row
    if status != "approved":
        return "No result: the owner has not approved this test, so nothing was run."

    wd = WEEKDAYS.index(weekday)
    ts = dt.date.fromisoformat(t_start)
    te = dt.date.fromisoformat(t_end)
    base = _avg_on_weekday(conn, shop_id, ts - dt.timedelta(days=21), ts - dt.timedelta(days=1), wd)
    test = _avg_on_weekday(conn, shop_id, ts, te, wd)
    change = (test - base) / base
    return {
        "weekday": weekday,
        "baseline_avg": round(base),
        "test_avg": round(test),
        "change_pct": round(change * 100, 1),
        "note": "Sales only. Profit and actual spend are not measured in this prototype.",
    }
