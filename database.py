import psycopg2
import psycopg2.extras
from config import DATABASE_URL

SCHEMA = "usam"


def _connect():
    return psycopg2.connect(DATABASE_URL)


def _rows(cur) -> list[dict]:
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _w(since: str | None, existing: bool = False) -> str:
    """Return a WHERE / AND timestamp filter clause, or empty string."""
    if not since:
        return ""
    kw = "AND" if existing else "WHERE"
    return f" {kw} timestamp >= '{since}'"


def get_transaction_summary(since: str = None) -> dict:
    conn = _connect()
    cur = conn.cursor()

    sf = _w(since)
    sf_booking = _w(since, existing=True)

    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.transaction{sf}")
    total_rows = cur.fetchone()[0]

    cur.execute(f"""
        SELECT
            category,
            COUNT(*)                                        AS count,
            SUM(total_sell)                                 AS total_revenue,
            SUM(total_cost)                                 AS total_cost,
            SUM(total_sell - COALESCE(total_cost, 0))       AS gross_profit,
            ROUND(AVG(total_sell), 0)                       AS avg_transaction_value
        FROM {SCHEMA}.transaction
        WHERE (status = 'Completed' OR status IS NULL){sf_booking}
        GROUP BY category
        ORDER BY total_revenue DESC
    """)
    by_category = _rows(cur)

    cur.execute(f"""
        SELECT
            court,
            COUNT(*)        AS bookings,
            SUM(total_sell) AS revenue
        FROM {SCHEMA}.transaction
        WHERE category = 'Booking'{sf_booking}
        GROUP BY court
        ORDER BY court
    """)
    by_court = _rows(cur)

    cur.execute(f"""
        SELECT
            DATE_TRUNC('month', timestamp)::date    AS month,
            SUM(total_sell)                         AS revenue,
            SUM(total_cost)                         AS cost,
            COUNT(*)                                AS transactions
        FROM {SCHEMA}.transaction{sf}
        GROUP BY 1
        ORDER BY 1
    """)
    by_month = _rows(cur)

    cur.execute(f"""
        SELECT
            item_name,
            category,
            SUM(qty)            AS units_sold,
            SUM(total_sell)     AS revenue,
            SUM(total_cost)     AS cost,
            SUM(total_sell - COALESCE(total_cost, 0)) AS gross_profit
        FROM {SCHEMA}.transaction{sf}
        GROUP BY item_name, category
        ORDER BY revenue DESC
        LIMIT 20
    """)
    by_item = _rows(cur)

    cur.execute(f"""
        SELECT
            EXTRACT(HOUR FROM timestamp) AS hour,
            COUNT(*)            AS count,
            SUM(total_sell)     AS revenue
        FROM {SCHEMA}.transaction
        WHERE category = 'Booking'{sf_booking}
        GROUP BY 1
        ORDER BY 1
    """)
    by_hour = _rows(cur)

    cur.execute(f"""
        SELECT
            TO_CHAR(timestamp, 'Day')   AS day_of_week,
            COUNT(*)                    AS count,
            SUM(total_sell)             AS revenue
        FROM {SCHEMA}.transaction
        WHERE category = 'Booking'{sf_booking}
        GROUP BY 1
        ORDER BY MIN(EXTRACT(DOW FROM timestamp))
    """)
    by_day = _rows(cur)

    cur.execute(f"""
        SELECT
            created_by,
            COUNT(*)            AS transactions,
            SUM(total_sell)     AS revenue_collected
        FROM {SCHEMA}.transaction{sf}
        GROUP BY created_by
        ORDER BY revenue_collected DESC
    """)
    by_staff = _rows(cur)

    cur.close()
    conn.close()

    return {
        "total_transaction_rows": total_rows,
        "by_category": by_category,
        "by_court": by_court,
        "by_month": by_month,
        "by_item_top20": by_item,
        "by_hour_of_day": by_hour,
        "by_day_of_week": by_day,
        "by_staff": by_staff,
    }


