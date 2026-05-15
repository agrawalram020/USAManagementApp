"""
Revenue Agent Blueprint — all /agent/* routes.
Mount in app.py with:
    from agent_routes import agent_bp
    app.register_blueprint(agent_bp)
"""

import os
import json
import threading
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint, render_template, request, jsonify,
    session, redirect, url_for, Response, send_file,
)

# ── Lazy imports (app still starts if MISTRAL_API_KEY is absent) ──────────
try:
    from config import MISTRAL_API_KEY, SUBAGENT_MODEL
    from utils import mistral_complete_with_retry
    from mistralai.client import Mistral
    from prompt_loader import load_prompt, save_prompt, list_prompts
    from generate_report import generate_report
    _AGENT_AVAILABLE = True
except Exception as _e:
    MISTRAL_API_KEY = None
    SUBAGENT_MODEL = "mistral-small-latest"
    _AGENT_AVAILABLE = False
    def load_prompt(a, d=""): return d
    def save_prompt(a, c): pass
    def list_prompts(): return {}
    def generate_report(**kw): pass

# ── Blueprint ─────────────────────────────────────────────────────────────
agent_bp = Blueprint("agent", __name__, url_prefix="/agent")

# ── Auth decorators ───────────────────────────────────────────────────────

def _login_required(f):
    @wraps(f)
    def _inner(*a, **kw):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*a, **kw)
    return _inner


def _owner_required(f):
    @wraps(f)
    def _inner(*a, **kw):
        if "user" not in session:
            if request.is_json:
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for("login"))
        if session.get("role") != "owner":
            return jsonify({"error": "Owner access required"}), 403
        return f(*a, **kw)
    return _inner

# ── State ─────────────────────────────────────────────────────────────────
_agent_running = False
_agent_period = "1y"
_ANALYSIS_PATH = "output/analysis.json"
_REPORT_PATH = "agent_report.html"
_VALID_PERIODS = {"1y", "6m", "1m"}
_PERIOD_LABELS = {"1y": "Last 12 Months", "6m": "Last 6 Months", "1m": "Last Month"}
_VALID_AGENTS = {
    "orchestrator", "data_collector", "market_researcher",
    "revenue_analyzer", "strategy_planner",
}

# ── Helpers ───────────────────────────────────────────────────────────────

