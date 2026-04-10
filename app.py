
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime, timedelta, timezone
from functools import wraps
import uuid
import re
import json
from pathlib import Path
from kmo import KMO
from playoo import PlayoO

app = Flask(__name__)
app.secret_key = 'unity_arena_ultra_v18_premium'

# --- India Timezone Helper ---
def get_india_time():
    # Fixed offset for India Standard Time (UTC+5:30)
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).replace(tzinfo=None)

# --- Database Connection ---
DB_URL = 'postgresql://usa_user:unity77@localhost:5432/usa_db'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Models ---
class Product(db.Model):
    __table_args__ = {'schema': 'usam'}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50)) 
    buy_price = db.Column(db.Integer, default=0)
    sell_price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=0)
    low_stock_limit = db.Column(db.Integer, default=5)

class Transaction(db.Model):
    __table_args__ = {'schema': 'usam'}
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50))
    item_name = db.Column(db.String(100))
    category = db.Column(db.String(50)) 
    qty = db.Column(db.Integer)
    total_sell = db.Column(db.Integer)
    total_cost = db.Column(db.Integer)
    court = db.Column(db.Integer, default=1)
    mobile = db.Column(db.String(20))
    description = db.Column(db.Text) 
    created_by = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Completed')
    timestamp = db.Column(db.DateTime, default=get_india_time) # Uses India Time
    
class MonthlyPass(db.Model):
    __table_args__ = {'schema': 'usam'}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    mobile = db.Column(db.String(20))
    court = db.Column(db.Integer) # Added field
    slot = db.Column(db.String(50)) # Added field
    amount = db.Column(db.Integer)
    payment_type = db.Column(db.String(50))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)
    created_by = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=get_india_time)

class Expense(db.Model):
    __table_args__ = {'schema': 'usam'}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    amount = db.Column(db.Integer)
    category = db.Column(db.String(50)) 
    created_by = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=get_india_time) # Uses India Time

class ExternalProfit(db.Model):
    __table_args__ = {'schema': 'usam'}
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50)) 
    amount = db.Column(db.Integer)
    description = db.Column(db.Text)
    created_by = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=get_india_time) # Uses India Time

class Task(db.Model):
    __table_args__ = {'schema': 'usam'}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.String(50))
    priority = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Pending')
    deadline = db.Column(db.Date) # New Field: Deadline
    comments = db.Column(db.Text, default="") # New Field: Comments storage
    created_by = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=get_india_time)
    
class StaffLedger(db.Model):
    __table_args__ = {'schema': 'usam'}
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20)) # 'Income' or 'Expense'
    account = db.Column(db.String(50)) # 'Arun Account', 'Gulesh Account', 'Cash'
    amount = db.Column(db.Integer)
    purpose = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_by = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=get_india_time)

class Conflict(db.Model):
    __table_args__ = {'schema': 'usam'}
    id = db.Column(db.Integer, primary_key=True)
    slot = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    court = db.Column(db.String(100), nullable=False)
    playo_user = db.Column(db.String(255))
    khelomore_user = db.Column(db.String(255))
    resolved = db.Column(db.Boolean, default=False)
    resolution_notes = db.Column(db.Text)
    resolved_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=get_india_time)
    updated_at = db.Column(db.DateTime, default=get_india_time, onupdate=get_india_time)


class Notification(db.Model):
    __table_args__ = {'schema': 'usam'}
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)
    booking_date = db.Column(db.Date)
    court = db.Column(db.String(100))
    error_message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_india_time)

class CoachingStudent(db.Model):
    __table_args__ = {'schema': 'usam'}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    batch_timing = db.Column(db.String(100))
    package = db.Column(db.String(100))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    fees = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=get_india_time)

with app.app_context():
    db.session.execute(text("CREATE SCHEMA IF NOT EXISTS usam;"))
    db.create_all()
    # Migration for new columns
    try:
        db.session.execute(text("ALTER TABLE usam.task ADD COLUMN IF NOT EXISTS deadline DATE;"))
        db.session.execute(text("ALTER TABLE usam.task ADD COLUMN IF NOT EXISTS comments TEXT DEFAULT '';"))
        # Ensure notification table has is_read column and create table if missing
        db.session.execute(text(
            "CREATE TABLE IF NOT EXISTS usam.notification (id SERIAL PRIMARY KEY, source VARCHAR(50) NOT NULL, booking_date DATE, court VARCHAR(100), error_message TEXT NOT NULL, is_read BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
        ))
        db.session.execute(text("ALTER TABLE IF EXISTS usam.notification ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE;"))
        db.session.commit()
    except: pass

