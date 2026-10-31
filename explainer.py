"""Turns the detector's numbers into plain words. It states what the data shows and what it cannot show."""


def explain(finding):
    if finding["status"] != "ok":
        return ("Not enough history yet. Sahayak needs about six weeks of payments "
                "before it describes trends.")
    if not finding["flagged"]:
        return "No weekday has dropped by 10% or more over the last three weeks."

    f = finding["flagged"][0]
    day = f["weekday"]
    pct = abs(f["change"]) * 100
    lines = [f"{day} collections are down {pct:.0f}% over the last three weeks, "
             f"compared with the three weeks before."]
    if finding["others_max_abs_change"] <= 0.08:
        lines.append(f"Other weekdays are within 8% of their usual level, so the drop is specific to {day}s.")
    else:
        lines.append("Other weekdays have changed too, so the drop may not be specific to one day.")
    lines.append("The data shows the drop, not the cause.")
    lines.append(f"Did your {day} opening hours, stock or staffing change?")
    return " ".join(lines)