def get_expense_summary(since: str = None) -> dict:
    conn = _connect()
    cur = conn.cursor()

    sf = _w(since)
    sf_and = _w(since, existing=True)

    cur.execute(f"SELECT COUNT(*), SUM(amount), AVG(amount) FROM {SCHEMA}.expense{sf}")
    row = cur.fetchone()
    totals = {
        "count": row[0],
        "total_amount": row[1],
        "avg_amount": float(row[2]) if row[2] else 0
    }

    cur.execute(f"""
        SELECT category, COUNT(*) AS count, SUM(amount) AS total
        FROM {SCHEMA}.expense{sf}
        GROUP BY category
        ORDER BY total DESC
    """)
    by_category = _rows(cur)

    cur.execute(f"""
        SELECT
            DATE_TRUNC('month', timestamp)::date AS month,
            SUM(amount) AS total
        FROM {SCHEMA}.expense{sf}
        GROUP BY 1
        ORDER BY 1
    """)
    by_month = _rows(cur)

    cur.execute(f"SELECT * FROM {SCHEMA}.expense{sf} ORDER BY timestamp")
    all_expenses = _rows(cur)

    cur.close()
    conn.close()
    return {
        "totals": totals,
        "by_category": by_category,
        "by_month": by_month,
        "all_expenses": all_expenses
    }


def get_product_inventory() -> dict:
    conn = _connect()
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM {SCHEMA}.product ORDER BY category, name")
    products = _rows(cur)

    cur.execute(f"""
        SELECT
            category,
            name,
            buy_price,
            sell_price,
            sell_price - buy_price                                          AS margin,
            ROUND(((sell_price - buy_price)::numeric / NULLIF(buy_price, 0)) * 100, 1) AS margin_pct,
            stock,
            low_stock_limit,
            CASE WHEN stock <= low_stock_limit THEN true ELSE false END     AS low_stock_alert
        FROM {SCHEMA}.product
        ORDER BY category, name
    """)
    margin_analysis = _rows(cur)

    cur.close()
    conn.close()
    return {"products": products, "margin_analysis": margin_analysis}


def get_monthly_pass_summary(since: str = None) -> dict:
    conn = _connect()
    cur = conn.cursor()

    sf = f" WHERE start_date >= '{since}'" if since else ""
    sf_and = f" AND start_date >= '{since}'" if since else ""

    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.monthly_pass{sf}")
    total = cur.fetchone()[0]

    cur.execute(f"""
        SELECT
            COUNT(*)        AS count,
            SUM(amount)     AS total_revenue,
            AVG(amount)     AS avg_amount,
            MIN(start_date) AS earliest,
            MAX(end_date)   AS latest
        FROM {SCHEMA}.monthly_pass{sf}
    """)
    summary = _rows(cur)[0]

    cur.execute(f"""
        SELECT payment_type, COUNT(*) AS count, SUM(amount) AS revenue
        FROM {SCHEMA}.monthly_pass{sf}
        GROUP BY payment_type
        ORDER BY revenue DESC
    """)
    by_payment = _rows(cur)

    cur.execute(f"""
        SELECT slot, COUNT(*) AS count, SUM(amount) AS revenue
        FROM {SCHEMA}.monthly_pass{sf}
        GROUP BY slot
        ORDER BY count DESC
    """)
    by_slot = _rows(cur)

    cur.execute(f"SELECT * FROM {SCHEMA}.monthly_pass{sf} ORDER BY start_date")
    all_passes = _rows(cur)

    cur.close()
    conn.close()
    return {
        "total_passes": total,
        "summary": summary,
        "by_payment_type": by_payment,
        "by_slot": by_slot,
        "all_passes": all_passes
    }


