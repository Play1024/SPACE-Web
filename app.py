from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import json
from datetime import datetime


app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE = 'whitelist.db'

# 数据库
def create_table():
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                balance REAL DEFAULT 0.0,
                last_sign_in DATETIME  -- 添加了 last_sign_in 字段
            )
        ''')
        conn.commit()
        conn.close()


def add_balance_column():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0")
    conn.commit()
    conn.close()
    

# 设置静态文件目录为 "static" 文件夹
app.static_folder = 'static'


# 主页
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')
    
    
    
# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()


        # 检查用户名是否已经存在
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        if result:
            conn.close()
            flash('Username already exists. Please choose another one.', 'error')
            return redirect(url_for('register'))



        # 在插入用户信息时，设置默认的管理员属性为 0（非管理员）
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, password, 0))
        conn.commit()
        conn.close()


        flash('Registered successfully!', 'success')
        return redirect(url_for('register_success'))

    return render_template('register.html')



    
# 注册成功
@app.route('/register_success')
def register_success():
    return render_template('register_success.html')    
    
    
    
# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['username'] = username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')
    
    
    
    
# 用户主页
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
        
        # 获取当前用户的余额
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE username = ?", (session['username'],))
    balance = c.fetchone()[0]
    conn.close()

    return render_template('dashboard.html', username=session['username'], balance=balance)


  
    
    
# 用户签到
@app.route('/sign_in', methods=['POST'])
def sign_in():
    if 'username' not in session:
        flash('You must be logged in to sign in.', 'danger')
        return redirect(url_for('login'))

    username = session['username']
    today = datetime.now().date()  # 获取当前日期

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT last_sign_in FROM users WHERE username = ?", (username,))
    last_sign_in = c.fetchone()

    # 检查 last_sign_in 是否为 None 或空字符串
    if last_sign_in and last_sign_in[0] is not None and last_sign_in[0] != '':
        # 尝试解析日期
        last_sign_in_date = datetime.strptime(last_sign_in[0], '%Y-%m-%d').date()
    else:
        last_sign_in_date = None  # last_sign_in 为 None 或空字符串，表示没有签到记录

    # 检查用户今天是否已经签到
    if last_sign_in_date and last_sign_in_date == today:
        conn.close()
        flash('You have already signed in today.', 'info')
        return redirect(url_for('dashboard'))

    # 更新用户的签到时间和余额
    c.execute("UPDATE users SET last_sign_in = ?, balance = balance + 5 WHERE username = ?",
              (today.isoformat(), username))
    conn.commit()
    conn.close()

    flash('Sign in successful! You received a reward.', 'success')
    return redirect(url_for('dashboard'))



    

    
# 登出
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))




# 管理员面板
@app.route('/admin')
def admin():
    if 'username' not in session:
        return redirect(url_for('login'))

     # 检查当前用户是否为管理员
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ?", (session['username'],))
    is_admin = c.fetchone()[0]
    conn.close()

    if not is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, username, password, balance FROM users")  
    users = c.fetchall()
    

    print(users)  # 打印用户列表
    conn.close()

    return render_template('admin.html', users=users)


   






# 删除用户功能
@app.route('/admin/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    # 检查当前用户是否为管理员
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ?", (session['username'],))
    is_admin = c.fetchone()[0]
    conn.close()

    if not is_admin:
        flash('您没有权限访问该页面。', 'danger')
        return redirect(url_for('index'))

    # 从数据库中删除用户
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash('用户删除成功！', 'success')
    return redirect(url_for('admin'))



# 发送货币
@app.route('/admin/send_money', methods=['POST'])
def admin_send_money():
    # 检查当前用户是否为管理员
    if 'username' not in session:
        flash('You must be logged in to perform this action.', 'danger')
        return redirect(url_for('login'))

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ?", (session['username'],))
    is_admin = c.fetchone()[0]
    conn.close()

    if not is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    # 确保表单数据存在
    if request.method == 'POST':
        user = request.form.get('user')
        amount = request.form.get('amount')

        if user and amount:  # 检查用户和金额是否被提供
            try:
                amount = float(amount)  # 尝试将金额转换为浮点数
                conn = sqlite3.connect(DATABASE)
                c = conn.cursor()
                # 确保使用正确的 WHERE 条件，如果 'user' 是用户名
                c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, user))
                conn.commit()
                conn.close()
                flash('Money sent successfully!', 'success')
            except ValueError:  # 如果转换失败，捕捉 ValueError 异常
                flash('Invalid amount. Please enter a numeric value.', 'danger')
            except Exception as e:  # 捕捉其他可能的异常
                flash(f'An error occurred: {e}', 'danger')
        else:
            flash('Please provide both user and amount.', 'danger')

        return redirect(url_for('admin'))  # 重定向到管理员页面





# 转账

@app.route('/transfer', methods=['POST'])
def transfer():
    if 'username' not in session:
        return redirect(url_for('login'))

    sender = session['username']
    receiver = request.form['receiver']
    amount = float(request.form['amount'])

    # 检查发送者和接收者是否相同
    if sender == receiver:
        flash('Cannot transfer to yourself.', 'danger')
        return redirect(url_for('dashboard'))

    # 检查余额是否足够
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE username = ?", (sender,))
    balance = c.fetchone()[0]
    conn.close()

    if balance < amount:
        flash('Insufficient balance.', 'danger')
        return redirect(url_for('dashboard'))

    # 执行转账
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (amount, sender))
    c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, receiver))
    conn.commit()
    conn.close()

    flash('Transfer successful!', 'success')
    return redirect(url_for('dashboard'))






if __name__ == '__main__':
    create_table()
    app.run(debug=False)


