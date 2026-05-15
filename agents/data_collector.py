import json
from decimal import Decimal
from datetime import date, datetime
from mistralai.client import Mistral
from config import MISTRAL_API_KEY, SUBAGENT_MODEL, SUBAGENT_MAX_TOKENS
from database import get_full_academy_data
from utils import mistral_complete_with_retry
from prompt_loader import load_prompt


def _serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

_DEFAULT_PROMPT = """You are the Data Collection Agent for a badminton academy management system.
You receive raw data extracted directly from the academy's PostgreSQL database and your job is
to interpret, enrich, and structure it into a clear analytical summary.

Database tables:
- transaction: every sale, court booking, and rental transaction (order_id, item_name, category,
  qty, total_sell, total_cost, court, mobile, description, timestamp)
- expense: operational expenses (title, amount, category, timestamp)
- product: inventory items with buy/sell prices and stock levels
- monthly_pass: monthly membership subscriptions (name, mobile, court, slot, amount, start_date, end_date)
- conflict: double-booking conflicts between Playo and Khelomore platforms
- external_profit: miscellaneous revenue not captured in transactions

When analyzing the data:
1. Calculate totals, averages, and trends from the raw numbers
2. Identify patterns in court usage, peak/off-peak times, and revenue mix
3. Flag data quality issues (sparse data, empty tables, etc.) and state confidence levels
4. Note operational issues like booking conflicts, low-margin products, or stock alerts
5. Derive utilization insights from booking patterns and conflict frequency
6. Return ALL financial figures in INR

Return only structured JSON with clear, quantified observations."""

SYSTEM_PROMPT = load_prompt("data_collector", _DEFAULT_PROMPT)


def collect_academy_data(data_categories: list, analysis_depth: str, since_date: str = None) -> dict:
    client = Mistral(api_key=MISTRAL_API_KEY, timeout_ms=300_000)

    print("\n  [DB] Querying live database...", end="", flush=True)
    raw_db_data = get_full_academy_data(since=since_date)
    print(" Done", flush=True)

    period_note = f"Data filtered from: {since_date} to present." if since_date else "Data: all available history."

    user_message = f"""Analyze the following live database extract for a badminton academy.
Requested categories: {data_categories}
Analysis depth: {analysis_depth}
{period_note}

RAW DATABASE DATA:
{json.dumps(raw_db_data, indent=2, default=_serializer)}

Based on this real data, return a comprehensive JSON object:
{{
  "academy_profile": {{
    "data_freshness": "<date range of data>",
    "data_completeness": "<assessment of gaps>",
    "platforms_used": ["Playo", "Khelomore", ...]
  }},
  "revenue_breakdown": {{
    "total_revenue_in_db": <number>,
    "by_category": {{
      "bookings": <number>,
      "product_sales": <number>,
      "rentals": <number>,
      "monthly_passes": <number>,
      "external": <number>
    }},
    "avg_booking_value": <number>,
    "avg_daily_revenue": <number>
  }},
  "utilization_metrics": {{
    "total_bookings": <number>,
    "courts_in_use": [...],
    "peak_hours": [...],
    "low_utilization_slots": [...],
    "booking_conflicts_count": <number>,
    "conflict_resolution_rate_pct": <number>
  }},
  "membership_analysis": {{
    "active_monthly_passes": <number>,
    "monthly_pass_revenue": <number>,
    "pass_utilization": "<assessment>"
  }},
  "product_analysis": {{
    "total_products": <number>,
    "low_margin_products": [...],
    "low_stock_alerts": [...],
    "total_inventory_value": <number>
  }},
  "expense_analysis": {{
    "total_expenses_in_db": <number>,
    "by_category": {{...}},
    "net_profit_in_db": <number>
  }},
  "operational_issues": [...],
  "key_observations": [...]
}}

Be precise with numbers. Note which tables have sparse or zero data and what that implies.
Return ONLY valid JSON, no other text."""

    response = mistral_complete_with_retry(
        client,
        model=SUBAGENT_MODEL,
        max_tokens=SUBAGENT_MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("`").strip()

    try:
        result = json.loads(raw)
        result["_raw_db_snapshot"] = raw_db_data
        return result
    except json.JSONDecodeError:
        return {"raw_analysis": raw, "_raw_db_snapshot": raw_db_data, "error": "Could not parse as JSON"}
