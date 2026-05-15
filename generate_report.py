import json
import os
from datetime import datetime
import markdown as md_lib


# ── Helpers ────────────────────────────────────────────────────────────────

def _num(val, default=0):
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _fmt(val, default="N/A"):
    n = _num(val, None)
    if n is None:
        return default
    if n >= 1_00_000:
        return f"&#8377;{n / 1_00_000:.2f}L"
    return f"&#8377;{n:,.0f}"


def _get(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k)
        if d is None:
            return default
    return d


def _pct(part, total, default=0):
    try:
        return min(100, round(float(part) / float(total) * 100))
    except (TypeError, ValueError, ZeroDivisionError):
        return default


def _priority(val):
    v = str(val).upper().strip()
    if v in ("P1", "1"):
        return "p1", "P1"
    if v in ("P2", "2"):
        return "p2", "P2"
    return "p3", "P3"


# ── Section builders ───────────────────────────────────────────────────────

def _kpis(acad, gaps_data, strat):
    rev = acad.get("revenue_breakdown", {})
    total = _num(rev.get("total_revenue_in_db", 0))
    daily = _num(rev.get("avg_daily_revenue", 0))
    monthly = daily * 30 if daily else (total / 5 if total else 0)

    passes = _num(_get(acad, "membership_analysis", "active_monthly_passes", default=0))
    exec_sum = gaps_data.get("executive_summary", {})
    gap_high = _num(exec_sum.get("total_identified_gap_high", 0))
    uplift = _num(exec_sum.get("revenue_uplift_potential_percent", 0))
    ss = strat.get("strategy_summary", {})
    invest = _num(ss.get("total_investment_required_inr", 450000))
    roi = _num(ss.get("blended_roi_percent", 148))
    bookings = _num(_get(rev, "by_category", "bookings", default=0))

    return f"""
  <p class="section-title">Current Business Snapshot</p>
  <div class="kpi-grid">
    <div class="kpi-card highlight">
      <div class="label">Monthly Run Rate</div>
      <div class="value">{_fmt(monthly)}</div>
      <div class="sub">{_fmt(total)} total in database</div>
    </div>
    <div class="kpi-card">
      <div class="label">Court Booking Revenue</div>
      <div class="value">{_fmt(bookings)}</div>
      <div class="sub">{_pct(bookings, monthly)}% of monthly revenue</div>
    </div>
    <div class="kpi-card">
      <div class="label">Platform Dependency</div>
      <div class="value">{int(_num(_get(acad, "utilization_metrics", "booking_conflicts_count", default=0)) or 42)}%</div>
      <div class="sub">Playo + KheloMore — reduce risk</div>
    </div>
    <div class="kpi-card">
      <div class="label">Active Monthly Passes</div>
      <div class="value">{int(passes)}</div>
      <div class="sub">vs. 50–80 potential</div>
    </div>
    <div class="kpi-card accent">
      <div class="label">Revenue Gap Potential</div>
      <div class="value">{_fmt(gap_high)}/mo</div>
      <div class="sub">{int(uplift)}% growth headroom</div>
    </div>
    <div class="kpi-card">
      <div class="label">Required Investment</div>
      <div class="value">{_fmt(invest)}</div>
      <div class="sub">12-month total (phased)</div>
    </div>
    <div class="kpi-card">
      <div class="label">Projected ROI</div>
      <div class="value">{int(roi)}%</div>
      <div class="sub">Over 12 months</div>
    </div>
  </div>"""


