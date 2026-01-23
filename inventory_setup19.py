import os

if not os.path.exists('templates'):
    os.makedirs('templates')

APP_PY = r"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime, timedelta, timezone
from functools import wraps
import uuid

app = Flask(__name__)
app.secret_key = 'unity_arena_ultra_v18_premium'

# --- India Timezone Helper ---
def get_india_time():
    # Fixed offset for India Standard Time (UTC+5:30)
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).replace(tzinfo=None)

# --- Database Connection ---
DB_URL = 'postgresql://neondb_owner:npg_lXSIMtk05eHv@ep-bold-wave-adctsiey-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require'
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

with app.app_context():
    db.session.execute(text("CREATE SCHEMA IF NOT EXISTS usam;"))
    db.create_all()
    # Migration for new columns
    try:
        db.session.execute(text("ALTER TABLE usam.task ADD COLUMN IF NOT EXISTS deadline DATE;"))
        db.session.execute(text("ALTER TABLE usam.task ADD COLUMN IF NOT EXISTS comments TEXT DEFAULT '';"))
        db.session.commit()
    except: pass

# --- Auth ---
USERS = {'ram': 'unity77', 'ranvir': 'unity77', 'amrendra': 'unity77', 'sandeep': 'unity77', 'arun': 'manager123', 'gulesh': 'manager123'}
OWNERS = ['ram', 'ranvir', 'amrendra', 'sandeep']
MANAGERS = ['Arun', 'Gulesh']

