
import random
from datetime import date
import calendar

random.seed(42)

MONTHS = [
    "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03",
    "2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09",
]
REGIONS = ["North", "South", "East", "West"]


CATEGORIES = {
    "Web Design":        (6000, 18000, (0.30, 0.40)),
    "App Development":   (15000, 45000, (0.35, 0.45)),
    "Video Editing":     (2500, 9000,  (0.20, 0.30)),
    "Automation":        (8000, 25000, (0.30, 0.42)),
    "Branding":          (4000, 12000, (0.25, 0.35)),
}

FIRST_NAMES = ["Aarav","Vivaan","Aditya","Ishaan","Kabir","Riya","Ananya","Diya",
               "Meera","Sara","Kunal","Rohan","Neha","Priya","Arjun","Karan",
               "Simran","Tara","Yash","Zara"]
LAST_NAMES = ["Sharma","Verma","Gupta","Kapoor","Nair","Iyer","Reddy","Singh",
              "Chatterjee","Mehta","Malhotra","Bose","Rao","Joshi","Khan"]


def _random_name(rng):
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def _random_day(month_str, rng):
    year, month = map(int, month_str.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    day = rng.randint(1, last_day)
    return date(year, month, day).isoformat()


def populate(conn):
    rng = random.Random(42)
    cur = conn.cursor()

    
    customer_id = 1
    customers_by_month = {m: [] for m in MONTHS}
    for i, month in enumerate(MONTHS):
        new_signups = rng.randint(8 + i, 14 + i)  
        for _ in range(new_signups):
            cur.execute(
                "INSERT INTO customers (customer_id, name, region, signup_month) VALUES (?,?,?,?)",
                (customer_id, _random_name(rng), rng.choice(REGIONS), month),
            )
            customers_by_month[month].append(customer_id)
            customer_id += 1

    all_customers_so_far = []
    active_pool_by_month = {}
    for month in MONTHS:
        all_customers_so_far = all_customers_so_far + customers_by_month[month]
        active_pool_by_month[month] = list(all_customers_so_far)

    
    base_orders = 34
    for i, month in enumerate(MONTHS):
        target_orders = int(base_orders + i * 3.4 + rng.randint(-4, 5))
        pool = active_pool_by_month[month]
      
        for _ in range(target_orders):
            if rng.random() < 0.65 and len(pool) > 5:
                cust = rng.choice(pool)
            else:
                cust = rng.choice(customers_by_month[month] or pool)

            category = rng.choice(list(CATEGORIES.keys()))
            lo, hi, cogs_range = CATEGORIES[category]
            unit_price = round(rng.uniform(lo, hi), -2)  
            cogs_ratio = rng.uniform(*cogs_range)
            unit_cost = round(unit_price * cogs_ratio, 2)
            quantity = rng.choice([1, 1, 1, 2])  

            cur.execute(
                """INSERT INTO orders (customer_id, order_date, category, quantity, unit_price, unit_cost)
                   VALUES (?,?,?,?,?,?)""",
                (cust, _random_day(month, rng), category, quantity, unit_price, unit_cost),
            )


    for month in MONTHS:
        new_count = len(customers_by_month[month])
        spend = round(new_count * rng.uniform(2800, 3600) + rng.uniform(5000, 15000), 2)
        cur.execute("INSERT INTO marketing_spend (month, spend) VALUES (?,?)", (month, spend))

    conn.commit()