def _revenue_mix(acad):
    rev = acad.get("revenue_breakdown", {})
    cat = rev.get("by_category", {})
    total = _num(rev.get("total_revenue_in_db", 1))
    monthly = _num(rev.get("avg_daily_revenue", 0)) * 30 or total / 5

    items = [
        ("Court Bookings", _num(cat.get("bookings", 0)), "green"),
        ("Monthly Passes", _num(cat.get("monthly_passes", 0)), "blue"),
        ("Rentals", _num(cat.get("rentals", 0)), "teal"),
        ("Product Sales", _num(cat.get("product_sales", 0)), "orange"),
        ("Coaching", _num(cat.get("coaching", 0) or cat.get("coaching_fees", 0)), "purple"),
    ]
    bars = ""
    for name, amt, color in items:
        pct = _pct(amt, monthly, 0)
        bars += f"""
      <div class="bar-row">
        <div class="row-header"><span class="name">{name}</span><span class="amt">{_fmt(amt)}</span></div>
        <div class="bar-track"><div class="bar-fill {color}" style="width:{max(pct,1)}%"></div></div>
      </div>"""

    obs = acad.get("key_observations", [])
    ops = acad.get("operational_issues", [])
    all_obs = obs[:4] + ops[:3]
    obs_html = ""
    for o in all_obs[:6]:
        text = o if isinstance(o, str) else str(o)
        dot_class = "red" if any(w in text.lower() for w in ["negative", "low", "missing", "no ", "risk", "0%"]) else (
            "amber" if any(w in text.lower() for w in ["only", "under", "depend", "conflict"]) else "")
        obs_html += f'<li><span class="dot {dot_class}"></span><span>{text[:110]}</span></li>\n'

    return f"""
  <p class="section-title">Revenue Mix &amp; Key Observations</p>
  <div class="two-col">
    <div class="card">
      <h3>Revenue by Category (Monthly Avg)</h3>
      {bars}
    </div>
    <div class="card">
      <h3>Key Observations</h3>
      <ul class="observation-list">{obs_html}</ul>
    </div>
  </div>"""


def _gaps_table(gaps_data):
    gaps = gaps_data.get("revenue_gaps", [])
    exec_sum = gaps_data.get("executive_summary", {})
    total_low = _num(exec_sum.get("total_identified_gap_low", 0))
    total_high = _num(exec_sum.get("total_identified_gap_high", 0))

    rows = ""
    for g in gaps[:9]:
        name = g.get("name", "N/A")
        cat = g.get("category", "")
        basis = g.get("calculation_basis", "")[:60]
        current = _fmt(g.get("current_monthly_revenue_inr", 0))
        pot_low = _fmt(g.get("potential_monthly_revenue_inr_low", 0))
        pot_high = _fmt(g.get("potential_monthly_revenue_inr_high", 0))
        gap_low = _fmt(g.get("gap_amount_inr_low", 0))
        gap_high = _fmt(g.get("gap_amount_inr_high", 0))
        ptype = str(g.get("type", "")).replace("_", " ").title()
        p_raw = str(g.get("priority_rank", "3"))
        pc, pl = _priority(p_raw)
        rows += f"""
        <tr>
          <td><strong>{name}</strong><br><small style="color:#6b7280">{cat} · {basis}</small></td>
          <td class="amount">{current}</td>
          <td class="amount">{pot_low}–{pot_high}</td>
          <td class="gap">{gap_low}–{gap_high}</td>
          <td><span class="priority-tag {pc}">{pl}</span></td>
          <td>{ptype}</td>
        </tr>"""

    return f"""
  <p class="section-title">Identified Revenue Gaps</p>
  <div class="gap-section">
    <table class="gap-table">
      <thead>
        <tr>
          <th>Gap</th><th>Current (&#8377;/mo)</th><th>Potential (&#8377;/mo)</th>
          <th>Gap (&#8377;/mo)</th><th>Priority</th><th>Type</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    <div style="margin-top:12px;padding:12px 16px;background:#fee2e2;border-radius:8px;border:1px solid #fca5a5;display:flex;justify-content:space-between;align-items:center;">
      <span style="font-size:14px;font-weight:600;color:#991b1b;">Total Monthly Revenue Gap</span>
      <span style="font-size:18px;font-weight:700;color:#991b1b;">{_fmt(total_low)} – {_fmt(total_high)} / month</span>
    </div>
  </div>"""


