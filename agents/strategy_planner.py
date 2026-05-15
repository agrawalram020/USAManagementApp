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
from config import MISTRAL_API_KEY, SUBAGENT_MODEL, STRATEGY_PLANNER_MAX_TOKENS
from utils import mistral_complete_with_retry
from prompt_loader import load_prompt

_DEFAULT_PROMPT = """You are the Revenue Strategy Planning Agent — a seasoned sports business consultant
who specializes in turning revenue gap analyses into actionable growth strategies for sports academies.

Your strategy framework produces:
1. PRIORITIZED INITIATIVES: Ranked by impact, feasibility, and time-to-revenue
2. IMPLEMENTATION ROADMAP: Month-by-month 12-month plan with milestones
3. INVESTMENT REQUIREMENTS: Capital needed per initiative with ROI projections
4. OPERATIONAL CHANGES: Staff, systems, processes needed
5. RISK ASSESSMENT: What could go wrong and mitigation strategies
6. SUCCESS METRICS: KPIs to track progress for each initiative

Strategy principles you follow:
- Quick wins first (build momentum and fund bigger initiatives)
- Conservative revenue projections (50–70% of theoretical maximum)
- Payback period must be < 12 months for recommended investments
- No initiative should require > ₹5 lakhs upfront without strong ROI evidence
- Human capital changes must be phased (no sudden cost spikes)
- Customer experience must not degrade during growth phase

Output format: Comprehensive JSON with full strategy, roadmap, financials, and KPIs."""

SYSTEM_PROMPT = load_prompt("strategy_planner", _DEFAULT_PROMPT)


def generate_revenue_strategy(
    revenue_gaps: dict,
    academy_data: dict,
    market_data: dict,
    constraints: dict
) -> dict:
    client = Mistral(api_key=MISTRAL_API_KEY, timeout_ms=300_000)

    user_message = f"""Create a comprehensive 12-month revenue growth strategy based on:

REVENUE GAPS IDENTIFIED:
{json.dumps(revenue_gaps, indent=2, default=_serializer)}

ACADEMY DATA:
{json.dumps(academy_data, indent=2, default=_serializer)}

MARKET DATA:
{json.dumps(market_data, indent=2, default=_serializer)}

CONSTRAINTS:
{json.dumps(constraints, indent=2, default=_serializer)}

Return a fully structured JSON strategy:
{{
  "strategy_summary": {{
    "current_monthly_revenue_inr": <number>,
    "projected_monthly_revenue_month_6_inr": <number>,
    "projected_monthly_revenue_month_12_inr": <number>,
    "total_annual_revenue_uplift_inr": <number>,
    "total_investment_required_inr": <number>,
    "blended_roi_percent": <number>,
    "payback_period_months": <number>
  }},
  "strategic_initiatives": [
    {{
      "initiative_id": "INIT-001",
      "name": "<initiative name>",
      "addresses_gaps": ["GAP-001", "..."],
      "description": "<detailed description>",
      "implementation_steps": ["step 1", "step 2", "..."],
      "investment_required_inr": <number>,
      "monthly_revenue_uplift_conservative_inr": <number>,
      "monthly_revenue_uplift_optimistic_inr": <number>,
      "payback_period_months": <number>,
      "roi_12_month_percent": <number>,
      "start_month": <1-12>,
      "completion_month": <1-12>,
      "priority": "P1|P2|P3",
      "complexity": "low|medium|high",
      "required_resources": ["resource 1", "..."],
      "success_kpis": ["kpi 1", "..."],
      "risks": ["risk 1", "..."],
      "risk_mitigation": ["mitigation 1", "..."]
    }}
  ],
  "monthly_roadmap": [
    {{
      "month": 1,
      "month_label": "Month 1 (June 2025)",
      "focus_theme": "<theme>",
      "initiatives_active": ["INIT-001", "..."],
      "key_milestones": ["milestone 1", "..."],
      "expected_revenue_inr": <number>,
      "investment_this_month_inr": <number>,
      "key_actions": ["action 1", "..."]
    }}
  ],
  "financial_projections": {{
    "monthly_revenue_projection": [<m1>, <m2>, ...<m12>],
    "monthly_cost_projection": [<m1>, <m2>, ...<m12>],
    "monthly_profit_projection": [<m1>, <m2>, ...<m12>],
    "cumulative_investment": <number>,
    "break_even_month": <number>
  }},
  "quick_wins_90_days": [
    {{
      "action": "<specific action>",
      "expected_impact": "<impact>",
      "revenue_uplift_inr": <number>,
      "effort": "low|medium",
      "owner": "<who does this>"
    }}
  ],
  "operational_requirements": {{
    "staffing_changes": [...],
    "technology_investments": [...],
    "facility_upgrades": [...],
    "partnerships_to_establish": [...]
  }},
  "risk_register": [
    {{
      "risk": "<risk description>",
      "probability": "low|medium|high",
      "impact": "low|medium|high",
      "mitigation": "<mitigation strategy>"
    }}
  ],
  "success_dashboard": {{
    "monthly_kpis": [...],
    "quarterly_targets": [...],
    "annual_goals": [...]
  }}
}}

Include at least 6 strategic initiatives and all 12 months in the roadmap.
Make financial projections realistic (conservative, not best-case).
Return ONLY valid JSON, no other text."""

    response = mistral_complete_with_retry(
        client,
        model=SUBAGENT_MODEL,
        max_tokens=STRATEGY_PLANNER_MAX_TOKENS,
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
        return _recover_json(raw)


def _recover_json(raw: str) -> dict:
    """Salvage a truncated JSON response by closing any open string/brackets."""
    stack = []       # tracks expected closing chars for '{' and '['
    in_string = False
    escape_next = False

    for ch in raw:
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            if in_string:
                in_string = False
            else:
                in_string = True
            continue
        if in_string:
            continue
        if ch == '{':
            stack.append('}')
        elif ch == '[':
            stack.append(']')
        elif ch in ('}', ']'):
            if stack and stack[-1] == ch:
                stack.pop()

    suffix = ""
    if in_string:
        suffix += '"'   # close open string
    suffix += ''.join(reversed(stack))

    try:
        return json.loads(raw + suffix)
    except json.JSONDecodeError:
        # Try trimming back to the last complete top-level value
        for end in (raw.rfind('}'), raw.rfind(']')):
            if end < 0:
                continue
            try:
                candidate = json.loads(raw[:end + 1])
                if isinstance(candidate, dict):
                    return candidate
            except json.JSONDecodeError:
                pass
        return {"raw_analysis": raw, "error": "Could not parse as JSON"}
