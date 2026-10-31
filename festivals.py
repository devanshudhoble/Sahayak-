"""Festive season detection and year-over-year comparison."""
import datetime as dt
from trend import daily_totals

# Major Indian festivals with approximate dates (varies yearly)
FESTIVALS = [
    {"name": "Makar Sankranti", "month": 1, "day": 14, "window": 3},
    {"name": "Republic Day", "month": 1, "day": 26, "window": 2},
    {"name": "Holi", "month": 3, "day": 14, "window": 5},
    {"name": "Ram Navami", "month": 4, "day": 6, "window": 3},
    {"name": "Eid", "month": 4, "day": 10, "window": 5},
    {"name": "Independence Day", "month": 8, "day": 15, "window": 2},
    {"name": "Raksha Bandhan", "month": 8, "day": 28, "window": 4},
    {"name": "Janmashtami", "month": 9, "day": 6, "window": 3},
    {"name": "Ganesh Chaturthi", "month": 9, "day": 17, "window": 5},
    {"name": "Navratri", "month": 10, "day": 3, "window": 9},
    {"name": "Dussehra", "month": 10, "day": 12, "window": 3},
    {"name": "Diwali", "month": 10, "day": 29, "window": 7},
    {"name": "Bhai Dooj", "month": 11, "day": 3, "window": 2},
    {"name": "Christmas", "month": 12, "day": 25, "window": 5},
    {"name": "New Year", "month": 12, "day": 31, "window": 3},
]


def upcoming_festival(as_of: dt.date, lookahead_days: int = 14):
    """Find the next festival within lookahead_days."""
    for f in FESTIVALS:
        fest_date = dt.date(as_of.year, f["month"], f["day"])
        days_until = (fest_date - as_of).days
        if 0 <= days_until <= lookahead_days:
            return {
                "name": f["name"],
                "date": fest_date.isoformat(),
                "days_until": days_until,
                "window": f["window"],
            }
    return None


def festive_comparison(conn, shop_id, as_of: dt.date):
    """Compare current period with same period last year if a festival is near."""
    fest = upcoming_festival(as_of)
    if not fest:
        return None

    window = fest["window"]
    fest_date = dt.date.fromisoformat(fest["date"])

    # This year: week around the festival
    this_start = fest_date - dt.timedelta(days=window)
    this_end = fest_date + dt.timedelta(days=window)

    # Last year: same calendar period
    last_start = this_start.replace(year=this_start.year - 1)
    last_end = this_end.replace(year=this_end.year - 1)

    # Get totals (may not have last year data in prototype — simulate)
    try:
        this_totals = daily_totals(conn, shop_id, max(this_start, as_of - dt.timedelta(days=60)), min(this_end, as_of))
        this_sum = sum(this_totals.values()) or 1

        # Simulate last year data (in production, real historical data)
        # For prototype: estimate last year as 2.5x normal during festival
        normal_daily = this_sum / max(len(this_totals), 1)
        last_year_estimated = normal_daily * 2.5 * (window * 2)
    except Exception:
        return None

    return {
        "festival": fest["name"],
        "date": fest["date"],
        "days_until": fest["days_until"],
        "last_year_estimated_total": round(last_year_estimated),
        "this_year_so_far": round(this_sum),
        "multiplier": 2.5,
        "advice": _festival_advice(fest["name"], fest["days_until"], window),
    }


def _festival_advice(name, days_until, window):
    """Generate festival-specific advice."""
    if days_until <= 2:
        return f"{name} is in {days_until} days! Last year sales were ~2.5x normal. Make sure you have extra stock ready."
    elif days_until <= 7:
        return f"{name} is coming in {days_until} days. Last year this period saw 2.5x sales. Start stocking up NOW — don't wait till last day."
    else:
        return f"{name} is {days_until} days away. Based on last year's pattern, expect 2-3x normal sales. Start planning your stock and offers."
