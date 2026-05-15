import json
import os
from decimal import Decimal
from datetime import date, datetime, timedelta
from mistralai.client import Mistral


def _serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
from config import MISTRAL_API_KEY, ORCHESTRATOR_MODEL, ORCHESTRATOR_MAX_TOKENS, MAX_ITERATIONS
from tools.tool_definitions import ORCHESTRATOR_TOOLS
from agents.data_collector import collect_academy_data
from agents.market_researcher import analyze_market
from agents.revenue_analyzer import identify_revenue_gaps
from agents.strategy_planner import generate_revenue_strategy
from utils import mistral_complete_with_retry
from prompt_loader import load_prompt

_DEFAULT_ORCHESTRATOR_SYSTEM = """You are the Chief Revenue Strategy Orchestrator for a badminton academy consulting engagement.
Your mission: identify revenue gaps and create a comprehensive growth plan for Unity Shuttle Arena
located at Hirai Sitai Road, Hinjavadi Phase 1, Pune, PIN-411057.

You coordinate four specialized subagents through tool calls:
1. collect_academy_data — gathers internal academy metrics, utilization, revenue, and demographics
2. analyze_market — researches competitors, pricing benchmarks, and market opportunities
3. identify_revenue_gaps — cross-references academy vs market data to find and quantify gaps
4. generate_revenue_strategy — creates a prioritized 12-month implementation roadmap

WORKFLOW:
Step 1: Call collect_academy_data with all relevant categories at 'comprehensive' depth
Step 2: Call analyze_market with all focus areas, passing academy context from step 1
Step 3: Call identify_revenue_gaps passing results from steps 1 and 2
Step 4: Call generate_revenue_strategy passing all previous results with 'balanced' priority

After all tool calls complete, synthesize findings into a clear, executive-level report with:
- Current revenue snapshot
- Top revenue gaps with INR amounts
- Prioritized strategic initiatives
- 12-month revenue trajectory
- Immediate next steps (first 30 days)

Be thorough but crisp. Use headers and structure your final report clearly."""

ORCHESTRATOR_SYSTEM = load_prompt("orchestrator", _DEFAULT_ORCHESTRATOR_SYSTEM)

PERIOD_DAYS = {"1y": 365, "6m": 183, "1m": 30}
PERIOD_LABELS = {"1y": "Last 12 Months", "6m": "Last 6 Months", "1m": "Last Month"}


