
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
