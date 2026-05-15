import json
from decimal import Decimal
from datetime import date, datetime
from mistralai.client import Mistral


def _serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
from config import MISTRAL_API_KEY, SUBAGENT_MODEL, SUBAGENT_MAX_TOKENS
from utils import mistral_complete_with_retry
from prompt_loader import load_prompt

_DEFAULT_PROMPT = """You are the Revenue Gap Analysis Agent — a specialist in sports facility economics
and revenue optimization. You receive raw academy data and market intelligence and identify
specific, quantified revenue gaps with financial precision.

Your analysis framework:
1. UTILIZATION GAPS: Compare actual vs potential court-hour revenue
2. PRICING GAPS: Compare academy pricing vs market benchmarks
3. PROGRAM GAPS: Identify missing revenue-generating programs
4. SEGMENT GAPS: Customer segments present in market but absent from academy
5. OPERATIONAL GAPS: Inefficiencies costing or limiting revenue
6. PARTNERSHIP GAPS: Corporate/institutional relationships not leveraged

For each gap, you MUST provide:
- Gap name and category
- Current state (revenue/metric)
- Benchmark/potential state
- Monthly revenue gap (INR)
- Confidence level (high/medium/low)
- Key evidence supporting the gap
- Quick-win vs long-term classification

Always be conservative but realistic with estimates. Use triangulation from multiple
data points. Show your calculations clearly in the JSON output.

Output format must be a structured JSON with all gaps quantified."""

SYSTEM_PROMPT = load_prompt("revenue_analyzer", _DEFAULT_PROMPT)


def identify_revenue_gaps(academy_data: dict, market_data: dict, gap_categories: list) -> dict:
    client = Mistral(api_key=MISTRAL_API_KEY, timeout_ms=300_000)

    user_message = f"""Perform a rigorous revenue gap analysis using the following data.

ACADEMY DATA:
{json.dumps(academy_data, indent=2, default=_serializer)}

MARKET DATA:
{json.dumps(market_data, indent=2, default=_serializer)}

Analyze gaps in these categories: {gap_categories}

Return a comprehensive JSON object structured as:
{{
  "executive_summary": {{
    "current_monthly_revenue": <number>,
    "total_identified_gap_low": <number>,
    "total_identified_gap_high": <number>,
    "revenue_uplift_potential_percent": <number>,
    "number_of_gaps_identified": <number>
  }},
  "revenue_gaps": [
    {{
      "gap_id": "GAP-001",
      "name": "<gap name>",
      "category": "<category>",
      "current_monthly_revenue_inr": <number>,
      "potential_monthly_revenue_inr_low": <number>,
      "potential_monthly_revenue_inr_high": <number>,
      "gap_amount_inr_low": <number>,
      "gap_amount_inr_high": <number>,
      "confidence": "high|medium|low",
      "calculation_basis": "<how you calculated this>",
      "evidence": ["<evidence 1>", "<evidence 2>"],
      "type": "quick_win|medium_term|long_term",
      "priority_rank": <1-10>,
      "implementation_complexity": "low|medium|high"
    }}
  ],
  "gap_summary_by_category": {{...}},
  "top_3_priority_gaps": [...],
  "quick_wins": [...],
  "total_gap_analysis": {{...}}
}}

Identify at least 6 specific revenue gaps. Be precise with calculations.
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
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_analysis": raw, "error": "Could not parse as JSON"}