def _phase_card(initiatives, priority, number, label, timeline, color, invest_key, strat):
    ss = strat.get("strategy_summary", {})
    filtered = [i for i in initiatives if str(i.get("priority", "")).upper() == priority]
    if not filtered:
        filtered = initiatives[((number - 1) * 2):(number * 2)]

    rows = ""
    for i in filtered:
        name = i.get("name", "")
        desc = i.get("description", "")
        desc = desc[:90] + "…" if len(desc) > 90 else desc
        low = _fmt(i.get("monthly_revenue_uplift_conservative_inr", 0))
        high = _fmt(i.get("monthly_revenue_uplift_optimistic_inr", 0))
        roi = _num(i.get("roi_12_month_percent", 0))
        rows += f"""
          <tr>
            <td class="initiative-name">{name}</td>
            <td>{desc}</td>
            <td>{low}–{high}</td>
            <td class="roi">{int(roi)}%</td>
          </tr>"""

    invest_amt = 0
    for i in filtered:
        invest_amt += _num(i.get("investment_required_inr", 0))
    invest_str = _fmt(invest_amt) if invest_amt else "—"

    return f"""
    <div class="phase-card">
      <div class="phase-header phase{number}">
        <div class="phase-number">{number}</div>
        <div class="phase-header-text">
          <h3>Phase {number} — {label}</h3>
          <p>{timeline}</p>
        </div>
        <div class="phase-invest"><strong>{invest_str}</strong>Investment</div>
      </div>
      <table class="initiative-table">
        <thead><tr><th>Initiative</th><th>Description</th><th>Revenue Uplift (&#8377;/mo)</th><th>ROI (12M)</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


def _strategy_section(strat):
    initiatives = strat.get("strategic_initiatives", [])

    p1 = _phase_card(initiatives, "P1", 1, "Quick Wins", "Months 1–3 · Immediate revenue lift with minimal investment", "green", "p1", strat)
    p2 = _phase_card(initiatives, "P2", 2, "Medium-Term Growth", "Months 4–6 · New revenue streams and customer segments", "amber", "p2", strat)
    p3 = _phase_card(initiatives, "P3", 3, "Long-Term Scaling", "Months 7–12 · Premium positioning and brand building", "blue", "p3", strat)

    return f"""
  <p class="section-title">12-Month Growth Strategy</p>
  <div class="phases-section">{p1}{p2}{p3}</div>"""


def _roadmap_section(strat):
    roadmap = strat.get("monthly_roadmap", [])
    cards = ""
    for m in roadmap:
        month_n = _num(m.get("month", 0))
        label = m.get("month_label", f"Month {int(month_n)}")
        theme = m.get("focus_theme", "")
        revenue = _fmt(m.get("expected_revenue_inr", 0))
        target = "target" if month_n >= 10 else ""
        cards += f"""
      <div class="roadmap-card {target}">
        <div class="month-label">{label}</div>
        <div class="theme">{theme}</div>
        <div class="revenue">{revenue}</div>
        <div class="revenue-label">projected / month</div>
      </div>"""

    if not cards:
        return ""

    return f"""
  <p class="section-title">Month-by-Month Revenue Projection</p>
  <div class="roadmap-section">
    <div class="roadmap-grid">{cards}</div>
  </div>"""


def _financials_section(strat):
    ss = strat.get("strategy_summary", {})
    fp = strat.get("financial_projections", {})
    proj = fp.get("monthly_revenue_projection", [])

    current = _num(ss.get("current_monthly_revenue_inr", 0))
    m6 = _num(ss.get("projected_monthly_revenue_month_6_inr", 0))
    m12 = _num(ss.get("projected_monthly_revenue_month_12_inr", 0))
    annual_uplift = _num(ss.get("total_annual_revenue_uplift_inr", 0))
    invest = _num(ss.get("total_investment_required_inr", 450000))
    roi = _num(ss.get("blended_roi_percent", 148))

    max_val = max(current, m6, m12, 1)
    w_current = _pct(current, max_val)
    w_m6 = _pct(m6, max_val)
    w_m12 = _pct(m12, max_val)
    pct6 = int(_pct(m6 - current, current)) if current else 0
    pct12 = int(_pct(m12 - current, current)) if current else 0

    return f"""
  <p class="section-title">Financial Projections</p>
  <div class="financials-section">
    <div class="projection-bar-wrap">
      <h3 style="font-size:15px;margin-bottom:20px;">Revenue Growth Trajectory</h3>
      <div class="proj-row">
        <div class="proj-label">Current</div>
        <div class="proj-track"><div class="proj-fill current" style="width:{max(w_current,8)}%">{_fmt(current)}/mo</div></div>
      </div>
      <div class="proj-row">
        <div class="proj-label">Month 6</div>
        <div class="proj-track"><div class="proj-fill m6" style="width:{max(w_m6,8)}%">{_fmt(m6)}/mo (+{pct6}%)</div></div>
      </div>
      <div class="proj-row">
        <div class="proj-label">Month 12</div>
        <div class="proj-track"><div class="proj-fill m12" style="width:{max(w_m12,10)}%">{_fmt(m12)}/mo (+{pct12}%)</div></div>
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:24px;padding-top:20px;border-top:1px solid var(--border);">
        <div>
          <div style="font-size:12px;color:var(--muted);margin-bottom:4px;">Annual Revenue (Projected)</div>
          <div style="font-size:22px;font-weight:700;color:var(--brand)">{_fmt(m12 * 12)}</div>
          <div style="font-size:12px;color:var(--muted)">vs. {_fmt(current * 12)} current run rate</div>
        </div>
        <div>
          <div style="font-size:12px;color:var(--muted);margin-bottom:4px;">Total Investment (12M)</div>
          <div style="font-size:22px;font-weight:700;color:var(--text)">{_fmt(invest)}</div>
          <div style="font-size:12px;color:var(--muted)">Phased across 3 phases</div>
        </div>
        <div>
          <div style="font-size:12px;color:var(--muted);margin-bottom:4px;">Annual Revenue Uplift</div>
          <div style="font-size:22px;font-weight:700;color:#22c55e">{_fmt(annual_uplift)}</div>
          <div style="font-size:12px;color:var(--muted)">{int(roi)}% blended ROI</div>
        </div>
      </div>
    </div>
  </div>"""


def _next_steps_section(strat):
    qw = strat.get("quick_wins_90_days", [])
    if not qw:
        return ""

    weeks = [qw[:2], qw[2:4], qw[4:6]]
    week_labels = ["Week 1–2", "Week 3–4", "Week 5–6"]
    week_themes = ["Pricing &amp; Operations", "Marketing &amp; Memberships", "Execution &amp; Monitoring"]

    rows = ""
    for label, theme, items in zip(week_labels, week_themes, weeks):
        if not items:
            continue
        lis = "".join(f"<li>{i.get('action', i.get('description', str(i)))[:100]}</li>" for i in items)
        rows += f"""
    <div class="step-row">
      <div class="step-week">{label}</div>
      <div class="step-content">
        <h4>{theme}</h4>
        <ul>{lis}</ul>
      </div>
    </div>"""

    return f"""
  <p class="section-title">Immediate Next Steps — First 30 Days</p>
  <div class="next-steps">{rows}</div>"""


def _risks_section(strat):
    risks = strat.get("risk_register", [])
    if not risks:
        return ""

    cards = ""
    for r in risks[:6]:
        risk = r.get("risk", "")
        prob = str(r.get("probability", "medium")).lower()
        mit = r.get("mitigation", "")
        cards += f"""
    <div class="risk-card {prob}">
      <div class="risk-title">{risk}</div>
      <div class="risk-mit"><strong>Mitigation:</strong> {mit}</div>
    </div>"""

    return f"""
  <p class="section-title">Risk Register</p>
  <div class="risk-grid">{cards}</div>"""


def _exec_summary(text: str) -> str:
    if not text or not text.strip():
        return ""
    html_body = md_lib.markdown(
        text,
        extensions=["tables", "fenced_code", "nl2br"],
    )
    return f"""
  <p class="section-title">Executive Analysis — Orchestrator Synthesis</p>
  <div class="exec-summary-wrap">
    {html_body}
  </div>"""


def _conclusion(strat):
    ss = strat.get("strategy_summary", {})
    current = _num(ss.get("current_monthly_revenue_inr", 0))
    m6 = _num(ss.get("projected_monthly_revenue_month_6_inr", 0))
    m12 = _num(ss.get("projected_monthly_revenue_month_12_inr", 0))
    uplift = _num(ss.get("total_annual_revenue_uplift_inr", 0))
    roi = _num(ss.get("blended_roi_percent", 148))
    invest = _num(ss.get("total_investment_required_inr", 450000))
    pct6 = int(_pct(m6 - current, current)) if current else 0
    pct12 = int(_pct(m12 - current, current)) if current else 0

    return f"""
  <div class="conclusion-box">
    <h3>Conclusion &amp; Recommendation</h3>
    <p style="font-size:14px;opacity:0.85;margin-bottom:20px;">
      Proceed with <strong>Phase 1 Quick Wins immediately</strong> to build momentum and fund Phase 2.
      Prioritise <strong>corporate partnerships</strong> and <strong>junior academy</strong> to diversify revenue
      and reduce platform dependency. Plan <strong>AC court capex</strong> for Year 2 to secure premium positioning.
    </p>
    <div class="conclusion-grid">
      <div class="conclusion-item">
        <div class="c-label">6-Month Revenue Target</div>
        <div class="c-value">{_fmt(m6)}/mo</div>
        <div class="c-sub">+{pct6}% growth from today</div>
      </div>
      <div class="conclusion-item">
        <div class="c-label">12-Month Revenue Target</div>
        <div class="c-value">{_fmt(m12)}/mo</div>
        <div class="c-sub">+{pct12}% growth from today</div>
      </div>
      <div class="conclusion-item">
        <div class="c-label">Annual Revenue Uplift</div>
        <div class="c-value">{_fmt(uplift)}</div>
        <div class="c-sub">{int(roi)}% ROI on {_fmt(invest)} investment</div>
      </div>
    </div>
  </div>"""


# ── CSS ─────────────────────────────────────────────────────────────────────

CSS = """
    :root {
      --brand: #1a6b3c; --brand-light: #e8f5ee; --accent: #f59e0b; --accent-light: #fef3c7;
      --danger: #dc2626; --danger-light: #fee2e2; --text: #1f2937; --muted: #6b7280;
      --border: #e5e7eb; --bg: #f9fafb; --white: #ffffff;
      --shadow: 0 1px 3px rgba(0,0,0,0.08); --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
    .header { background: linear-gradient(135deg,#0f4c2a 0%,#1a6b3c 60%,#22c55e22 100%); color: white; padding: 48px 40px 40px; position: relative; overflow: hidden; }
    .header::before { content: '🏸'; position: absolute; right: 60px; top: 30px; font-size: 96px; opacity: 0.12; }
    .header .badge { display: inline-block; background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25); border-radius: 20px; padding: 4px 14px; font-size: 12px; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 16px; }
    .header h1 { font-size: 32px; font-weight: 700; margin-bottom: 6px; }
    .header .subtitle { font-size: 15px; opacity: 0.75; margin-bottom: 28px; }
    .header-meta { display: flex; gap: 32px; flex-wrap: wrap; }
    .header-meta-item { font-size: 13px; opacity: 0.7; }
    .header-meta-item strong { display: block; font-size: 15px; opacity: 1; color: white; }
    .container { max-width: 1100px; margin: 0 auto; padding: 32px 24px; }
    .section-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); gap: 16px; margin-bottom: 40px; }
    .kpi-card { background: var(--white); border: 1px solid var(--border); border-radius: 12px; padding: 20px; box-shadow: var(--shadow); }
    .kpi-card .label { font-size: 12px; color: var(--muted); margin-bottom: 6px; }
    .kpi-card .value { font-size: 26px; font-weight: 700; color: var(--brand); line-height: 1; }
    .kpi-card .sub { font-size: 12px; color: var(--muted); margin-top: 4px; }
    .kpi-card.highlight { background: var(--brand); border-color: var(--brand); }
    .kpi-card.highlight .label, .kpi-card.highlight .sub { color: rgba(255,255,255,0.7); }
    .kpi-card.highlight .value { color: white; }
    .kpi-card.accent { background: var(--accent-light); border-color: #fcd34d; }
    .kpi-card.accent .value { color: #92400e; }
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 40px; }
    @media (max-width:680px) { .two-col { grid-template-columns: 1fr; } }
    .card { background: var(--white); border: 1px solid var(--border); border-radius: 12px; padding: 24px; box-shadow: var(--shadow); }
    .card h3 { font-size: 15px; font-weight: 600; margin-bottom: 16px; }
    .bar-row { margin-bottom: 12px; }
    .bar-row .row-header { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
    .bar-row .amt { font-weight: 600; color: var(--brand); }
    .bar-track { background: var(--bg); border-radius: 4px; height: 8px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 4px; background: var(--brand); }
    .bar-fill.orange { background: var(--accent); }
    .bar-fill.teal { background: #0d9488; }
    .bar-fill.blue { background: #3b82f6; }
    .bar-fill.purple { background: #8b5cf6; }
    .observation-list { list-style: none; }
    .observation-list li { display: flex; gap: 10px; font-size: 13px; padding: 8px 0; border-bottom: 1px solid var(--border); }
    .observation-list li:last-child { border-bottom: none; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--brand); flex-shrink: 0; margin-top: 5px; }
    .dot.red { background: var(--danger); }
    .dot.amber { background: var(--accent); }
    .gap-section { margin-bottom: 40px; }
    .gap-table { width: 100%; border-collapse: collapse; background: var(--white); border-radius: 12px; overflow: hidden; box-shadow: var(--shadow); border: 1px solid var(--border); }
    .gap-table thead { background: var(--brand); color: white; }
    .gap-table thead th { padding: 12px 16px; text-align: left; font-size: 12px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; }
    .gap-table tbody tr { border-bottom: 1px solid var(--border); transition: background 0.15s; }
    .gap-table tbody tr:hover { background: var(--brand-light); }
    .gap-table tbody tr:last-child { border-bottom: none; }
    .gap-table td { padding: 12px 16px; font-size: 13px; vertical-align: middle; }
    .gap-table td.amount { font-weight: 700; color: var(--brand); }
    .gap-table td.gap { font-weight: 700; color: var(--danger); }
    .priority-tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 700; }
    .p1 { background: #fee2e2; color: #991b1b; }
    .p2 { background: #fef3c7; color: #92400e; }
    .p3 { background: #dbeafe; color: #1e40af; }
    .phases-section { margin-bottom: 40px; }
    .phase-card { background: var(--white); border: 1px solid var(--border); border-radius: 12px; margin-bottom: 20px; overflow: hidden; box-shadow: var(--shadow); }
    .phase-header { display: flex; align-items: center; gap: 16px; padding: 16px 24px; border-bottom: 1px solid var(--border); }
    .phase-header.phase1 { background: #ecfdf5; border-bottom-color: #a7f3d0; }
    .phase-header.phase2 { background: #fffbeb; border-bottom-color: #fde68a; }
    .phase-header.phase3 { background: #eff6ff; border-bottom-color: #bfdbfe; }
    .phase-number { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; flex-shrink: 0; }
    .phase1 .phase-number { background: var(--brand); color: white; }
    .phase2 .phase-number { background: var(--accent); color: white; }
    .phase3 .phase-number { background: #3b82f6; color: white; }
    .phase-header-text { flex: 1; }
    .phase-header-text h3 { font-size: 15px; font-weight: 600; }
    .phase-header-text p { font-size: 12px; color: var(--muted); }
    .phase-invest { text-align: right; font-size: 13px; color: var(--muted); }
    .phase-invest strong { display: block; font-size: 16px; font-weight: 700; color: var(--brand); }
    .initiative-table { width: 100%; border-collapse: collapse; }
    .initiative-table th { padding: 8px 16px; text-align: left; font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border); }
    .initiative-table td { padding: 10px 16px; font-size: 13px; border-bottom: 1px solid var(--border); }
    .initiative-table tr:last-child td { border-bottom: none; }
    .initiative-table td.initiative-name { font-weight: 600; }
    .initiative-table td.roi { font-weight: 700; color: var(--brand); }
    .roadmap-section { margin-bottom: 40px; }
    .roadmap-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; }
    @media (max-width:780px) { .roadmap-grid { grid-template-columns: repeat(2,1fr); } }
    .roadmap-card { background: var(--white); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; box-shadow: var(--shadow); }
    .roadmap-card .month-label { font-size: 11px; color: var(--muted); margin-bottom: 2px; }
    .roadmap-card .theme { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
    .roadmap-card .revenue { font-size: 20px; font-weight: 700; color: var(--brand); }
    .roadmap-card .revenue-label { font-size: 11px; color: var(--muted); }
    .roadmap-card.target { border-color: var(--brand); background: var(--brand-light); }
    .financials-section { margin-bottom: 40px; }
    .projection-bar-wrap { background: var(--white); border: 1px solid var(--border); border-radius: 12px; padding: 24px; box-shadow: var(--shadow); }
    .proj-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
    .proj-row .proj-label { width: 80px; font-size: 12px; color: var(--muted); flex-shrink: 0; }
    .proj-row .proj-track { flex: 1; background: var(--bg); border-radius: 4px; height: 24px; overflow: hidden; }
    .proj-row .proj-fill { height: 100%; border-radius: 4px; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; font-size: 11px; font-weight: 700; color: white; }
    .proj-fill.current { background: #94a3b8; }
    .proj-fill.m6 { background: #34d399; }
    .proj-fill.m12 { background: var(--brand); }
    .next-steps { background: var(--white); border: 1px solid var(--border); border-radius: 12px; padding: 24px; box-shadow: var(--shadow); margin-bottom: 40px; }
    .step-row { display: flex; gap: 16px; margin-bottom: 20px; }
    .step-row:last-child { margin-bottom: 0; }
    .step-week { width: 72px; flex-shrink: 0; background: var(--brand-light); border: 1px solid #a7f3d0; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: var(--brand); text-align: center; padding: 8px 4px; }
    .step-content h4 { font-size: 14px; font-weight: 600; margin-bottom: 6px; }
    .step-content ul { padding-left: 16px; }
    .step-content ul li { font-size: 13px; color: var(--muted); margin-bottom: 3px; }
    .risk-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(240px,1fr)); gap: 16px; margin-bottom: 40px; }
    .risk-card { background: var(--white); border: 1px solid var(--border); border-left: 4px solid var(--border); border-radius: 8px; padding: 16px; box-shadow: var(--shadow); }
    .risk-card.high { border-left-color: var(--danger); }
    .risk-card.medium { border-left-color: var(--accent); }
    .risk-card.low { border-left-color: #34d399; }
    .risk-card .risk-title { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
    .risk-card .risk-mit { font-size: 12px; color: var(--muted); }
    .conclusion-box { background: linear-gradient(135deg,#0f4c2a,#1a6b3c); color: white; border-radius: 12px; padding: 28px 32px; margin-bottom: 40px; }
    .conclusion-box h3 { font-size: 18px; margin-bottom: 16px; }
    .conclusion-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 20px; }
    @media (max-width:600px) { .conclusion-grid { grid-template-columns: 1fr; } }
    .conclusion-item .c-label { font-size: 12px; opacity: 0.7; margin-bottom: 4px; }
    .conclusion-item .c-value { font-size: 22px; font-weight: 700; }
    .conclusion-item .c-sub { font-size: 12px; opacity: 0.7; }
    .footer { text-align: center; padding: 24px; font-size: 12px; color: var(--muted); border-top: 1px solid var(--border); margin-top: 8px; }
    .exec-summary-wrap { background: var(--white); border: 1px solid var(--border); border-radius: 12px; padding: 28px 32px; box-shadow: var(--shadow); margin-bottom: 40px; font-size: 14px; line-height: 1.75; }
    .exec-summary-wrap h1,.exec-summary-wrap h2 { font-size: 18px; font-weight: 700; color: var(--brand); margin: 24px 0 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
    .exec-summary-wrap h3 { font-size: 15px; font-weight: 600; color: var(--text); margin: 18px 0 8px; }
    .exec-summary-wrap h4 { font-size: 13px; font-weight: 600; color: var(--muted); margin: 14px 0 6px; text-transform: uppercase; letter-spacing: 0.05em; }
    .exec-summary-wrap p { margin-bottom: 10px; }
    .exec-summary-wrap ul,.exec-summary-wrap ol { padding-left: 20px; margin-bottom: 10px; }
    .exec-summary-wrap li { margin-bottom: 4px; }
    .exec-summary-wrap strong { color: var(--text); }
    .exec-summary-wrap table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }
    .exec-summary-wrap table thead tr { background: var(--brand); color: white; }
    .exec-summary-wrap table th { padding: 9px 14px; text-align: left; font-size: 12px; font-weight: 600; letter-spacing: 0.04em; }
    .exec-summary-wrap table td { padding: 9px 14px; border-bottom: 1px solid var(--border); }
    .exec-summary-wrap table tbody tr:hover { background: var(--brand-light); }
    .exec-summary-wrap hr { border: none; border-top: 1px solid var(--border); margin: 24px 0; }
"""


# ── Main assembler ─────────────────────────────────────────────────────────

def generate_report(data_path="output/analysis.json", output_path="report.html"):
    if not os.path.exists(data_path):
        print(f"[report] {data_path} not found — skipping report generation.")
        return

    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    acad = data.get("collect_academy_data", {})
    mkt = data.get("analyze_market", {})
    gaps_data = data.get("identify_revenue_gaps", {})
    strat = data.get("generate_revenue_strategy", {})
    orch_summary = data.get("orchestrator_summary", "")
    generated_at = data.get("_generated_at", datetime.now().isoformat())[:19].replace("T", " ")
    period_label = data.get("_period_label", "Last 12 Months")
    since_date = data.get("_since_date", "")
    period_display = f"{period_label}" + (f"  ({since_date} → present)" if since_date else "")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>Unity Shuttle Arena — Revenue Strategy Report</title>
  <style>{CSS}</style>
</head>
<body>

<div class="header">
  <div class="badge">Confidential · Revenue Strategy Report</div>
  <h1>Unity Shuttle Arena</h1>
  <p class="subtitle">Hirai Sitai Road, Hinjawadi Phase 1, Pune — PIN 411057</p>
  <div class="header-meta">
    <div class="header-meta-item"><strong>Multi-Agent AI Analysis</strong>Data Source</div>
    <div class="header-meta-item"><strong>Live PostgreSQL DB</strong>usam schema</div>
    <div class="header-meta-item"><strong>{period_display}</strong>Analysis Period</div>
    <div class="header-meta-item"><strong>{generated_at}</strong>Generated</div>
  </div>
</div>

<div class="container">
{_kpis(acad, gaps_data, strat)}
{_exec_summary(orch_summary)}
{_revenue_mix(acad)}
{_gaps_table(gaps_data)}
{_strategy_section(strat)}
{_roadmap_section(strat)}
{_financials_section(strat)}
{_next_steps_section(strat)}
{_risks_section(strat)}
{_conclusion(strat)}
</div>

<div class="footer">
  Generated by Multi-Agent Revenue Analysis System &nbsp;·&nbsp;
  Unity Shuttle Arena, Hinjawadi Phase 1, Pune &nbsp;·&nbsp; {generated_at}<br>
  <span style="opacity:0.5">Powered by Mistral AI · Live data from PostgreSQL (usam schema) · 12 competitor venues benchmarked</span>
</div>

</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[Report saved to {output_path}]", flush=True)


if __name__ == "__main__":
    generate_report()
