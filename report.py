import os
import sys
import smtplib
import socket
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from collections import defaultdict

REPORT_TO = [
    'ranvirkpoddar@gmail.com',
    'agrawalram020@gmail.com',
    'sande2891@gmail.com',
    'amrendra.ks@outlook.com'
]

IST = timezone(timedelta(hours=5, minutes=30))

smtp_server = "smtp.gmail.com"
smtp_port = 587



def get_india_today():
    return datetime.now(IST).date()


def _fmt_inr(amount):
    return f"₹{amount:,}"


def build_report_html(app, db, Transaction, MonthlyPass, CoachingStudent, CoachingBatch):
    """Build and return the full HTML report for the previous calendar day (IST)."""
    today = get_india_today()
    report_date = today - timedelta(days=1)

    with app.app_context():
        # ── Daily Transactions ────────────────────────────────────────
        txns = (
            Transaction.query
            .filter(db.func.date(Transaction.timestamp) == report_date)
            .filter(Transaction.status == 'Completed')
            .all()
        )

        rentals = [t for t in txns if t.category == 'Rent']
        sales   = [t for t in txns if t.category == 'Sale']
        bookings = [t for t in txns if t.category == 'Booking'
                    and not (t.item_name or '').startswith('Pass:')]

        # Aggregate rentals by item
        rental_agg = defaultdict(lambda: {'qty': 0, 'amount': 0})
        for t in rentals:
            rental_agg[t.item_name]['qty'] += t.qty or 1
            rental_agg[t.item_name]['amount'] += t.total_sell or 0

        # Aggregate sales by item
        sale_agg = defaultdict(lambda: {'qty': 0, 'amount': 0})
        for t in sales:
            sale_agg[t.item_name]['qty'] += t.qty or 1
            sale_agg[t.item_name]['amount'] += t.total_sell or 0

        rental_total  = sum(t.total_sell or 0 for t in rentals)
        sale_total    = sum(t.total_sell or 0 for t in sales)
        booking_total = sum(t.total_sell or 0 for t in bookings)

        # ── Monthly Passes sold yesterday ────────────────────────────
        passes_sold = (
            MonthlyPass.query
            .filter(db.func.date(MonthlyPass.timestamp) == report_date)
            .all()
        )
        pass_sold_total = sum(p.amount or 0 for p in passes_sold)

        # ── Active Coaching Students (snapshot) ──────────────────────
        active_students = (
            CoachingStudent.query
            .filter(
                db.or_(
                    CoachingStudent.end_date == None,
                    CoachingStudent.end_date >= today
                )
            )
            .order_by(CoachingStudent.end_date)
            .all()
        )
        active_students_fees = sum(s.fees or 0 for s in active_students)

        # ── Coaching Batches ─────────────────────────────────────────
        batches = CoachingBatch.query.order_by(CoachingBatch.start_time).all()

        # ── Active Monthly Pass Holders (snapshot) ───────────────────
        active_passes = (
            MonthlyPass.query
            .filter(MonthlyPass.end_date >= today)
            .order_by(MonthlyPass.end_date)
            .all()
        )
        active_pass_total = sum(p.amount or 0 for p in active_passes)

    # ── HTML Construction ────────────────────────────────────────────
    style = """
        body { font-family: Arial, sans-serif; font-size: 14px; color: #333; background: #f5f5f5; margin: 0; padding: 0; }
        .container { max-width: 700px; margin: 24px auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.1); }
        .header { background: #1a73e8; color: #fff; padding: 20px 28px; }
        .header h1 { margin: 0; font-size: 20px; }
        .header p { margin: 4px 0 0; font-size: 13px; opacity: .85; }
        .section { padding: 20px 28px; border-bottom: 1px solid #eee; }
        .section:last-child { border-bottom: none; }
        h2 { font-size: 15px; color: #1a73e8; margin: 0 0 12px; text-transform: uppercase; letter-spacing: .5px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { background: #f0f4ff; text-align: left; padding: 7px 10px; color: #555; }
        td { padding: 7px 10px; border-bottom: 1px solid #f0f0f0; }
        tr:last-child td { border-bottom: none; }
        .total-row td { font-weight: bold; background: #f9f9f9; }
        .summary-box { display: inline-block; background: #f0f4ff; border-radius: 6px; padding: 10px 18px; margin: 4px 6px 4px 0; text-align: center; }
        .summary-box .val { font-size: 20px; font-weight: bold; color: #1a73e8; }
        .summary-box .lbl { font-size: 11px; color: #777; margin-top: 2px; }
        .empty { color: #aaa; font-style: italic; font-size: 13px; }
        .footer { background: #f5f5f5; text-align: center; padding: 14px; font-size: 12px; color: #999; }
    """

    def table_rows(agg):
        if not agg:
            return '<tr><td colspan="3" class="empty">No records</td></tr>'
        rows = ''
        total = 0
        for name, d in sorted(agg.items()):
            rows += f'<tr><td>{name}</td><td style="text-align:center">{d["qty"]}</td><td style="text-align:right">{_fmt_inr(d["amount"])}</td></tr>'
            total += d['amount']
        rows += f'<tr class="total-row"><td>Total</td><td></td><td style="text-align:right">{_fmt_inr(total)}</td></tr>'
        return rows

    # ── Section 1: Daily Summary ──────────────────────────────────────
    sec1 = f"""
    <div class="section">
        <h2>📊 Daily Summary — {report_date.strftime('%d %b %Y')}</h2>
        <div>
            <div class="summary-box"><div class="val">{_fmt_inr(rental_total)}</div><div class="lbl">Rentals</div></div>
            <div class="summary-box"><div class="val">{_fmt_inr(sale_total)}</div><div class="lbl">Sales</div></div>
            <div class="summary-box"><div class="val">{_fmt_inr(booking_total)}</div><div class="lbl">Offline Bookings</div></div>
            <div class="summary-box"><div class="val">{_fmt_inr(pass_sold_total)}</div><div class="lbl">Pass Revenue</div></div>
            <div class="summary-box"><div class="val">{_fmt_inr(rental_total + sale_total + booking_total + pass_sold_total)}</div><div class="lbl">Total Revenue</div></div>
        </div>
    </div>"""

    # ── Section 2: Rentals ────────────────────────────────────────────
    sec2 = f"""
    <div class="section">
        <h2>🏸 Rentals</h2>
        <table>
            <thead><tr><th>Item</th><th style="text-align:center">Qty</th><th style="text-align:right">Amount</th></tr></thead>
            <tbody>{table_rows(rental_agg)}</tbody>
        </table>
    </div>"""

    # ── Section 3: Sales ─────────────────────────────────────────────
    sec3 = f"""
    <div class="section">
        <h2>🛒 Sales</h2>
        <table>
            <thead><tr><th>Item</th><th style="text-align:center">Qty</th><th style="text-align:right">Amount</th></tr></thead>
            <tbody>{table_rows(sale_agg)}</tbody>
        </table>
    </div>"""

    # ── Section 4: Offline Bookings ───────────────────────────────────
    booking_rows = ''
    if not bookings:
        booking_rows = '<tr><td colspan="3" class="empty">No offline bookings</td></tr>'
    else:
        for b in bookings:
            booking_rows += f'<tr><td>{b.item_name or "-"}</td><td>{b.description or "-"}</td><td style="text-align:right">{_fmt_inr(b.total_sell or 0)}</td></tr>'
        booking_rows += f'<tr class="total-row"><td colspan="2">Total ({len(bookings)} bookings)</td><td style="text-align:right">{_fmt_inr(booking_total)}</td></tr>'

    sec4 = f"""
    <div class="section">
        <h2>🏟️ Offline Bookings</h2>
        <table>
            <thead><tr><th>Description</th><th>Notes</th><th style="text-align:right">Amount</th></tr></thead>
            <tbody>{booking_rows}</tbody>
        </table>
    </div>"""

    # ── Section 5: Monthly Passes Sold Yesterday ─────────────────────
    pass_sold_rows = ''
    if not passes_sold:
        pass_sold_rows = '<tr><td colspan="4" class="empty">No passes sold</td></tr>'
    else:
        for p in passes_sold:
            pass_sold_rows += f'<tr><td>{p.name}</td><td>{p.slot or "-"}</td><td>{p.end_date.strftime("%d %b %Y") if p.end_date else "-"}</td><td style="text-align:right">{_fmt_inr(p.amount or 0)}</td></tr>'
        pass_sold_rows += f'<tr class="total-row"><td colspan="3">Total ({len(passes_sold)} passes)</td><td style="text-align:right">{_fmt_inr(pass_sold_total)}</td></tr>'

    sec5 = f"""
    <div class="section">
        <h2>🎟️ Monthly Passes Sold</h2>
        <table>
            <thead><tr><th>Name</th><th>Slot</th><th>Valid Till</th><th style="text-align:right">Amount</th></tr></thead>
            <tbody>{pass_sold_rows}</tbody>
        </table>
    </div>"""

    # ── Section 6: Coaching — Active Students ────────────────────────
    student_rows = ''
    if not active_students:
        student_rows = '<tr><td colspan="5" class="empty">No active students</td></tr>'
    else:
        for s in active_students:
            end = s.end_date.strftime('%d %b %Y') if s.end_date else 'Ongoing'
            student_rows += f'<tr><td>{s.name}</td><td>{s.phone or "-"}</td><td>{s.batch_timing or "-"}</td><td style="text-align:right">{_fmt_inr(s.fees or 0)}</td><td>{end}</td></tr>'
        student_rows += f'<tr class="total-row"><td colspan="3">Total ({len(active_students)} students)</td><td style="text-align:right">{_fmt_inr(active_students_fees)}</td><td></td></tr>'

    sec6 = f"""
    <div class="section">
        <h2>🎓 Coaching — Active Students</h2>
        <table>
            <thead><tr><th>Name</th><th>Phone</th><th>Batch</th><th style="text-align:right">Fees</th><th>Valid Till</th></tr></thead>
            <tbody>{student_rows}</tbody>
        </table>
    </div>"""

    # ── Section 7: Coaching — Batches ────────────────────────────────
    batch_rows = ''
    if not batches:
        batch_rows = '<tr><td colspan="4" class="empty">No batches created</td></tr>'
    else:
        for b in batches:
            from sqlalchemy import func
            batch_rows += f'<tr><td>{b.name or "-"}</td><td>{b.start_time} – {b.end_time}</td><td>{b.package or "-"}</td><td style="text-align:right">{_fmt_inr(b.fees or 0)}</td></tr>'

    sec7 = f"""
    <div class="section">
        <h2>⏰ Coaching — Batches ({len(batches)} total)</h2>
        <table>
            <thead><tr><th>Name</th><th>Timing</th><th>Package</th><th style="text-align:right">Fees</th></tr></thead>
            <tbody>{batch_rows}</tbody>
        </table>
    </div>"""

    # ── Section 8: Active Monthly Pass Holders ────────────────────────
    active_pass_rows = ''
    if not active_passes:
        active_pass_rows = '<tr><td colspan="4" class="empty">No active pass holders</td></tr>'
    else:
        for p in active_passes:
            active_pass_rows += f'<tr><td>{p.name}</td><td>{p.mobile or "-"}</td><td style="text-align:right">{_fmt_inr(p.amount or 0)}</td><td>{p.end_date.strftime("%d %b %Y") if p.end_date else "-"}</td></tr>'
        active_pass_rows += f'<tr class="total-row"><td colspan="2">Total ({len(active_passes)} holders)</td><td style="text-align:right">{_fmt_inr(active_pass_total)}</td><td></td></tr>'

    sec8 = f"""
    <div class="section">
        <h2>🎫 Active Monthly Pass Holders</h2>
        <table>
            <thead><tr><th>Name</th><th>Mobile</th><th style="text-align:right">Amount</th><th>Valid Till</th></tr></thead>
            <tbody>{active_pass_rows}</tbody>
        </table>
    </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>{style}</style></head>
<body>
<div class="container">
    <div class="header">
        <h1>Unity Sports Arena — Daily Report</h1>
        <p>Report for {report_date.strftime('%A, %d %B %Y')} &nbsp;|&nbsp; Generated on {today.strftime('%d %b %Y')} at 9:00 AM IST</p>
    </div>
    {sec1}{sec2}{sec3}{sec4}{sec5}{sec6}{sec7}{sec8}
    <div class="footer">Unity Sports Arena Management System &nbsp;|&nbsp; Automated Daily Report</div>
</div>
</body>
</html>"""

    return html, report_date


