import os
import resend
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 设置 Resend API 密钥
resend.api_key = "re_RkYg577m_DtM5LYUZyWXqkcUUPLtGFc7f"

# 初始化 Flask 应用
app = Flask(__name__)
app.secret_key = "your_secret_key"  # 用于闪现消息和会话
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///email_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定义用户账号模型
class UserAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email_accounts = db.relationship('EmailAccount', backref='user', lazy=True)

# 定义邮箱账户模型
class EmailAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='申请中')  # 状态：申请中、已通过、已拒绝
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=False)

# 定义邮件记录模型
class EmailRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_email = db.Column(db.String(120), nullable=False)
    to_email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=False)

# 定义注册请求记录模型
class RegistrationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=False)

# 创建数据库
with app.app_context():
    db.create_all()

# 添加新的配置项，用于存储默认管理员的登录信息
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "luoshang"

# 管理员登录页面
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash("登录失败！请检查用户名和密码。")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

# 后台管理页面
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin_logged_in'):
        flash("请先登录管理员账户！")
        return redirect(url_for('admin_login'))

    search_query = request.args.get('search')
    sort_by = request.args.get('sort', 'email')
    sort_order = request.args.get('order', 'asc')

    accounts_query = EmailAccount.query

    if search_query:
        accounts_query = accounts_query.filter(EmailAccount.email.contains(search_query))

    if sort_by and sort_order:
        if sort_order == 'asc':
            accounts_query = accounts_query.order_by(getattr(EmailAccount, sort_by).asc())
        else:
            accounts_query = accounts_query.order_by(getattr(EmailAccount, sort_by).desc())

    accounts = accounts_query.all()

    if request.method == 'POST':
        action = request.form.get('action')
        selected_ids = request.form.getlist('selected_ids')

        if action == 'delete':
            EmailAccount.query.filter(EmailAccount.id.in_(selected_ids)).delete(synchronize_session=False)
            db.session.commit()
            flash("选中的账户已被删除！")
        elif action == 'approve':
            accounts_to_approve = EmailAccount.query.filter(EmailAccount.id.in_(selected_ids)).all()
            for account in accounts_to_approve:
                if account.status == '申请中':
                    account.status = '已通过'
            db.session.commit()
            flash("选中的账户已被批准！")
        elif action == 'reject':
            EmailAccount.query.filter(EmailAccount.id.in_(selected_ids)).delete(synchronize_session=False)
            db.session.commit()
            flash("选中的账户已被拒绝并删除！")

        return redirect(url_for('admin'))

    return render_template('admin.html', accounts=accounts, search_query=search_query, sort_by=sort_by, sort_order=sort_order)

# 批准单个邮箱账户
@app.route('/approve/<int:id>', methods=['POST'])
def approve(id):
    account = EmailAccount.query.get(id)
    if account:
        if account.status == '申请中':
            account.status = '已通过'
            db.session.commit()
            print(f"Approved: {account.email}, Status: {account.status}")  # Debug 信息
            flash(f"邮箱 {account.email} 已批准！")
        else:
            flash(f"邮箱 {account.email} 当前状态为 {account.status}，无法批准！")
    else:
        flash("未找到指定的邮箱账户！")
    return redirect(url_for('admin'))

@app.route('/reject/<int:id>', methods=['POST'])
def reject(id):
    account = EmailAccount.query.get(id)
    if account:
        db.session.delete(account)
        db.session.commit()  # 确保数据库变更被提交
        flash(f"邮箱 {account.email} 已拒绝并删除！")
    else:
        flash("未找到指定的邮箱账户！")
    return redirect(url_for('admin'))

# 登出管理员
@app.route('/admin_logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("已成功登出管理员账户！")
    return redirect(url_for('admin_login'))

# 注册用户页面
@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 检查用户名是否已存在
        if UserAccount.query.filter_by(username=username).first():
            flash("用户名已存在！")
            return redirect(url_for('register_user'))

        new_user = UserAccount(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("用户注册成功！请登录。")
        return redirect(url_for('index'))

    return render_template('register_user.html')

# 用户登录页面
@app.route('/user_login', methods=['POST'])
def user_login():
    username = request.form['username']
    password = request.form['password']
    user = UserAccount.query.filter_by(username=username, password=password).first()
    if user:
        session['logged_in'] = True
        session['user_id'] = user.id
        flash("登录成功！")
    else:
        flash("登录失败！请检查用户名和密码。")
    return redirect(url_for('index'))

# 用户登出
@app.route('/user_logout', methods=['POST'])
def user_logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    flash("已成功登出！")
    return redirect(url_for('index'))

# 注册邮箱页面
@app.route('/register_email', methods=['GET', 'POST'])
def register_email():
    if not session.get('logged_in'):
        flash("请先登录用户账号！")
        return redirect(url_for('index'))

    if request.method == 'POST':
        email_prefix = request.form.get('email_prefix')
        password = request.form.get('password')
        email = f"{email_prefix}@wangxitan.work"

        # 检查邮箱账户是否已存在
        if EmailAccount.query.filter_by(email=email).first():
            flash("邮箱账户已存在！")
            return redirect(url_for('register_email'))

        new_account = EmailAccount(email=email, password=password, user_id=session['user_id'])
        db.session.add(new_account)
        db.session.commit()

        flash("邮箱注册成功，请等待管理员审核。")
        return redirect(url_for('index'))

    return render_template('register_email.html')

# 发送邮件页面
@app.route('/send_email', methods=['GET', 'POST'])
def send_email():
    if not session.get('logged_in'):
        flash("请先登录用户账号！")
        return redirect(url_for('index'))

    user_id = session['user_id']

    if request.method == 'GET':
        accounts = EmailAccount.query.filter_by(user_id=user_id, status='已通过').all()
        return render_template('send_email.html', accounts=accounts)

    if request.method == 'POST':
        to_email = request.form.get('to_email')
        subject = request.form.get('subject')
        html_content = request.form.get('html_content')
        from_email = request.form.get('from_email')

        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        # 处理附件
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            for file in files:
                # 这里可以添加文件处理逻辑，例如保存文件或附加文件到邮件
                pass

        email = resend.Emails.send(params)

        # 保存邮件记录到数据库
        new_record = EmailRecord(from_email=from_email, to_email=to_email, subject=subject, html_content=html_content, user_id=user_id)
        db.session.add(new_record)
        db.session.commit()

        flash("邮件发送成功！")
        return redirect(url_for('index'))

# 查看邮件记录
@app.route('/records')
def view_records():
    if not session.get('logged_in'):
        flash("请先登录用户账号！")
        return redirect(url_for('index'))

    user_id = session['user_id']
    records = EmailRecord.query.filter_by(user_id=user_id).all()
    return render_template('records.html', records=records)

# 删除邮件记录
@app.route('/delete_record/<int:id>', methods=['POST'])
def delete_record(id):
    if not session.get('logged_in'):
        flash("请先登录用户账号！")
        return redirect(url_for('index'))

    record = EmailRecord.query.get(id)
    if record and record.user_id == session['user_id']:
        db.session.delete(record)
        db.session.commit()
    return redirect(url_for('view_records'))

# 主页
@app.route('/')
def index():
    if session.get('logged_in') and 'user_id' in session:
        user_id = session['user_id']
        accounts = EmailAccount.query.filter_by(user_id=user_id).all()
        return render_template('index.html', accounts=accounts, logged_in=True)
    return render_template('index.html', accounts=[], logged_in=False)

if __name__ == '__main__':
    app.run(debug=True)
