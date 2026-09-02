"""Makes the example data: a small shop, June to August 2026, and the August file loaded twice."""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(7)
here = Path(__file__).parent

customers = [(i, random.choice(["PT", "ES", "FR", "DE"])) for i in range(1, 401)]
with open(here / "customers.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["customer_id", "country"])
    w.writerows(customers)

orders = []
order_id = 5000
for month in (6, 7, 8):
    days = 30 if month == 6 else 31
    for _ in range(random.randint(1150, 1250)):
        order_id += 1
        day = date(2026, month, random.randint(1, days))
        orders.append(
            (
                order_id,
                random.choice(customers)[0],
                random.choice([10, 15, 20, 35, 50, 80, 120]),
                day.isoformat(),
                random.choice(["paid", "paid", "paid", "fulfilled", "cancelled"]),
                f"orders_{month:02d}.csv",
            )
        )

august = [o for o in orders if o[3].startswith("2026-08")]
orders += august

with open(here / "orders.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["order_id", "customer_id", "amount", "ordered_at", "status", "file_id"])
    w.writerows(orders)

print(f"{len(customers)} customers, {len(orders)} order rows, {len(august)} of them are the August file again")