def send_daily_report(app, db, Transaction, MonthlyPass, CoachingStudent, CoachingBatch):
    """Generate and email the daily report. Called by the scheduler."""
    email_user = os.environ.get('REPORT_EMAIL_USER', '')
    email_pass = os.environ.get('REPORT_EMAIL_PASS', '')

    if not email_user or not email_pass:
        print('[report] ERROR: REPORT_EMAIL_USER or REPORT_EMAIL_PASS env vars not set.')
        return

    try:
        html, report_date = build_report_html(
            app, db, Transaction, MonthlyPass, CoachingStudent, CoachingBatch
        )

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"USA Daily Report — {report_date.strftime('%d %b %Y')}"
        msg['From'] = email_user
        msg['To'] = ', '.join(REPORT_TO)
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(email_user, email_pass)
            server.sendmail(email_user, REPORT_TO, msg.as_string())

        print(f'[report] Daily report for {report_date} sent')
    except Exception as e:
        print(f'[report] Failed to send report: {e}')
        sys.exit(1)


if __name__ == '__main__':
    # Bootstrap Flask + DB so models are available when run as a standalone script
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))

    from app import app, db, Transaction, MonthlyPass, CoachingStudent, CoachingBatch
    send_daily_report(app, db, Transaction, MonthlyPass, CoachingStudent, CoachingBatch)
