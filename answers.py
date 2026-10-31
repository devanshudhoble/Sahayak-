"""Answers a question using Groq LLM (primary) with keyword fallback."""
import groq_chat


def _hour(h):
    suffix = "pm" if h >= 12 else "am"
    h12 = h % 12 or 12
    return f"{h12} {suffix}"


def _credit_answer(credit):
    if not credit or credit.get("status") != "ok":
        return "Your credit signal needs at least four weeks of sales history before I can score it."
    comps = credit["components"]
    labels = {"consistency": "consistency", "growth": "growth", "frequency": "frequency",
              "adoption": "digital payments", "tenure": "tenure"}
    ranked = sorted(comps.items(), key=lambda kv: kv[1]["score"])
    weakest_key, weakest = ranked[0]
    strongest_key, strongest = ranked[-1]
    return (f"Your credit signal is {round(credit['credit_score'])} out of 100, which is {credit['risk_level']} risk. "
            f"Your strongest area is {labels[strongest_key]} ({strongest['score']}/100). "
            f"The area to work on is {labels[weakest_key]} ({weakest['score']}/100). "
            "This is a prototype signal from your payment history, not a loan offer.")


WEEKDAY_WORDS = {
    "monday": "Monday", "mon": "Monday", "somvar": "Monday",
    "tuesday": "Tuesday", "tue": "Tuesday", "mangalvar": "Tuesday",
    "wednesday": "Wednesday", "wed": "Wednesday", "budhvar": "Wednesday",
    "thursday": "Thursday", "thu": "Thursday", "guruvar": "Thursday",
    "friday": "Friday", "fri": "Friday", "shukravar": "Friday",
    "saturday": "Saturday", "sat": "Saturday", "shanivar": "Saturday",
    "sunday": "Sunday", "sun": "Sunday", "ravivar": "Sunday",
}


def _weekday_in(question):
    words = question.lower().replace("?", " ").replace(",", " ").split()
    for w in words:
        if w in WEEKDAY_WORDS:
            return WEEKDAY_WORDS[w]
    return None


def _day_line(day, info):
    """One plain sentence about a single weekday, from the three-week comparison."""
    pct = round(info["change"] * 100, 1)
    prior = f"₹{info['prior_avg']:,.0f}"
    recent = f"₹{info['recent_avg']:,.0f}"
    if info["change"] <= -0.10 and info["weeks_lower"] >= 2:
        return (f"{day} collections are down {abs(pct)}% over the last three weeks, "
                f"from about {prior} to {recent} on average.")
    sign = "+" if pct >= 0 else ""
    return (f"{day} is not showing a drop. Collections are {sign}{pct}% against the three weeks "
            f"before, from about {prior} to {recent} on average.")


def _day_summary(per_day):
    if not per_day:
        return "none"
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return "; ".join(_day_line(d, per_day[d]) for d in order if d in per_day)


def _keyword_route(question, ctx):
    """Fallback: keyword-based routing when LLM is unavailable."""
    s = question.lower()
    if any(k in s for k in ["credit", "score", "loan", "rating"]):
        return _credit_answer(ctx.get("credit"))
    day = _weekday_in(question)
    if day and ctx.get("per_day") and day in ctx["per_day"]:
        return _day_line(day, ctx["per_day"][day])
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
    if any(k in s for k in ["what can", "help", "who are", "introduce", "kya kar", "madad"]):
        return ("I'm Sahayak, your shop assistant. I watch your daily sales, spot trends, "
                "suggest small experiments, and measure results. You just say yes or no.")
    if any(k in s for k in ["hello", "hi", "namaste", "hey"]):
        return "Namaste! I'm Sahayak. I've been watching your sales data. Ask me anything about your shop's trends."
    if any(k in s for k in ["earn", "today", "kitna", "total", "income", "kamai"]):
        return ("Based on your recent pattern, Thursdays average around ₹8,700. "
                "I don't have today's live data in this prototype, but your overall trend is clear.")
    return ("I can only answer from your sales data right now. Try asking: "
            "Why are Thursday sales down? When is my busiest time? What should I try?")


def answer(question, ctx):
    """ctx holds: explanation, peak, suggestion, decision, measure, note."""
    # Build context for LLM
    peak_text = ""
    if ctx.get("peak") and len(ctx["peak"]) >= 2:
        peak_text = f"{_hour(ctx['peak'][0][0])} and {_hour(ctx['peak'][1][0])}"

    measure_text = "no test run yet"
    if ctx["decision"] == "approved" and ctx.get("measure"):
        m = ctx["measure"]
        sign = "+" if m["change_pct"] >= 0 else ""
        measure_text = f"test ran: {sign}{m['change_pct']}% change"
    elif ctx["decision"] == "skipped":
        measure_text = "owner skipped the test"

    llm_ctx = {
        "explanation": ctx["explanation"],
        "peak_text": peak_text,
        "suggestion": ctx["suggestion"],
        "decision": ctx["decision"],
        "measure_text": measure_text,
        "day_summary": _day_summary(ctx.get("per_day")),
    }

    # Try LLM first
    llm_answer = groq_chat.chat(question, llm_ctx)
    if llm_answer:
        return llm_answer

    # Fallback to keywords
    return _keyword_route(question, ctx)