def _load_analysis() -> dict:
    if not os.path.exists(_ANALYSIS_PATH):
        return {}
    with open(_ANALYSIS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _fmt(val, default="N/A"):
    try:
        n = float(val)
        if n >= 1_00_000:
            return f"₹{n / 1_00_000:.2f}L"
        return f"₹{n:,.0f}"
    except (TypeError, ValueError):
        return default


def _pct(part, total, default=0):
    try:
        return min(100, round(float(part) / float(total) * 100))
    except (TypeError, ValueError, ZeroDivisionError):
        return default


def _extract_kpis(data: dict) -> dict:
    if not data:
        return {"has_data": False, "generated_at": None}
    acad = data.get("collect_academy_data", {})
    rev = acad.get("revenue_breakdown", {})
    cat = rev.get("by_category", {})
    gaps_data = data.get("identify_revenue_gaps", {})
    strat = data.get("generate_revenue_strategy", {})
    exec_sum = gaps_data.get("executive_summary", {})
    ss = strat.get("strategy_summary", {})
    total = float(rev.get("total_revenue_in_db", 0) or 0)
    daily = float(rev.get("avg_daily_revenue", 0) or 0)
    monthly = daily * 30 if daily else (total / 5 if total else 0)
    bookings = float(cat.get("bookings", 0) or 0)
    return {
        "has_data": True,
        "generated_at": data.get("_generated_at"),
        "monthly_revenue": _fmt(monthly),
        "total_revenue": _fmt(total),
        "bookings_revenue": _fmt(bookings),
        "bookings_pct": _pct(bookings, monthly),
        "active_passes": int(float(
            acad.get("membership_analysis", {}).get("active_monthly_passes", 0) or 0
        )),
        "gap_potential": _fmt(exec_sum.get("total_identified_gap_high", 0)),
        "gaps_count": int(exec_sum.get("number_of_gaps_identified", 0) or 0),
        "m12_revenue": _fmt(ss.get("projected_monthly_revenue_month_12_inr", 0)),
        "roi": int(float(ss.get("blended_roi_percent", 0) or 0)),
        "investment": _fmt(ss.get("total_investment_required_inr", 0)),
        "observations": acad.get("key_observations", [])[:6],
        "top_gaps": gaps_data.get("revenue_gaps", [])[:4],
    }


def _analysis_summary(data: dict) -> str:
    if not data:
        return "No analysis data available yet. Run the analysis pipeline first."
    acad = data.get("collect_academy_data", {})
    gaps = data.get("identify_revenue_gaps", {})
    strat = data.get("generate_revenue_strategy", {})
    rev = acad.get("revenue_breakdown", {})
    total = float(rev.get("total_revenue_in_db", 0) or 0)
    daily = float(rev.get("avg_daily_revenue", 0) or 0)
    monthly = daily * 30 if daily else (total / 5 if total else 0)
    exec_sum = gaps.get("executive_summary", {})
    gap_high = float(exec_sum.get("total_identified_gap_high", 0) or 0)
    ss = strat.get("strategy_summary", {})
    m12 = float(ss.get("projected_monthly_revenue_month_12_inr", 0) or 0)
    roi = float(ss.get("blended_roi_percent", 0) or 0)
    top_gaps = "\n".join(
        f"  - {g.get('name')}: gap "
        f"₹{float(g.get('gap_amount_inr_low', 0)):,.0f}–"
        f"₹{float(g.get('gap_amount_inr_high', 0)):,.0f}/mo"
        for g in gaps.get("revenue_gaps", [])[:5]
    )
    top_inits = "\n".join(
        f"  - {i.get('name')} (ROI {float(i.get('roi_12_month_percent', 0)):.0f}%)"
        for i in strat.get("strategic_initiatives", [])[:5]
    )
    obs = "\n".join(f"  - {o}" for o in acad.get("key_observations", [])[:5])
    return f"""UNITY SHUTTLE ARENA — LATEST ANALYSIS SUMMARY
Generated: {data.get("_generated_at", "unknown")}

FINANCIALS:
- Monthly run rate: ₹{monthly:,.0f}
- Total revenue in DB: ₹{total:,.0f}
- Revenue gap potential: up to ₹{gap_high:,.0f}/month
- 12-month revenue target: ₹{m12:,.0f}/month
- Blended ROI: {roi:.0f}%

TOP REVENUE GAPS:
{top_gaps}

KEY OBSERVATIONS:
{obs}

TOP STRATEGIC INITIATIVES:
{top_inits}
"""

# ── SPA ───────────────────────────────────────────────────────────────────

@agent_bp.route("")
@agent_bp.route("/")
@_owner_required
def spa():
    return render_template("agent_spa.html", root_path="/agent")


@agent_bp.route("/ui")
@agent_bp.route("/ui/<path:subpath>")
@_owner_required
def spa_ui(subpath=""):
    return render_template("agent_spa.html", root_path="/agent")

# ── State API — single endpoint the SPA polls ─────────────────────────────

@agent_bp.route("/api/state")
@_login_required
def api_state():
    kpis = _extract_kpis(_load_analysis())
    kpis["running"] = _agent_running
    agents = sorted(_VALID_AGENTS)
    return jsonify({
        "kpis": kpis,
        "agents": agents,
        "has_report": os.path.exists(_REPORT_PATH),
        "prompts": {a: load_prompt(a) for a in agents},
    })

# ── Analysis ──────────────────────────────────────────────────────────────

@agent_bp.route("/analysis")
@_login_required
def get_analysis():
    data = _load_analysis()
    if not data:
        return jsonify({"error": "No analysis found. Run the pipeline first."}), 404
    acad = data.get("collect_academy_data", {})
    acad.pop("_raw_db_snapshot", None)
    return jsonify(data)


@agent_bp.route("/analysis/summary")
@_login_required
def get_analysis_summary():
    return jsonify({"summary": _analysis_summary(_load_analysis())})


@agent_bp.route("/run-analysis", methods=["POST"])
@_owner_required
def run_analysis():
    global _agent_running, _agent_period
    if _agent_running:
        return jsonify({"status": "already_running", "message": "Analysis already in progress."})

    body = request.get_json(silent=True) or {}
    period = body.get("period", "1y") if body.get("period") in _VALID_PERIODS else "1y"
    _agent_period = period

    def _run():
        global _agent_running
        _agent_running = True
        try:
            os.makedirs("output", exist_ok=True)
            from agents.orchestrator import run_revenue_analysis
            run_revenue_analysis(period)
            generate_report(data_path=_ANALYSIS_PATH, output_path=_REPORT_PATH)
        except Exception as exc:
            print(f"[agent] pipeline error: {exc}", flush=True)
        finally:
            _agent_running = False

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({
        "status": "started",
        "period": period,
        "period_label": _PERIOD_LABELS[period],
        "message": f"Analysis started for {_PERIOD_LABELS[period]}.",
    })


@agent_bp.route("/generate-report", methods=["POST"])
@_owner_required
def gen_report():
    if not os.path.exists(_ANALYSIS_PATH):
        return jsonify({"error": "No analysis data. Run the pipeline first."}), 404
    try:
        generate_report(data_path=_ANALYSIS_PATH, output_path=_REPORT_PATH)
        return jsonify({"status": "ok", "message": "Report generated."})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

# ── Prompts ───────────────────────────────────────────────────────────────

@agent_bp.route("/prompts")
@_login_required
def get_all_prompts():
    return jsonify(list_prompts())


@agent_bp.route("/prompts/<string:agent_name>", methods=["GET"])
@_login_required
def get_prompt(agent_name):
    if agent_name not in _VALID_AGENTS:
        return jsonify({"error": f"Unknown agent '{agent_name}'"}), 404
    content = load_prompt(agent_name)
    if not content:
        return jsonify({"error": f"No prompt file for '{agent_name}'"}), 404
    return jsonify({"agent": agent_name, "content": content})


@agent_bp.route("/prompts/<string:agent_name>", methods=["PUT"])
@_owner_required
def update_prompt(agent_name):
    if agent_name not in _VALID_AGENTS:
        return jsonify({"error": f"Unknown agent '{agent_name}'"}), 404
    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return jsonify({"error": "Prompt content cannot be empty."}), 400
    save_prompt(agent_name, content)
    return jsonify({"agent": agent_name, "status": "updated", "length": len(content)})

# ── Chat ──────────────────────────────────────────────────────────────────

_CHAT_SYSTEM = """You are a business intelligence assistant for Unity Shuttle Arena, a badminton academy
in Hinjawadi Phase 1, Pune. You have access to the latest revenue analysis data for the academy.

Your role:
- Answer questions about current revenue, gaps, opportunities, and strategy
- Explain findings from the analysis clearly and concisely
- Suggest action steps based on the data
- Help update or refine agent prompts when asked

Always ground your answers in the analysis data provided. Be specific with numbers.
If something is not in the data, say so clearly rather than guessing.
Respond in a friendly, professional tone suitable for a business owner."""


@agent_bp.route("/chat", methods=["POST"])
@_login_required
def chat():
    if not MISTRAL_API_KEY:
        return jsonify({"error": "MISTRAL_API_KEY not configured."}), 500

    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message field required."}), 400

    context = _analysis_summary(_load_analysis())
    system = f"{_CHAT_SYSTEM}\n\n=== CURRENT ANALYSIS DATA ===\n{context}"

    messages = [{"role": "system", "content": system}]
    for h in (body.get("history") or [])[-10:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    client = Mistral(api_key=MISTRAL_API_KEY, timeout_ms=60_000)
    response = mistral_complete_with_retry(
        client, model=SUBAGENT_MODEL, max_tokens=1024, messages=messages
    )
    return jsonify({
        "reply": response.choices[0].message.content.strip(),
        "timestamp": datetime.now().isoformat(),
    })

# ── Report serving ────────────────────────────────────────────────────────

@agent_bp.route("/report-raw")
@_login_required
def report_raw():
    if not os.path.exists(_REPORT_PATH):
        return "Report not generated yet.", 404
    with open(_REPORT_PATH, encoding="utf-8") as f:
        return Response(f.read(), mimetype="text/html")


@agent_bp.route("/report-download")
@_login_required
def report_download():
    if not os.path.exists(_REPORT_PATH):
        return "Report not generated yet.", 404
    return send_file(
        _REPORT_PATH,
        mimetype="text/html",
        as_attachment=True,
        download_name="usa-revenue-report.html",
    )
