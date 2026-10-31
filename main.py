"""End-to-end demo: notice, explain, suggest, decide, measure. Runs on synthetic data."""
import datetime as dt
import os
import sqlite3

import planner
from data_gen import START, SHOP_ID, generate
from explainer import explain
from trend import detect

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sahayak.db")


def main():
    n = generate(DB)
    print(f"Generated {n} synthetic transactions for {SHOP_ID}.\n")

    conn = sqlite3.connect(DB)
    planner.init(conn)

    as_of = START + dt.timedelta(days=41)  # end of six weeks of history
    finding = detect(conn, SHOP_ID, as_of)

    print("NOTICE and EXPLAIN")
    print(explain(finding))
    if finding["status"] != "ok" or not finding["flagged"]:
        return

    print("\nPEAK HOURS (last 3 weeks):", finding["peak_hours"])

    action = planner.propose(conn, SHOP_ID, finding, as_of)
    print("\nSUGGEST")
    print(action["text"])

    print("\nDECIDE: owner taps Approve")
    planner.decide(conn, action["id"], "approve")

    print("\nMEASURE")
    result = planner.measure(conn, SHOP_ID, action["id"])
    if isinstance(result, dict):
        print(f"{result['weekday']}s: ₹{result['test_avg']:,} during the test vs "
              f"₹{result['baseline_avg']:,} in the three weeks before ({result['change_pct']:+}%).")
        print(result["note"])
        print("Caution: the test uplift in this synthetic data is planted, so this shows the flow, not real evidence.")
    else:
        print(result)
    conn.close()


if __name__ == "__main__":
    main()