def _compute_since_date(period: str) -> str:
    days = PERIOD_DAYS.get(period, 365)
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def run_revenue_analysis(period: str = "1y"):
    since_date = _compute_since_date(period)
    period_label = PERIOD_LABELS.get(period, "Last 12 Months")

    REQUIRED_TOOLS = ["collect_academy_data", "analyze_market", "identify_revenue_gaps", "generate_revenue_strategy"]

    def _slim(result: dict) -> dict:
        """Return a copy of the result without the raw DB snapshot (too large for message history)."""
        if isinstance(result, dict):
            return {k: v for k, v in result.items() if k != "_raw_db_snapshot"}
        return result

    def process_tool_call(tool_name: str, tool_input: dict) -> dict:
        print(f"\n  [Tool: {tool_name}]", end="", flush=True)
        if tool_name == "collect_academy_data":
            result = collect_academy_data(
                data_categories=tool_input.get("data_categories", []),
                analysis_depth=tool_input.get("analysis_depth", "comprehensive"),
                since_date=since_date,
            )
        elif tool_name == "analyze_market":
            result = analyze_market(
                focus_areas=tool_input.get("focus_areas", []),
                academy_context=tool_input.get("academy_context", {})
            )
        elif tool_name == "identify_revenue_gaps":
            # Always use the authoritative collected results — the model may pass empty dicts
            result = identify_revenue_gaps(
                academy_data=collected_results.get("collect_academy_data", tool_input.get("academy_data", {})),
                market_data=collected_results.get("analyze_market", tool_input.get("market_data", {})),
                gap_categories=tool_input.get("gap_categories", [])
            )
        elif tool_name == "generate_revenue_strategy":
            # Always use the authoritative collected results
            result = generate_revenue_strategy(
                revenue_gaps=collected_results.get("identify_revenue_gaps", tool_input.get("revenue_gaps", {})),
                academy_data=collected_results.get("collect_academy_data", tool_input.get("academy_data", {})),
                market_data=collected_results.get("analyze_market", tool_input.get("market_data", {})),
                constraints=tool_input.get("constraints", {})
            )
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        print(" Done", flush=True)
        return result

    client = Mistral(api_key=MISTRAL_API_KEY, timeout_ms=300_000)

    print("=" * 70)
    print(f"UNITY SHUTTLE ARENA — REVENUE GAP & GROWTH STRATEGY ANALYSIS")
    print(f"Period: {period_label}  (from {since_date})")
    print("=" * 70)
    print()

    initial_prompt = f"""Conduct a complete revenue gap analysis and strategic growth planning session for
Unity Shuttle Arena, Hirai Sitai Road, Hinjavadi Phase 1, Pune, PIN-411057.

Analysis period: {period_label} (data from {since_date} to present).

Use all available tools in sequence to:
1. Collect comprehensive internal academy data for this period
2. Research the local market, competitors, and opportunities
3. Identify and quantify all revenue gaps
4. Generate a prioritized 12-month revenue growth strategy

After completing all analysis, provide a clear executive summary with specific recommendations
and financial projections."""

    messages = [
        {"role": "system", "content": ORCHESTRATOR_SYSTEM},
        {"role": "user", "content": initial_prompt},
    ]
    iteration = 0
    collected_results = {}

    while iteration < MAX_ITERATIONS:
        iteration += 1

        response = mistral_complete_with_retry(
            client,
            model=ORCHESTRATOR_MODEL,
            messages=messages,
            tools=ORCHESTRATOR_TOOLS,
            max_tokens=ORCHESTRATOR_MAX_TOKENS,
        )

        finish_reason = response.choices[0].finish_reason
        assistant_msg = response.choices[0].message

        if assistant_msg.content:
            print(assistant_msg.content, flush=True)

        if finish_reason == "stop":
            missing = [t for t in REQUIRED_TOOLS if t not in collected_results]
            if missing:
                # Model stopped early before all required tools ran — nudge it to continue
                print(f"\n  [Orchestrator] Model stopped early. Missing tools: {missing}. Continuing…")
                messages.append({
                    "role": "user",
                    "content": (
                        f"You have not yet called: {missing}. "
                        "Please continue the analysis by calling the remaining tools now."
                    ),
                })
                continue
            # Save the final executive narrative so the report generator can include it
            if assistant_msg.content and assistant_msg.content.strip():
                collected_results["orchestrator_summary"] = assistant_msg.content.strip()
            print("\n")
            break

        if finish_reason != "tool_calls":
            print(f"\n[Stopped: {finish_reason}]")
            break

        # Append the assistant's tool-call message
        messages.append({
            "role": "assistant",
            "content": assistant_msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in assistant_msg.tool_calls
            ],
        })

        # Execute each tool and append results (skip duplicate tool names)
        seen = set()
        for tc in assistant_msg.tool_calls:
            tool_input = json.loads(tc.function.arguments)
            if tc.function.name in seen:
                content = json.dumps({"info": "duplicate call skipped"})
            else:
                seen.add(tc.function.name)
                result = process_tool_call(tc.function.name, tool_input)
                collected_results[tc.function.name] = result
                # Strip raw DB snapshot before adding to message history to keep context lean
                content = json.dumps(_slim(result), ensure_ascii=False, default=_serializer)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": content,
            })

    print("\n" + "=" * 70)
    print("Analysis complete.")
    print("=" * 70)

    os.makedirs("output", exist_ok=True)
    collected_results["_generated_at"] = datetime.now().isoformat()
    collected_results["_period"] = period
    collected_results["_period_label"] = period_label
    collected_results["_since_date"] = since_date
    with open("output/analysis.json", "w", encoding="utf-8") as f:
        json.dump(collected_results, f, ensure_ascii=False, default=_serializer, indent=2)
    print("[Results saved to output/analysis.json]", flush=True)