def login_required(role_needed=None):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user' not in session: return redirect(url_for('login'))
            if role_needed == 'owner' and session.get('role') != 'owner': return "Unauthorized", 403
            return f(*args, **kwargs)
        return decorated
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('user').lower(), request.form.get('pass')
        if u in USERS and USERS[u] == p:
            session['user'] = u.capitalize()
            session['role'] = 'owner' if u in OWNERS else 'manager'
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
"""

# ... (Rest of HTML strings remain same as the previous response with the 'Pending' feature)
BASE_HTML = r"""
<!DOCTYPE html><html><head>
    <title>Unity Shuttle Arena ERP</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background:#f4f7fa; font-family: 'Inter', system-ui, -apple-system, sans-serif; }
        .navbar { background: #111827 !important; padding: 0.8rem 1.5rem; }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .btn-primary { background: #2563eb; border: none; border-radius: 8px; }
        #loader { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.8); z-index: 9999; display: none; justify-content: center; align-items: center; }
        .spinner { width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #2563eb; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .low-stock { border: 2px solid #ef4444 !important; animation: glow 2s infinite; }
        @keyframes glow { 0%, 100% { box-shadow: 0 0 5px rgba(239, 68, 68, 0.2); } 50% { box-shadow: 0 0 15px rgba(239, 68, 68, 0.5); } }
        .status-pending { background: #fffbeb; color: #92400e; border: 1px solid #fef3c7; }
    </style>
</head>
<body>
    <div id="loader"><div class="spinner"></div></div>
    <nav class="navbar navbar-expand-lg navbar-dark shadow mb-4">
        <a class="navbar-brand fw-bold" href="/">🏸 Unity Shuttle Arena</a>
        <div class="ms-auto d-flex align-items-center gap-2">
            {% if session['role'] == 'owner' %}
            <a href="/dashboard" class="btn btn-sm btn-outline-light">Analytics</a>
            <a href="/inventory" class="btn btn-sm btn-outline-light">Stock</a>
            {% endif %}
            <a href="/passes" class="btn btn-sm btn-info text-white">Monthly Pass</a>
            <a href="/staff_ledger" class="btn btn-sm btn-outline-info text-white">Staff Ledger</a>
            <a href="/tasks" class="btn btn-sm btn-warning">Tasks</a>
            <a href="/" class="btn btn-sm btn-primary">POS</a>
            <a href="/logout" class="btn btn-sm btn-danger">Logout</a>
        </div>
    </nav>
    <div class="container-fluid px-4">{% block content %}{% endblock %}</div>
    <script>
        function showLoader() { document.getElementById('loader').style.display = 'flex'; }
        window.addEventListener('beforeunload', showLoader);
        document.querySelectorAll('form').forEach(f => f.addEventListener('submit', function(e) { if(!f.classList.contains('no-loader')) showLoader(); }));
    </script>
    {% block scripts %}{% endblock %}
</body></html>
"""


# --- NEW PASSES HTML ---
PASSES_HTML = r"""
{% extends "base.html" %}
{% block content %}
<div class="row g-4">
    <div class="col-md-4">
        <div class="card p-4 shadow-sm border-0">
            <h5 class="fw-bold mb-4">Monthly Pass Entry</h5>
            <form id="passForm" action="/pass/add" method="POST">
                <div class="mb-2"><label class="small fw-bold">Player Name</label><input name="name" class="form-control" required></div>
                <div class="mb-2"><label class="small fw-bold">Mobile</label><input name="mobile" class="form-control" required></div>
                
                <div class="row">
                    <div class="col-6 mb-2">
                        <label class="small fw-bold">Court</label>
                        <select name="court" id="p_court" class="form-select"><option>1</option><option>2</option><option>3</option><option>4</option></select>
                    </div>
                    <div class="col-6 mb-2">
                        <label class="small fw-bold">Slot</label>
                        <select name="slot" id="p_slot" class="form-select" onchange="updatePrice()">
                            {% for s in slots %}<option value="{{s}}">{{s}}</option>{% endfor %}
                        </select>
                    </div>
                </div>

                <div class="mb-2">
                    <label class="small fw-bold text-primary">Price (Editable)</label>
                    <input type="number" name="amount" id="p_price" class="form-control fw-bold" value="4900" required>
                </div>

                <div class="row">
                    <div class="col-6 mb-2"><label class="small fw-bold">Start Date</label><input type="date" name="start_date" id="p_start" class="form-control" value="{{today}}" required></div>
                    <div class="col-6 mb-2"><label class="small fw-bold">End Date</label><input type="date" name="end_date" class="form-control" value="{{default_end}}" required></div>
                </div>

                <div class="mb-2">
                    <label class="small fw-bold">Payment Mode</label>
                    <select name="payment_type" class="form-select">
                        <option>UPI (Direct)</option>
                        <option>Cash</option>
                        <option>Arun Account</option>
                        <option>Gulesh Account</option>
                    </select>
                </div>
                <div class="mb-3"><label class="small fw-bold">Description</label><textarea name="desc" class="form-control" rows="2"></textarea></div>
                
                <button type="button" onclick="validateConflict()" class="btn btn-primary w-100 fw-bold">Activate Pass</button>
            </form>
        </div>
    </div>

    <div class="col-md-8">
        <div class="card p-0 shadow-sm border-0">
            <div class="p-3 bg-white border-bottom fw-bold">Active Monthly Passes</div>
            <div class="table-responsive">
                <table class="table table-hover mb-0">
                    <thead class="table-light small">
                        <tr><th>Player</th><th>Court/Slot</th><th>Validity</th><th>Description</th><th>Paid</th><th>Status</th><th>Action</th></tr>
                    </thead>
                    <tbody class="small">
                        {% for p in passes %}
                        <tr>
                            <td><b>{{p.name}}</b><br><small class="text-muted">{{p.mobile}}</small></td>
                            <td>C{{p.court}} | {{p.slot}}</td>
                            <td>{{p.start_date.strftime('%d %b')}} to {{p.end_date.strftime('%d %b')}}</td>
                            <td><small>{{p.description or '-'}}</small></td>
                            <td class="text-success fw-bold">₹{{p.amount}}</td>
                            <td>{% if p.end_date >= today %}<span class="badge bg-success">Active</span>{% else %}<span class="badge bg-secondary">Expired</span>{% endif %}</td>
                            <td>{% if session['role'] == 'owner' %}<form action="/pass/delete/{{p.id}}" method="POST"><button class="btn btn-link text-danger p-0">✕</button></form>{% endif %}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
function updatePrice() {
    const slot = document.getElementById('p_slot').value;
    const priceInput = document.getElementById('p_price');
    const isPM = slot.includes("PM");
    const hour = parseInt(slot);
    // Pricing rule
    if (isPM && hour >= 5 && hour < 12) { priceInput.value = 5900; } 
    else { priceInput.value = 4900; }
}

async function validateConflict() {
    const payload = {
        court: document.getElementById('p_court').value,
        slot: document.getElementById('p_slot').value,
        start_date: document.getElementById('p_start').value
    };

    const response = await fetch('/pass/check_conflict', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    if (result.conflict) {
        alert(result.message); // The immediate popup
    } else {
        document.getElementById('passForm').submit();
    }
}
updatePrice();
</script>
{% endblock %}
"""

STAFFLENDER_HTML = R"""
{% extends "base.html" %}
{% block content %}
<div class="row g-4">
    <div class="col-md-12">
        <div class="row g-3">
            {% for acc, bal in balances.items() %}
            <div class="col-md-4">
                <div class="card p-3 shadow-sm border-0 {% if bal < 0 %}bg-danger-subtle text-danger{% else %}bg-white text-success{% endif %}">
                    <small class="text-muted fw-bold">{{ acc }} Remaining</small>
                    <h2 class="fw-bold mb-0">₹{{ bal }}</h2>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="col-md-4">
        <div class="card p-4 shadow-sm border-0">
            <h5 class="fw-bold mb-4">New Transaction</h5>
            <form action="/staff_ledger/add" method="POST">
                <div class="mb-3">
                    <label class="small fw-bold">Direction</label>
                    <select name="type" class="form-select">
                        <option value="Income">Payment Received (IN)</option>
                        <option value="Expense">Expense Paid (OUT)</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="small fw-bold">Account / Mode</label>
                    <select name="account" class="form-select">
                        <option>Arun Account</option>
                        <option>Gulesh Account</option>
                        <option>Cash</option>
                    </select>
                </div>
                <div class="mb-3"><label class="small fw-bold">Amount</label><input type="number" name="amount" class="form-control" required></div>
                <div class="mb-3"><label class="small fw-bold">Purpose</label><input name="purpose" class="form-control" placeholder="Pass, Water, etc." required></div>
                <div class="mb-3"><label class="small fw-bold">Notes</label><textarea name="desc" class="form-control" rows="2"></textarea></div>
                <button class="btn btn-primary w-100 fw-bold">Save Record</button>
            </form>
        </div>
    </div>

    <div class="col-md-8">
        <div class="card p-0 shadow-sm border-0 overflow-hidden">
            <div class="p-3 bg-white border-bottom fw-bold">Staff Transaction Ledger</div>
            <div class="table-responsive" style="max-height: 500px;">
                <table class="table table-hover mb-0">
                    <thead class="table-light small">
                        <tr><th>Date/Time</th><th>Account</th><th>Purpose</th><th>In (₹)</th><th>Out (₹)</th><th>By</th></tr>
                    </thead>
                    <tbody class="small">
                        {% for l in logs %}
                        <tr>
                            <td>{{ l.timestamp.strftime('%d %b, %H:%M') }}</td>
                            <td><span class="badge bg-light text-dark">{{ l.account }}</span></td>
                            <td><b>{{ l.purpose }}</b><br><small class="text-muted">{{ l.description or '' }}</small></td>
                            <td class="text-success fw-bold">{% if l.type == 'Income' %}{{ l.amount }}{% else %}-{% endif %}</td>
                            <td class="text-danger fw-bold">{% if l.type == 'Expense' %}{{ l.amount }}{% else %}-{% endif %}</td>
                            <td>{{ l.created_by }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

TASKS_HTML = r"""
{% extends "base.html" %}
{% block content %}
<div class="row g-4">
    {% if session['role'] == 'owner' %}
    <div class="col-md-3">
        <div class="card p-4 shadow-sm position-sticky" style="top:20px;">
            <h5 class="fw-bold mb-4">Assign New Task</h5>
            <form action="/task/add" method="POST">
                <div class="mb-2"><label class="small fw-bold">Title</label><input name="title" class="form-control" required></div>
                <div class="mb-2">
                    <label class="small fw-bold">Assignee</label>
                    <select name="assignee" class="form-select">{% for m in managers %}<option value="{{m}}">{{m}}</option>{% endfor %}</select>
                </div>
                <div class="mb-2">
                    <label class="small fw-bold">Deadline</label>
                    <input type="date" name="deadline" class="form-control" required>
                </div>
                <div class="mb-2">
                    <label class="small fw-bold">Priority</label>
                    <select name="priority" class="form-select"><option>High</option><option selected>Medium</option><option>Low</option></select>
                </div>
                <div class="mb-3"><label class="small fw-bold">Details</label><textarea name="desc" class="form-control" rows="2"></textarea></div>
                <button class="btn btn-primary w-100 fw-bold">Create Task</button>
            </form>
        </div>
    </div>
    {% endif %}

    <div class="{% if session['role'] == 'owner' %}col-md-9{% else %}col-md-12{% endif %}">
        <h4 class="fw-bold mb-3">Tasks Tracking</h4>
        <div class="row g-3">
            {% for t in tasks %}
            <div class="col-md-6">
                <div class="card p-3 priority-{{t.priority}} h-100 {% if t.status == 'Completed' %}opacity-75 bg-light{% endif %}">
                    <div class="d-flex justify-content-between">
                        <span class="badge {% if t.priority == 'High' %}bg-danger{% elif t.priority == 'Medium' %}bg-warning text-dark{% else %}bg-success{% endif %}">
                            {{t.priority}}
                        </span>
                        {% if t.deadline %}
                            {% if t.status != 'Completed' %}
                                {% if t.days_left < 0 %}
                                    <span class="text-danger fw-bold small">Overdue by {{ t.days_left | abs }} days</span>
                                {% elif t.days_left == 0 %}
                                    <span class="text-warning fw-bold small">Due Today</span>
                                {% else %}
                                    <span class="text-primary fw-bold small">{{ t.days_left }} days remaining</span>
                                {% endif %}
                            {% else %}
                                <span class="text-muted small">Finished</span>
                            {% endif %}
                        {% endif %}
                    </div>
                    
                    <h6 class="fw-bold mt-2 mb-1">{{t.title}}</h6>
                    <p class="small text-muted mb-2">{{t.description}}</p>
                    
                    <div class="comment-box mb-2">{{t.comments if t.comments else "No comments yet..."}}</div>
                    
                    <form action="/task/comment/{{t.id}}" method="POST" class="input-group input-group-sm mb-3">
                        <input name="comment" class="form-control" placeholder="Add note...">
                        <button class="btn btn-outline-primary">Post</button>
                    </form>

                    <div class="d-flex justify-content-between align-items-center mt-auto border-top pt-2">
                        <div class="small text-muted">For: <b>{{t.assigned_to}}</b></div>
                        <div class="d-flex gap-2">
                            {% if t.status == 'Pending' %}
                                <form action="/task/complete/{{t.id}}" method="POST"><button class="btn btn-sm btn-success px-3">Mark Done</button></form>
                            {% endif %}
                            {% if session['role'] == 'owner' %}
                                <form action="/task/delete/{{t.id}}" method="POST"><button class="btn btn-sm btn-outline-danger">✕</button></form>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}
"""

INDEX_HTML = r"""
{% extends "base.html" %}
{% block content %}
<div class="row g-4">
    <div class="col-md-8">
        <div class="row g-3 mb-4">
            {% for p in products %}
            <div class="col-md-3">
                <div class="card p-3 text-center cursor-pointer h-100 position-relative {% if p.stock <= p.low_stock_limit %}low-stock{% endif %}" onclick="addToCart('{{p.name}}', {{p.sell_price}}, '{{p.category}}')">
                    {% if p.stock <= p.low_stock_limit %}<span class="position-absolute top-0 start-50 translate-middle badge rounded-pill bg-danger" style="font-size:0.6rem">LOW</span>{% endif %}
                    <div class="fw-bold small">{{p.name}}</div>
                    <div class="text-primary fw-bold h5">₹{{p.sell_price}}</div>
                    <small class="text-muted">In Stock: {{p.stock}}</small>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="card p-4 mb-4">
            <h6 class="fw-bold text-primary mb-3">📅 New Court Booking</h6>
            <div class="row g-2">
                <div class="col-md-4"><input type="text" id="b_name" class="form-control" placeholder="Player Name*"></div>
                <div class="col-md-4"><input type="text" id="b_mobile" class="form-control" placeholder="Mobile Number"></div>
                <div class="col-md-2"><select id="b_court" class="form-select"><option value="1">C1</option><option value="2">C2</option><option value="3">C3</option><option value="4">C4</option></select></div>
                <div class="col-md-2"><input type="date" id="b_date" class="form-control" onchange="calcPrice()"></div>
                <div class="col-md-4"><select id="b_slot" class="form-select" onchange="calcPrice()">{% for s in slots %}<option>{{s}}</option>{% endfor %}</select></div>
                <div class="col-md-3"><div class="input-group"><span class="input-group-text">₹</span><input type="number" id="b_price" class="form-control fw-bold" value="279"></div></div>
                <div class="col-md-5"><input type="text" id="b_desc" class="form-control" placeholder="Booking Description"></div>
                <button class="btn btn-primary w-100 mt-2 fw-bold py-2" onclick="addBooking()">Add Booking to Cart</button>
            </div>
        </div>

        <div class="card p-0 overflow-hidden">
            <div class="p-3 bg-white border-bottom d-flex justify-content-between align-items-center">
                <h6 class="mb-0 fw-bold">Daily Ledger</h6>
                <div class="text-success fw-bold">Daily Revenue: ₹{{today_total}}</div>
            </div>
            <div class="table-responsive">
                <table class="table table-sm table-hover mb-0">
                    <thead class="table-light small"><tr><th>Time</th><th>Item</th><th>Court</th><th>Price</th><th>Status</th><th>Action</th></tr></thead>
                    <tbody>{% for t in today_txns %}
                    <tr class="{% if t.status == 'Pending' %}status-pending{% endif %}">
                        <td class="small">{{t.timestamp.strftime('%d-%b  %I-%M %p')}}</td>
                        <td><b>{{t.item_name}}</b></td>
                        <td>C{{t.court}}</td>
                        <td>₹{{t.total_sell}}</td>
                        <td>
                            {% if t.status == 'Pending' %}
                            <span class="badge bg-warning text-dark">Pending</span>
                            {% else %}
                            <span class="badge bg-success">Paid</span>
                            {% endif %}
                        </td>
                        <td class="d-flex gap-2">
                            {% if t.status == 'Pending' %}
                            <form action="/complete_txn/{{t.id}}" method="POST" class="no-loader"><button class="btn btn-link text-success p-0 small fw-bold">Mark Paid</button></form>
                            {% endif %}
                            <form action="/undo_txn/{{t.id}}" method="POST" class="no-loader"><button class="btn btn-link text-danger p-0 small">Undo</button></form>
                        </td>
                    </tr>{% endfor %}</tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="col-md-4">
        <div class="card p-4 shadow-lg sticky-top" style="top:20px; border-top: 5px solid #2563eb;">
            <h5 class="fw-bold mb-4">Shopping Cart</h5>
            <div id="cart-list" style="min-height: 250px;"></div>
            <div class="d-flex justify-content-between h3 fw-bold border-top pt-3 mt-3"><span>Total</span><span>₹<span id="cart-total">0</span></span></div>
            
            <div class="row g-2 mt-3">
                <div class="col-6"><button class="btn btn-success w-100 py-3 fw-bold" onclick="checkout('Completed')">Checkout (Paid)</button></div>
                <div class="col-6"><button class="btn btn-warning w-100 py-3 fw-bold" onclick="checkout('Pending')">Mark Pending</button></div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
let cart = [];

function calcPrice(){
    const dateInput = document.getElementById('b_date').value;
    const slot = document.getElementById('b_slot').value;
    const d = dateInput ? new Date(dateInput) : new Date();
    const day = d.getDay(); 
    const isPM = slot.includes("PM");
    const hr = parseInt(slot);
    let price = 279;
    if(day >= 1 && day <= 4 && isPM && hr >= 5 && hr < 12) price = 333;
    if((day == 5 && isPM && hr >= 5 && hr < 12) || day == 0 || day == 6) price = 379;
    document.getElementById('b_price').value = price;
}

// Set default input date to today based on LOCAL machine time (browser)
document.getElementById('b_date').valueAsDate = new Date();
calcPrice();

function addToCart(n, p, c){
    let ex = cart.find(i=>i.name===n);
    if(ex) ex.qty++; else cart.push({name:n, price:p, category:c, qty:1});
    render();
}

function removeFromCart(i){ cart.splice(i, 1); render(); }

function addBooking(){ 
    let n = document.getElementById('b_name').value;
    if(!n) return alert("Player Name is Required");
    cart.push({
        name: `B: ${n}`, 
        price: parseInt(document.getElementById('b_price').value), 
        category: 'Booking', 
        qty: 1, 
        court: document.getElementById('b_court').value, 
        mobile: document.getElementById('b_mobile').value, 
        desc: document.getElementById('b_desc').value
    });
    render();
}

function render(){
    let h='', t=0;
    cart.forEach((it, i)=>{
        t += it.price * it.qty;
        h += `<div class="d-flex justify-content-between align-items-center mb-2 p-2 bg-light rounded shadow-sm">
                <div class="small"><b>${it.name}</b><br>₹${it.price} x ${it.qty}</div>
                <button class="btn btn-sm btn-outline-danger border-0" onclick="removeFromCart(${i})">✕</button>
              </div>`;
    });
    document.getElementById('cart-list').innerHTML = h || '<div class="text-center py-5 text-muted small">Cart is empty</div>';
    document.getElementById('cart-total').innerText = t;
}

function checkout(status){
    if(!cart.length) return;
    showLoader();
    fetch('/submit_order',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({items:cart, status: status})
    }).then(()=>location.reload());
}
</script>
{% endblock %}
"""

DASHBOARD_HTML = r"""
{% extends "base.html" %}
{% block content %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
    /* Styling for the multi-select dropdown */
    .dropdown-check-list { display: inline-block; position: relative; }
    .dropdown-check-list .anchor { 
        position: relative; cursor: pointer; display: inline-block; 
        padding: 5px 25px 5px 10px; border: 1px solid #ccc; 
        border-radius: 4px; background: #fff; min-width: 180px;
    }
    .dropdown-check-list .anchor:after { 
        position: absolute; content: ""; border-left: 2px solid black; 
        border-top: 2px solid black; padding: 3px; right: 10px; 
        top: 35%; transform: rotate(-135deg); 
    }
    .dropdown-check-list ul.items { 
        padding: 5px; display: none; margin: 0; border: 1px solid #ccc; 
        border-top: none; position: absolute; z-index: 1000; 
        background: #fff; width: 100%; list-style: none; 
    }
    .dropdown-check-list ul.items li { padding: 5px; }
    .dropdown-check-list.visible ul.items { display: block; }
</style>

<div class="row mb-4 align-items-center">
    <div class="col-md-4"><h3>Business Analytics</h3></div>
    <div class="col-md-8 text-end">
        <form class="d-flex gap-2 justify-content-end align-items-center" id="filterForm" method="GET" action="/dashboard">
            <span class="small fw-bold text-muted">Filters:</span>
            
            <div id="list1" class="dropdown-check-list" tabindex="100">
                <span class="anchor">Select Categories</span>
                <ul class="items">
                    <li><input type="checkbox" name="cat" value="All" {% if 'All' in cat_filters %}checked{% endif %} /> All </li>
                    <li><input type="checkbox" name="cat" value="Booking" {% if 'Booking' in cat_filters %}checked{% endif %} /> Bookings</li>
                    <li><input type="checkbox" name="cat" value="Sale" {% if 'Sale' in cat_filters %}checked{% endif %} /> Sales</li>
                    <li><input type="checkbox" name="cat" value="Rent" {% if 'Rent' in cat_filters %}checked{% endif %} /> Rents</li>
                    <li><input type="checkbox" name="cat" value="Expense" {% if 'Expense' in cat_filters %}checked{% endif %} /> Expenses</li>
                    <li><input type="checkbox" name="cat" value="External" {% if 'External' in cat_filters %}checked{% endif %} /> External</li>
                </ul>
            </div>

            <input type="date" name="start" value="{{start}}" class="form-control form-control-sm w-auto shadow-sm">
            <input type="date" name="end" value="{{end}}" class="form-control form-control-sm w-auto shadow-sm">
            
            <button type="submit" class="btn btn-sm btn-primary shadow-sm px-3">Apply Filters</button>
        </form>
    </div>
</div>

<div class="row g-3 mb-5 text-center">
    <div class="col-md-4"><div class="card p-3 border-start border-5 border-primary"><h6>Revenue (Paid)</h6><h2 class="text-primary fw-bold">₹{{revenue}}</h2></div></div>
    <div class="col-md-4"><div class="card p-3 border-start border-5 border-danger"><h6>Expenses</h6><h2 class="text-danger fw-bold">₹{{expenses_total}}</h2></div></div>
    <div class="col-md-4"><div class="card p-3 border-start border-5 border-success"><h6>Net Profit</h6><h2 class="text-success fw-bold">₹{{profit}}</h2></div></div>
</div>

<div class="row g-4">
    <div class="col-md-4">
        <div class="card p-4 mb-4"><h6>Category Split</h6><canvas id="revChart"></canvas></div>
		        <div class="card p-4 mb-4">
            <h6 class="fw-bold mb-3 text-danger">Log Business Expense</h6>
            <form action="/add_expense" method="POST">
                <input name="title" class="form-control mb-2" placeholder="Detail (Electricity, Salary)" required>
                <input name="amount" type="number" class="form-control mb-2" placeholder="Amount" required>
                <select name="cat" class="form-select mb-2"><option>Electricity</option><option>Salary</option><option>Misc</option></select>
                <button class="btn btn-danger btn-sm w-100 fw-bold">Add Expense</button>
            </form>
        </div>

        <div class="card p-4">
            <h6 class="fw-bold mb-3 text-success">Log External Partner Income</h6>
            <form action="/add_external" method="POST">
                <select name="source" class="form-select mb-2"><option>Playo</option><option>Khelomore</option><option>Other</option></select>
                <input name="amount" type="number" class="form-control mb-2" placeholder="Amount" required>
                <input name="date" type="date" class="form-control mb-2">
				<input name="desc" type="text" class="form-control mb-2">
                <button class="btn btn-success btn-sm w-100 fw-bold">Add Partner Income</button>
            </form>
        </div>
    </div>
    <div class="col-md-8">
        <div class="card p-0 shadow-sm overflow-hidden">
            <div class="p-3 bg-white border-bottom fw-bold">Unified Transaction Ledger</div>
            <div class="table-responsive" style="max-height: 500px;">
                <table class="table table-hover mb-0">
                    <thead class="table-light small"><tr><th>Date</th><th>Category</th><th>Details</th><th>Status</th><th>Income</th><th>Expense</th></tr></thead>
                    <tbody class="small">
                        {% for t in txns %}<tr><td>{{t.timestamp.strftime('%d %b')}}</td><td>{{t.category}}</td><td>{{t.item_name}}</td><td>{{t.status}}</td><td class="text-success">₹{{t.total_sell}}</td><td>-</td></tr>{% endfor %}
                        {% for p in ext %}<tr><td>{{p.timestamp.strftime('%d %b')}}</td><td>External</td><td>{{p.source}}</td><td>Paid</td><td class="text-success">₹{{p.amount}}</td><td>-</td></tr>{% endfor %}
                        {% for e in exps %}<tr><td>{{e.timestamp.strftime('%d %b')}}</td><td>Expense</td><td>{{e.title}}</td><td>-</td><td>-</td><td class="text-danger">₹{{e.amount}}</td></tr>{% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
    // Toggle dropdown visibility
    var checkList = document.getElementById('list1');
    checkList.getElementsByClassName('anchor')[0].onclick = function(evt) {
        if (checkList.classList.contains('visible'))
            checkList.classList.remove('visible');
        else
            checkList.classList.add('visible');
    }

    // Close dropdown if user clicks outside of it
    document.addEventListener('click', function(event) {
        if (!checkList.contains(event.target)) {
            checkList.classList.remove('visible');
        }
    });

    // Chart logic
    new Chart(document.getElementById('revChart'), { 
        type:'doughnut', 
        data:{ 
            labels: Object.keys({{chart_data|tojson}}), 
            datasets:[{
                data: Object.values({{chart_data|tojson}}), 
                backgroundColor:['#2563eb','#10b981','#f59e0b','#ef4444','#8b5cf6']
            }] 
        },
        options: { plugins: { legend: { position: 'bottom' } } }
    });
</script>
{% endblock %}
"""

INVENTORY_HTML = r"""
{% extends "base.html" %}
{% block content %}
<div class="card p-4 mb-4">
    <h4 class="fw-bold mb-4">Inventory Management</h4>
    <form action="/product/add" method="POST" class="row g-2 p-3 bg-light rounded">
        <div class="col-md-3"><input name="name" class="form-control" placeholder="Item Name" required></div>
        <div class="col-md-2"><select name="cat" class="form-select"><option>Sale</option><option>Rent</option></select></div>
        <div class="col-md-2"><input type="number" name="buy" class="form-control" placeholder="Unit Cost" required></div>
        <div class="col-md-2"><input type="number" name="sell" class="form-control" placeholder="Sell Price" required></div>
        <div class="col-md-2"><input type="number" name="stock" class="form-control" placeholder="Qty" required></div>
        <div class="col-md-1"><button class="btn btn-primary w-100">Add</button></div>
    </form>
</div>
<div class="card p-0 shadow-sm overflow-hidden">
    <table class="table table-hover align-middle mb-0">
        <thead class="table-light"><tr><th>Product</th><th>Type</th><th>Cost</th><th>Price</th><th>Stock Status</th></tr></thead>
        <tbody>
            {% for p in products %}
            <tr>
                <td><b>{{p.name}}</b></td>
                <td><span class="badge {% if p.category=='Sale' %}bg-info{% else %}bg-warning text-dark{% endif %}">{{p.category}}</span></td>
                <td>₹{{p.buy_price}}</td><td>₹{{p.sell_price}}</td>
                <td>
                    {% if p.stock <= p.low_stock_limit %}<span class="text-danger fw-bold">LOW: {{p.stock}}</span>
                    {% else %}<span class="text-success">{{p.stock}}</span>{% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
"""

LOGIN_HTML = r"""
<!DOCTYPE html><html><head><title>Login</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-dark d-flex align-items-center" style="height:100vh">
<form method="POST" class="card p-5 m-auto shadow-lg" style="width:400px; border-radius: 20px;">
    <h2 class="text-center fw-bold text-primary mb-4">Unity Shuttle Arena</h2>
    <div class="mb-3"><label class="small fw-bold">Admin Username</label><input name="user" class="form-control form-control-lg" required></div>
    <div class="mb-3"><label class="small fw-bold">Password</label><input name="pass" type="password" class="form-control form-control-lg" required></div>
    <button class="btn btn-primary btn-lg w-100 fw-bold">LOGIN</button>
</form></body></html>
"""

with open('app.py', 'w', encoding='utf-8') as f: f.write(APP_PY)
with open('templates/base.html', 'w', encoding='utf-8') as f: f.write(BASE_HTML)
with open('templates/login.html', 'w', encoding='utf-8') as f: f.write(LOGIN_HTML)
with open('templates/index.html', 'w', encoding='utf-8') as f: f.write(INDEX_HTML)
with open('templates/dashboard.html', 'w', encoding='utf-8') as f: f.write(DASHBOARD_HTML)
with open('templates/inventory.html', 'w', encoding='utf-8') as f: f.write(INVENTORY_HTML)
with open('templates/tasks.html', 'w', encoding='utf-8') as f: f.write(TASKS_HTML)
with open('templates/passes.html', 'w', encoding='utf-8') as f: f.write(PASSES_HTML)
with open('templates/staff_ledger.html', 'w', encoding='utf-8') as f: f.write(STAFFLENDER_HTML)

print("✅ SUCCESS: Unity ERP v18 with India Timezone (IST) fix applied.")
