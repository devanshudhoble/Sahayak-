"""Answers a question using only the engine's numbers. Keyword routing; no model writes figures."""


def _hour(h):
    suffix = "pm" if h >= 12 else "am"
    h12 = h % 12 or 12
    return f"{h12} {suffix}"


def answer(question, ctx):
    """ctx holds: explanation, peak (list of (hour, amount)), suggestion (text),
    decision (None / 'approved' / 'skipped'), measure (dict or None), note (str)."""
    s = question.lower()
    if any(k in s for k in ["why", "down", "decreas", "drop", "kyun", "kyu", "gir", "kam"]):
        return ctx["explanation"]
    if any(k in s for k in ["busy", "peak", "rush", "when", "kab", "samay", "hour"]):
        (h1, _), (h2, _) = ctx["peak"][0], ctx["peak"][1]
        return f"Your busiest hours in the last three weeks are {_hour(h1)} and {_hour(h2)}, in that order."
    if any(k in s for k in ["result", "measure", "how did", "worked", "test"]):
        if ctx["decision"] == "approved" and ctx.get("measure"):
            m = ctx["measure"]
            sign = "+" if m["change_pct"] >= 0 else ""
            return (f"{m['weekday']}s averaged ₹{m['test_avg']:,} during the test, against "
                    f"₹{m['baseline_avg']:,} in the three weeks before ({sign}{m['change_pct']}%). {m['note']}")
        if ctx["decision"] == "skipped":
            return "You skipped the test, so there is no result."
        return "No test has been approved yet, so there is no result."
    if any(k in s for k in ["try", "suggest", "should", "idea", "what do", "kya"]):
        return ctx["suggestion"] + " Nothing runs until you approve it."
    return ("I can't answer that from your data yet. Ask about why Thursday sales fell, "
            "your busiest time, a suggested test, or the test result.")
