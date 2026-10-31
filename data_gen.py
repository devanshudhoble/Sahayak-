"""Synthetic payment data for one demo shop. This is NOT real Paytm data."""
import datetime as dt
import random
import sqlite3

START = dt.date(2026, 9, 7)  # a Monday
WEEKS = 9                    # 6 weeks of history + 3 weeks during a test
SHOP_ID = "demo-kirana"

# Typical daily collections in rupees, Monday=0 ... Sunday=6
BASE_DAILY = [9000, 8000, 8500, 10000, 11000, 13000, 12000]

# Thursday's weekly multiplier: gradual decline for 6 weeks, then a simulated test period
THU_FACTOR = [1.00, 0.98, 0.95, 0.90, 0.85, 0.80,   # history (planted dip)
              0.98, 1.05, 1.08]                      # during a test (planted uplift, simulated)

HOUR_WEIGHTS = {8: 1, 9: 1, 10: 2, 11: 2, 12: 3, 13: 3, 14: 2, 15: 2,
                16: 3, 17: 4, 18: 5, 19: 6, 20: 6, 21: 4}


def generate(db_path: str, seed: int = 7) -> int:
    rng = random.Random(seed)
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS transactions")
    conn.execute("""CREATE TABLE transactions (
        id INTEGER PRIMARY KEY,
        shop_id TEXT NOT NULL,
        ts TEXT NOT NULL,
        amount REAL NOT NULL)""")
    hours, weights = zip(*HOUR_WEIGHTS.items())
    rows = []
    for day_i in range(WEEKS * 7):
        day = START + dt.timedelta(days=day_i)
        wd = day.weekday()
        week = day_i // 7
        total = BASE_DAILY[wd] * rng.uniform(0.93, 1.07)
        if wd == 3:  # Thursday
            total *= THU_FACTOR[week]
        n = max(3, round(total / 350))
        amounts = [rng.uniform(100, 600) for _ in range(n)]
        scale = total / sum(amounts)
        for a in amounts:
            hour = rng.choices(hours, weights)[0]
            minute = rng.randrange(60)
            ts = dt.datetime.combine(day, dt.time(hour, minute)).isoformat(timespec="minutes")
            rows.append((SHOP_ID, ts, round(a * scale, 2)))
    conn.executemany("INSERT INTO transactions (shop_id, ts, amount) VALUES (?, ?, ?)", rows)
    conn.commit()
    conn.close()
    return len(rows)