def get_external_profit_summary(since: str = None) -> dict:
    conn = _connect()
    cur = conn.cursor()

    sf = _w(since)

    cur.execute(f"SELECT COUNT(*), SUM(amount) FROM {SCHEMA}.external_profit{sf}")
    row = cur.fetchone()

    cur.execute(f"""
        SELECT
            source,
            COUNT(*)        AS entries,
            SUM(amount)     AS total_revenue,
            AVG(amount)     AS avg_per_entry,
            MIN(timestamp)  AS first_entry,
            MAX(timestamp)  AS last_entry
        FROM {SCHEMA}.external_profit{sf}
        GROUP BY source
        ORDER BY total_revenue DESC
    """)
    by_source = _rows(cur)

    cur.execute(f"""
        SELECT
            DATE_TRUNC('month', timestamp)::date AS month,
            source,
            SUM(amount) AS revenue
        FROM {SCHEMA}.external_profit{sf}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)
    by_month = _rows(cur)

    cur.execute(f"SELECT * FROM {SCHEMA}.external_profit{sf} ORDER BY timestamp")
    all_records = _rows(cur)

    cur.close()
    conn.close()
    return {
        "total_records": row[0],
        "total_amount": row[1],
        "by_source": by_source,
        "by_month": by_month,
        "all_records": all_records
    }


def get_coaching_summary(since: str = None) -> dict:
    conn = _connect()
    cur = conn.cursor()

    sf_ts = _w(since)
    sf_start = f" WHERE start_date >= '{since}'" if since else ""

    cur.execute(f"SELECT * FROM {SCHEMA}.coaching_batch{sf_ts} ORDER BY timestamp")
    batches = _rows(cur)

    cur.execute(f"""
        SELECT
            COUNT(*)        AS total_students,
            SUM(fees)       AS total_fees,
            AVG(fees)       AS avg_fees,
            MIN(start_date) AS earliest_start,
            MAX(end_date)   AS latest_end
        FROM {SCHEMA}.coaching_student{sf_start}
    """)
    student_summary = _rows(cur)[0]

    cur.execute(f"SELECT * FROM {SCHEMA}.coaching_student{sf_start} ORDER BY start_date")
    students = _rows(cur)

    cur.close()
    conn.close()
    return {
        "batches": batches,
        "student_summary": student_summary,
        "students": students
    }


def get_accounts_summary(since: str = None) -> dict:
    conn = _connect()
    cur = conn.cursor()

    sf = _w(since)

    cur.execute(f"SELECT * FROM {SCHEMA}.accounts ORDER BY type, name")
    accounts = _rows(cur)

    cur.execute(f"""
        SELECT
            account,
            type,
            COUNT(*)        AS entries,
            SUM(amount)     AS total_amount
        FROM {SCHEMA}.staff_ledger{sf}
        GROUP BY account, type
        ORDER BY total_amount DESC
    """)
    ledger_by_account = _rows(cur)

    cur.execute(f"""
        SELECT
            DATE_TRUNC('month', timestamp)::date AS month,
            type,
            SUM(amount) AS amount
        FROM {SCHEMA}.staff_ledger{sf}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)
    ledger_by_month = _rows(cur)

    cur.execute(f"SELECT * FROM {SCHEMA}.staff_ledger{sf} ORDER BY timestamp")
    all_ledger = _rows(cur)

    cur.close()
    conn.close()
    return {
        "accounts": accounts,
        "ledger_by_account": ledger_by_account,
        "ledger_by_month": ledger_by_month,
        "all_ledger": all_ledger
    }


def get_conflict_analysis() -> dict:
    conn = _connect()
    cur = conn.cursor()

    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.conflict")
    total = cur.fetchone()[0]

    cur.execute(f"""
        SELECT
            COUNT(*)                                                            AS total,
            SUM(CASE WHEN resolved = true THEN 1 ELSE 0 END)                   AS resolved,
            SUM(CASE WHEN resolved = false OR resolved IS NULL THEN 1 ELSE 0 END) AS unresolved
        FROM {SCHEMA}.conflict
    """)
    resolution = _rows(cur)[0]

    cur.execute(f"""
        SELECT court, COUNT(*) AS conflicts
        FROM {SCHEMA}.conflict
        GROUP BY court
        ORDER BY conflicts DESC
    """)
    by_court = _rows(cur)

    cur.close()
    conn.close()
    return {
        "total_conflicts": total,
        "resolution_status": resolution,
        "by_court": by_court,
    }


def get_full_academy_data(since: str = None) -> dict:
    return {
        "transactions": get_transaction_summary(since=since),
        "expenses": get_expense_summary(since=since),
        "products": get_product_inventory(),
        "monthly_passes": get_monthly_pass_summary(since=since),
        "external_profit": get_external_profit_summary(since=since),
        "coaching": get_coaching_summary(since=since),
        "accounts_and_ledger": get_accounts_summary(since=since),
        "booking_conflicts": get_conflict_analysis(),
    }