with app.app_context():
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS usam.coaching_student (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                batch_timing VARCHAR(100),
                package VARCHAR(100),
                notes TEXT,
                created_by VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        db.session.execute(text("ALTER TABLE usam.coaching_student ADD COLUMN IF NOT EXISTS start_date DATE;"))
        db.session.execute(text("ALTER TABLE usam.coaching_student ADD COLUMN IF NOT EXISTS end_date DATE;"))
        db.session.execute(text("ALTER TABLE usam.coaching_student ADD COLUMN IF NOT EXISTS fees INTEGER DEFAULT 0;"))
        db.session.commit()
    except: pass

# --- Auth ---
USERS = {'ram': 'unity77', 'ranvir': 'unity77', 'amrendra': 'unity77', 'sandeep': 'unity77', 'arun': 'manager123', 'kambale': 'manager123', 'kritika': 'coach77'}
OWNERS = ['ram', 'ranvir', 'amrendra', 'sandeep']
MANAGERS = ['Arun', 'Kambale']
COACHES = ['kritika']

def login_required(role_needed=None):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user' not in session: return redirect(url_for('login'))
            if role_needed:
                user_role = session.get('role')
                if isinstance(role_needed, (list, tuple, set)):
                    if user_role not in role_needed:
                        return "Unauthorized", 403
                elif user_role != role_needed:
                    return "Unauthorized", 403
            # Coaches can only access coaching pages
            if session.get('role') == 'coach' and role_needed != 'coach':
                from flask import request as req
                if not req.path.startswith('/coaching') and req.path != '/logout':
                    return redirect(url_for('coaching'))
            return f(*args, **kwargs)
        return decorated
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('user').lower(), request.form.get('pass')
        if u in USERS and USERS[u] == p:
            session['user'] = u.capitalize()
            if u in OWNERS:
                session['role'] = 'owner'
            elif u in COACHES:
                session['role'] = 'coach'
            else:
                session['role'] = 'manager'
            if session['role'] == 'coach':
                return redirect(url_for('coaching'))
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required()
def index():
    now_ist = get_india_time()
    prods = Product.query.order_by(Product.name).all()
    # Query filtered by India current date
    today_txns = Transaction.query.filter(db.func.date(Transaction.timestamp) == now_ist.date()).order_by(Transaction.timestamp.desc()).all()
    today_total = sum(t.total_sell for t in today_txns if t.status == 'Completed')
    today_txns = Transaction.query.filter(db.func.date(Transaction.timestamp) >= now_ist.date()-timedelta(days=1)).order_by(Transaction.timestamp.desc()).all()
    slots = ["6 to 7 AM", "7 to 8AM", "8 to 9 AM", "9 to 10 AM", "10 to 11 AM", "11 to 12 AM", "12 to 1 PM", "1 to 2 PM", "2 to 3 PM", "3 to 4 PM", "4 to 5 PM", "5 to 6 PM", "6 to 7 PM", "7 to 8 PM", "8 to 9 PM", "9 to 10 PM", "10 to 11 PM", "11 to 12 PM", "12 to 1 AM", "1 to 2 AM"]
    return render_template('index.html', products=prods, slots=slots, today_txns=today_txns, today_total=today_total)

# --- Monthly Pass Routes ---
@app.route('/passes')
@login_required()
def passes():
    all_passes = MonthlyPass.query.order_by(MonthlyPass.timestamp.desc()).all()
    today = get_india_time().date()
    default_end = (today + timedelta(days=30)).strftime('%Y-%m-%d')
    # Define slots here to pass to the template
    slots = ["6 to 7 AM", "7 to 8AM", "8 to 9 AM", "9 to 10 AM", "10 to 11 AM", "11 to 12 AM", "12 to 1 PM", "1 to 2 PM", "2 to 3 PM", "3 to 4 PM", "4 to 5 PM", "5 to 6 PM", "6 to 7 PM", "7 to 8 PM", "8 to 9 PM", "9 to 10 PM", "10 to 11 PM", "11 to 12 PM", "12 to 1 AM", "1 to 2 AM"]
    return render_template('passes.html', passes=all_passes, today=today, default_end=default_end, slots=slots)

@app.route('/pass/check_conflict', methods=['POST'])
@login_required()
def check_conflict():
    data = request.json
    court = int(data.get('court'))
    slot = data.get('slot')
    start = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
    
    # Check for overlapping active passes
    conflict = MonthlyPass.query.filter(
        MonthlyPass.court == court,
        MonthlyPass.slot == slot,
        MonthlyPass.end_date >= start
    ).first()
    
    if conflict:
        return jsonify({
            "conflict": True, 
            "message": f"Conflict! Court {court} at {slot} is already taken by {conflict.name} until {conflict.end_date.strftime('%d %b')}."
        })
    return jsonify({"conflict": False})

@app.route('/pass/add', methods=['POST'])
@login_required()
def add_pass():
    pay_mode = request.form['payment_type']
    name = request.form['name']
    amount = int(request.form['amount'])
    
    new_pass = MonthlyPass(
        name=name,
        mobile=request.form['mobile'],
        court=int(request.form['court']),
        slot=request.form['slot'],
        amount=amount,
        payment_type=pay_mode,
        start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
        end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date(),
        description=request.form.get('desc', ''),
        created_by=session['user']
    )
    db.session.add(new_pass)
    
    # 1. Standard Ledger Entry (For Daily Revenue)
    txn = Transaction(
        order_id=str(uuid.uuid4())[:8],
        item_name=f"Pass: {name}",
        category='Booking',
        qty=1,
        total_sell=amount,
        total_cost=0,
        court=new_pass.court,
        mobile=new_pass.mobile,
        description=f"Monthly Pass ({pay_mode})",
        created_by=session['user'],
        status='Completed'
    )
    db.session.add(txn)

    # 2. Automatic StaffLedger Entry for Offline/Staff Payments
    offline_modes = ['Cash', 'Arun Account', 'Gulesh Account']
    if pay_mode in offline_modes:
        staff_log = StaffLedger(
            type='Income',
            account=pay_mode,
            amount=amount,
            purpose=f"Monthly Pass: {name}",
            description="Auto-generated from Pass Page",
            created_by=session['user']
        )
        db.session.add(staff_log)
    
    db.session.commit()
    return redirect(url_for('passes'))

@app.route('/pass/delete/<int:id>', methods=['POST'])
@login_required('owner')
def delete_pass(id):
    p = MonthlyPass.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
    return redirect(url_for('passes'))

@app.route('/staff_ledger')
@login_required()
def staff_ledger():
    logs = StaffLedger.query.order_by(StaffLedger.timestamp.desc()).all()
    
    # Calculate current balances held by staff/cash
    balances = {"Arun Account": 0, "Gulesh Account": 0, "Cash": 0}
    for log in logs:
        if log.type == 'Income':
            balances[log.account] = balances.get(log.account, 0) + log.amount
        else:
            balances[log.account] = balances.get(log.account, 0) - log.amount
            
    return render_template('staff_ledger.html', logs=logs, balances=balances)

@app.route('/staff_ledger/add', methods=['POST'])
@login_required()
def add_staff_log():
    log_type = request.form.get('type')
    amount = int(request.form.get('amount'))
    acc = request.form.get('account')
    purp = request.form.get('purpose')
    
    new_log = StaffLedger(
        type=log_type,
        account=acc,
        amount=amount,
        purpose=purp,
        description=request.form.get('desc'),
        created_by=session['user']
    )
    db.session.add(new_log)
    
    # Mirroring to Dashboard Analytics
    if log_type == 'Income':
        # Counted as External Revenue
        db.session.add(ExternalProfit(
            source=f"Staff Col: {acc}",
            amount=amount,
            description=f"{purp}",
            created_by=session['user']
        ))
    else:
        # Counted as Business Expense
        db.session.add(Expense(
            title=f"Staff Paid: {purp} ({acc})",
            amount=amount,
            category='Misc',
            created_by=session['user']
        ))
        
    db.session.commit()
    return redirect(url_for('staff_ledger'))

@app.route('/tasks')
@login_required()
def tasks():
    now_ist = get_india_time().date()
    if session['role'] == 'owner':
        all_tasks = Task.query.order_by(Task.timestamp.desc()).all()
    else:
        all_tasks = Task.query.filter_by(assigned_to=session['user']).order_by(Task.timestamp.desc()).all()
    
    # Calculate days remaining for display
    for t in all_tasks:
        if t.deadline:
            diff = (t.deadline - now_ist).days
            t.days_left = diff
        else:
            t.days_left = None
            
    return render_template('tasks.html', tasks=all_tasks, managers=MANAGERS, today=now_ist)

# --- Conflict Management Routes ---
@app.route('/conflicts')
@login_required()
def conflicts():
    now_ist = get_india_time().date()
    resolved_filter = request.args.get('filter', 'all')
    
    query = Conflict.query.order_by(Conflict.created_at.desc())
    
    if resolved_filter == 'resolved':
        query = query.filter_by(resolved=True)
    elif resolved_filter == 'unresolved':
        query = query.filter_by(resolved=False)
    
    all_conflicts = query.all()
    
    # Get summary
    total = Conflict.query.count()
    resolved_count = Conflict.query.filter_by(resolved=True).count()
    unresolved_count = total - resolved_count
    
    return render_template('conflicts.html', 
                         conflicts=all_conflicts, 
                         resolved_filter=resolved_filter,
                         total=total,
                         resolved=resolved_count,
                         unresolved=unresolved_count,
                         today=now_ist)

@app.route('/conflict/add', methods=['POST'])
@login_required()
def add_conflict():
    """Add a new conflict record"""
    try:
        data = request.json
        new_conflict = Conflict(
            slot=data.get('slot'),
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
            court=data.get('court'),
            playo_user=data.get('playo_user'),
            khelomore_user=data.get('khelomore_user'),
            resolved=False
        )
        db.session.add(new_conflict)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Conflict recorded - {new_conflict.playo_user} vs {new_conflict.khelomore_user} on {new_conflict.slot}",
            "conflict": {
                "id": new_conflict.id,
                "slot": new_conflict.slot,
                "date": new_conflict.date.strftime('%Y-%m-%d'),
                "court": new_conflict.court,
                "playo_user": new_conflict.playo_user,
                "khelomore_user": new_conflict.khelomore_user,
                "resolved": new_conflict.resolved
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/conflict/resolve/<int:id>', methods=['POST'])
@login_required('owner')
def resolve_conflict(id):
    """Mark conflict as resolved with optional notes"""
    try:
        conflict = Conflict.query.get(id)
        if not conflict:
            return jsonify({"status": "error", "message": "Conflict not found"}), 404
        
        data = request.json
        conflict.resolved = True
        conflict.resolution_notes = data.get('notes', '')
        conflict.resolved_by = session['user']
        conflict.updated_at = get_india_time()
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Conflict #{id} marked as resolved"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/conflict/delete/<int:id>', methods=['POST'])
@login_required()
def delete_conflict(id):
    """Delete a conflict record"""
    try:
        conflict = Conflict.query.get(id)
        if not conflict:
            return jsonify({"status": "error", "message": "Conflict not found"}), 404
        
        db.session.delete(conflict)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Conflict #{id} deleted successfully"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/conflicts/unresolved')
@login_required()
def get_unresolved_conflicts():
    """API endpoint for checking unresolved conflicts (for notifications)"""
    unresolved = Conflict.query.filter_by(resolved=False).order_by(Conflict.created_at.desc()).all()
    return jsonify({
        "status": "success",
        "count": len(unresolved),
        "conflicts": [{
            "id": c.id,
            "slot": c.slot,
            "date": c.date.strftime('%Y-%m-%d'),
            "court": c.court,
            "playo_user": c.playo_user,
            "khelomore_user": c.khelomore_user,
            "created_at": c.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for c in unresolved]
    })


@app.route('/api/notifications/unread_count')
@login_required()
def notifications_unread_count():
    count = Notification.query.filter_by(is_read=False).count()
    latest = Notification.query.filter_by(is_read=False).order_by(Notification.created_at.desc()).first()
    latest_item = None
    if latest:
        latest_item = {
            'id': latest.id,
            'source': latest.source,
            'booking_date': latest.booking_date.strftime('%Y-%m-%d') if latest.booking_date else None,
            'court': latest.court,
            'error_message': latest.error_message,
            'created_at': latest.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    return jsonify({'status': 'success', 'count': count, 'latest': latest_item})


@app.route('/api/notifications/unread')
@login_required()
def notifications_unread_list():
    items = Notification.query.filter_by(is_read=False).order_by(Notification.created_at.desc()).limit(10).all()
    return jsonify({
        'status': 'success',
        'notifications': [{
            'id': n.id,
            'source': n.source,
            'booking_date': n.booking_date.strftime('%Y-%m-%d') if n.booking_date else None,
            'court': n.court,
            'error_message': n.error_message,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for n in items]
    })


@app.route('/api/notifications/mark_read', methods=['POST'])
@login_required()
def notifications_mark_read():
    data = request.json or {}
    ids = data.get('ids')
    mark_all = data.get('all', False)
    try:
        if mark_all:
            Notification.query.filter_by(is_read=False).update({'is_read': True})
        elif ids and isinstance(ids, list):
            Notification.query.filter(Notification.id.in_(ids)).update({'is_read': True}, synchronize_session=False)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/task/add', methods=['POST'])
@login_required('owner')
def add_task():
    deadline_val = request.form.get('deadline')
    deadline = datetime.strptime(deadline_val, '%Y-%m-%d').date() if deadline_val else None
    t = Task(
        title=request.form['title'],
        description=request.form['desc'],
        assigned_to=request.form['assignee'],
        priority=request.form['priority'],
        deadline=deadline,
        created_by=session['user']
    )
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('tasks'))

@app.route('/task/comment/<int:id>', methods=['POST'])
@login_required()
def add_comment(id):
    t = Task.query.get(id)
    comment = request.form.get('comment')
    if t and comment:
        timestamp = get_india_time().strftime('%d %b, %H:%M')
        new_entry = f"[{timestamp}] {session['user']}: {comment}\n"
        t.comments = (t.comments or "") + new_entry
        db.session.commit()
    return redirect(url_for('tasks'))

@app.route('/task/complete/<int:id>', methods=['POST'])
@login_required()
def complete_task(id):
    t = Task.query.get(id)
    if t:
        t.status = 'Completed'
        db.session.commit()
    return redirect(url_for('tasks'))

@app.route('/task/delete/<int:id>', methods=['POST'])
@login_required('owner')
def delete_task(id):
    t = Task.query.get(id)
    if t:
        db.session.delete(t)
        db.session.commit()
    return redirect(url_for('tasks'))

@app.route('/submit_order', methods=['POST'])
@login_required()
def submit_order():
    data = request.json
    order_id = str(uuid.uuid4())[:8]
    status = data.get('status', 'Completed')
    for item in data['items']:
        p = Product.query.filter_by(name=item['name']).first()
        cost = int(p.buy_price * item['qty']) if (p and p.category == 'Sale') else 0
        if p and p.category == 'Sale': p.stock -= item['qty']
        txn = Transaction(order_id=order_id, item_name=item['name'], category=item['category'], qty=item['qty'], total_sell=int(item['price'] * item['qty']), total_cost=cost, court=int(item.get('court', 1)), mobile=item.get('mobile', ''), description=item.get('desc', ''), created_by=session['user'], status=status, timestamp=get_india_time())
        db.session.add(txn)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/complete_txn/<int:id>', methods=['POST'])
@login_required()
def complete_txn(id):
    t = Transaction.query.get(id)
    if t:
        t.status = 'Completed'
        t.timestamp = get_india_time()
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/undo_txn/<int:id>', methods=['POST'])
@login_required()
def undo_txn(id):
    t = Transaction.query.get(id)
    if t and t.category == 'Sale':
        p = Product.query.filter_by(name=t.item_name).first()
        if p: p.stock += t.qty
    db.session.delete(t)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required('owner')
def dashboard():
    now_ist = get_india_time()
    list_to_check = ['Sale','Rent','Booking']
    start = request.args.get('start', (now_ist - timedelta(days=7)).strftime('%Y-%m-%d'))
    end = request.args.get('end', now_ist.strftime('%Y-%m-%d'))
    cat_filter = request.args.getlist('cat')
    t_q = Transaction.query.filter(db.func.date(Transaction.timestamp).between(start, end))
    e_q = Expense.query.filter(db.func.date(Expense.timestamp).between(start, end))
    ext_q = ExternalProfit.query.filter(db.func.date(ExternalProfit.timestamp).between(start, end))
    t_q = t_q.filter(db.false())
    e_q = ext_q.filter(db.false())
    ext_q = ext_q.filter(db.false())
    if cat_filter ==[]:
        cat_filter.append('All')

    if ('All' in cat_filter):
        t_q = Transaction.query.filter(db.func.date(Transaction.timestamp).between(start, end))
        e_q = Expense.query.filter(db.func.date(Expense.timestamp).between(start, end))
        ext_q = ExternalProfit.query.filter(db.func.date(ExternalProfit.timestamp).between(start, end))
        
    if any(value in list_to_check for value in cat_filter):
        t_q = Transaction.query.filter(db.func.date(Transaction.timestamp).between(start, end))
        e_q = Expense.query.filter(db.func.date(Expense.timestamp).between(start, end))
        t_q = t_q.filter(Transaction.category.in_(cat_filter))
        e_q = e_q.filter(Expense.category .in_(cat_filter))
        
    if 'External' in cat_filter:
        ext_q = ExternalProfit.query.filter(db.func.date(ExternalProfit.timestamp).between(start, end))
        
    if 'Expense' in cat_filter:
        e_q = Expense.query.filter(db.func.date(Expense.timestamp).between(start, end))

    txns, exps, ext = t_q.all(), e_q.all(), ext_q.all()
    rev = sum(t.total_sell for t in txns if t.status == 'Completed') + sum(p.amount for p in ext)
    exp_total = sum(e.amount for e in exps)
    
    chart_data = {}
    for t in txns: 
        if t.status == 'Completed':
            chart_data[t.category] = chart_data.get(t.category, 0) + t.total_sell
    for p in ext: chart_data[p.source] = chart_data.get(p.source, 0) + p.amount
    for e in exps: chart_data[f"Exp: {e.category}"] = chart_data.get(f"Exp: {e.category}", 0) + e.amount

    return render_template('dashboard.html', revenue=rev, expenses_total=exp_total, profit=rev-exp_total, txns=txns, exps=exps, ext=ext, start=start, end=end, cat_filter=cat_filter, chart_data=chart_data)

@app.route('/inventory')
@login_required('owner')
def inventory():
    products = Product.query.order_by(Product.name).all()
    return render_template('inventory.html', products=products)

@app.route('/product/add', methods=['POST'])
@login_required('owner')
def add_product():
    name, qty, buy, sell, cat = request.form['name'], int(request.form['stock']), int(request.form['buy']), int(request.form['sell']), request.form['cat']
    db.session.add(Expense(title=f"Stock Purchase: {name} (x{qty})", amount=buy*qty, category=cat, created_by=session['user']))
    p = Product.query.filter_by(name=name).first()
    if p:
        p.stock += qty; p.buy_price, p.sell_price = buy, sell
    else:
        db.session.add(Product(name=name, category=cat, buy_price=buy, sell_price=sell, stock=qty))
    db.session.commit()
    return redirect(url_for('inventory'))

@app.route('/product/update/<int:pid>', methods=['POST'])
@login_required('owner')
def update_product(pid):
    p = Product.query.get_or_404(pid)
    data = request.get_json()
    p.name = data.get('name', p.name).strip()
    p.category = data.get('category', p.category)
    p.buy_price = int(data.get('buy_price', p.buy_price))
    p.sell_price = int(data.get('sell_price', p.sell_price))
    p.stock = int(data.get('stock', p.stock))
    p.low_stock_limit = int(data.get('low_stock_limit', p.low_stock_limit))
    db.session.commit()
    return jsonify(success=True)

@app.route('/product/delete/<int:pid>', methods=['POST'])
@login_required('owner')
def delete_product(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify(success=True)

@app.route('/add_external', methods=['POST'])
@login_required()
def add_external():
    date_val = request.form.get('date')
    ts = datetime.strptime(date_val, '%Y-%m-%d') if date_val else get_india_time()
    db.session.add(ExternalProfit(source=request.form['source'], amount=int(request.form['amount']), description=request.form['desc'], created_by=session['user'], timestamp=ts))
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_expense', methods=['POST'])
@login_required()
def add_expense():
    db.session.add(Expense(title=request.form['title'], amount=int(request.form['amount']), category=request.form['cat'], created_by=session['user'], timestamp=get_india_time()))
    db.session.commit()
    return redirect(url_for('dashboard'))

# --- Booking Comparison (Playo vs Khelomore) ---
@app.route('/manager/bookings')
@login_required(['owner', 'manager'])
def manager_bookings():
    today = get_india_time().date()
    selected_date = request.args.get('date', today.strftime('%Y-%m-%d'))
    errors = []
    success_message = request.args.get('cred_status', '')

    try:
        datetime.strptime(selected_date, '%Y-%m-%d')
    except ValueError:
        selected_date = today.strftime('%Y-%m-%d')
        errors.append('Invalid date selected. Showing today instead.')

    court_numbers = [1, 2, 3, 4]
    hour_labels = [f"{h:02d}:00 - {(h + 1) % 24:02d}:00" for h in range(24)]
    playo_grid = {label: {c: [] for c in court_numbers} for label in hour_labels}
    kmo_grid = {label: {c: [] for c in court_numbers} for label in hour_labels}

    def parse_hour(time_val):
        if not time_val:
            return None
        text_val = str(time_val).strip()
        formats = ['%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M%p', '%H']
        for fmt in formats:
            try:
                return datetime.strptime(text_val, fmt).hour
            except ValueError:
                continue
        if 'T' in text_val:
            try:
                return datetime.fromisoformat(text_val.replace('Z', '+00:00')).hour
            except ValueError:
                pass
        return None

    def parse_minutes(time_val):
        if not time_val:
            return None
        text_val = str(time_val).strip()
        formats = ['%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M%p', '%H']
        for fmt in formats:
            try:
                parsed = datetime.strptime(text_val, fmt)
                return parsed.hour * 60 + parsed.minute
            except ValueError:
                continue
        if 'T' in text_val:
            try:
                parsed = datetime.fromisoformat(text_val.replace('Z', '+00:00'))
                return parsed.hour * 60 + parsed.minute
            except ValueError:
                pass
        return None

    def expand_hours(start_time, end_time):
        start_m = parse_minutes(start_time)
        end_m = parse_minutes(end_time)
        if start_m is None:
            return []
        if end_m is None:
            return [start_m // 60]

        # Handle overnight slots by rolling end to next day.
        if end_m <= start_m:
            end_m += 24 * 60

        start_h = start_m // 60
        end_h = (end_m - 1) // 60
        return [h % 24 for h in range(start_h, end_h + 1)]

    def parse_court_number(court_name):
        if not court_name:
            return None
        match = re.search(r'([1-4])', str(court_name))
        if not match:
            return None
        return int(match.group(1))

    def normalize_kmo_status(status_raw):
        status_text = str(status_raw or '').strip()
        lowered = status_text.lower()
        if 'bulk slots blocked by vendor' in lowered or 'blocked by vendor' in lowered:
            return 'Vendor Block', status_text or 'Blocked by Vendor'
        if not status_text:
            return '-', '-'
        if status_text.isupper() and len(status_text) > 3:
            return status_text.title(), status_text
        return status_text, status_text

    try:
        playo_data = PlayoO().extract_all_data(selected_date)
        if isinstance(playo_data, dict):
            errors.append(playo_data.get('message', 'Could not fetch Playo data.'))
        elif playo_data is not None and not playo_data.empty:
            for row in playo_data.to_dict(orient='records'):
                customer = str(row.get('customerName') or '').strip()
                booking_id = row.get('bookingId')
                blocked = bool(row.get('blocked'))
                available = row.get('available')
                status = str(row.get('status') or '-').strip()
                # Keep only slot rows that indicate booking/blocking
                if customer or booking_id or blocked or available in (0, False):
                    hour = parse_hour(row.get('slotTime'))
                    court_num = parse_court_number(row.get('courtName'))
                    if hour is None or court_num not in court_numbers:
                        continue
                    slot_label = hour_labels[hour]
                    playo_grid[slot_label][court_num].append({
                        'customer': customer or '-',
                        'status': 'Blocked' if blocked else (status or 'Booked'),
                        'booking_id': booking_id or '-'
                    })
    except Exception as e:
        errors.append(f'Playo fetch error: {str(e)}')

    try:
        kmo = KMO()
        for court_name in ['Court_1', 'Court_2', 'Court_3', 'Court_4']:
            court_df = kmo.extract_relevant_data(selected_date, court_name)
            if court_df is None:
                continue
            if court_df.empty:
                continue
            for row in court_df.to_dict(orient='records'):
                status_text = str(row.get('timeslotStatus') or '').strip().lower()
                reason = str(row.get('timeslotReason') or '').strip()
                customer = str(row.get('customerName') or '').strip()
                booking_id = row.get('bookingId')
                if customer or reason or booking_id or status_text not in ('', 'available', 'open', 'unblocked'):
                    hours = expand_hours(row.get('startTime'), row.get('endTime'))
                    if not hours:
                        hour = parse_hour(row.get('startTime'))
                        hours = [hour] if hour is not None else []
                    court_num = parse_court_number(row.get('propertyName') or court_name)
                    if not hours or court_num not in court_numbers:
                        continue
                    display_status, full_status = normalize_kmo_status(row.get('timeslotStatus'))
                    reason_clean = reason if reason.lower() not in ('na', 'n/a', 'none', 'null', '-') else '-'
                    for hour in hours:
                        slot_label = hour_labels[hour]
                        kmo_grid[slot_label][court_num].append({
                            'customer': customer or '-',
                            'status': display_status,
                            'status_full': full_status,
                            'reason': reason_clean
                        })
    except Exception as e:
        errors.append(f'Khelomore fetch error: {str(e)}')

    playo_count = sum(
        len(playo_grid[label][court])
        for label in hour_labels
        for court in court_numbers
    )
    kmo_count = sum(
        len(kmo_grid[label][court])
        for label in hour_labels
        for court in court_numbers
    )

    return render_template(
        'manager_bookings.html',
        selected_date=selected_date,
        hour_labels=hour_labels,
        court_numbers=court_numbers,
        playo_grid=playo_grid,
        kmo_grid=kmo_grid,
        playo_count=playo_count,
        kmo_count=kmo_count,
        errors=errors,
        success_message=success_message
    )


@app.route('/manager/bookings/update_tokens', methods=['POST'])
@login_required(['owner', 'manager'])
def manager_update_tokens():
    selected_date = request.form.get('selected_date') or get_india_time().strftime('%Y-%m-%d')
    km_cookie = (request.form.get('km_cookie') or '').strip()
    km_key = (request.form.get('km_key') or '').strip()
    playo_cookie = (request.form.get('playo_cookie') or '').strip()
    playo_key = (request.form.get('playo_key') or '').strip()

    if not any([km_cookie, km_key, playo_cookie, playo_key]):
        return redirect(url_for('manager_bookings', date=selected_date, cred_status='No values submitted.'))

    constant_path = Path(__file__).resolve().parent / 'constant.py'
    content = constant_path.read_text(encoding='utf-8')

    def upsert_literal(src, key_name, value):
        if not value:
            return src
        quoted = json.dumps(value)
        pattern = rf'^{key_name}\s*=\s*".*"$'
        replacement = f'{key_name}={quoted}'
        updated, count = re.subn(pattern, replacement, src, flags=re.MULTILINE)
        if count == 0:
            updated = updated.rstrip() + f'\n{replacement}\n'
        return updated

    content = upsert_literal(content, 'KM_COOKIE', km_cookie)
    content = upsert_literal(content, 'KM_KEY', km_key)
    content = upsert_literal(content, 'PLAYO_COOKIE', playo_cookie)
    content = upsert_literal(content, 'PLAYO_KEY', playo_key)

    constant_path.write_text(content, encoding='utf-8')

    return redirect(url_for('manager_bookings', date=selected_date, cred_status='Credentials updated in constant.py'))

# --- Coaching Students Routes ---
@app.route('/coaching')
@login_required(['owner', 'coach'])
def coaching():
    students = CoachingStudent.query.order_by(CoachingStudent.timestamp.desc()).all()
    today = get_india_time().date()
    return render_template('coaching.html', students=students, today=today)

@app.route('/coaching/add', methods=['POST'])
@login_required(['owner', 'coach'])
def add_coaching_student():
    start_raw = request.form.get('start_date')
    end_raw = request.form.get('end_date')
    s = CoachingStudent(
        name=request.form['name'],
        phone=request.form.get('phone', ''),
        batch_timing=request.form.get('batch_timing', ''),
        package=request.form.get('package', ''),
        start_date=datetime.strptime(start_raw, '%Y-%m-%d').date() if start_raw else None,
        end_date=datetime.strptime(end_raw, '%Y-%m-%d').date() if end_raw else None,
        fees=int(request.form.get('fees') or 0),
        notes=request.form.get('notes', ''),
        created_by=session['user']
    )
    db.session.add(s)
    db.session.commit()
    return redirect(url_for('coaching'))

@app.route('/coaching/edit/<int:id>', methods=['POST'])
@login_required(['owner', 'coach'])
def edit_coaching_student(id):
    s = CoachingStudent.query.get_or_404(id)
    start_raw = request.form.get('start_date')
    end_raw = request.form.get('end_date')
    s.name = request.form['name']
    s.phone = request.form.get('phone', '')
    s.batch_timing = request.form.get('batch_timing', '')
    s.package = request.form.get('package', '')
    s.start_date = datetime.strptime(start_raw, '%Y-%m-%d').date() if start_raw else None
    s.end_date = datetime.strptime(end_raw, '%Y-%m-%d').date() if end_raw else None
    s.fees = int(request.form.get('fees') or 0)
    s.notes = request.form.get('notes', '')
    db.session.commit()
    return redirect(url_for('coaching'))

@app.route('/coaching/delete/<int:id>', methods=['POST'])
@login_required('owner')
def delete_coaching_student(id):
    s = CoachingStudent.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for('coaching'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
