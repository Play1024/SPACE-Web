from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE = 'whitelist.db'

# 数据库
def create_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT,
                 password TEXT,
                 is_admin INTEGER DEFAULT 0
                 )''')
    conn.commit()
    conn.close()

# 白名单路径
import  json
WHITELIST_PATH = 'G:\server\whitelist.json'

# 添加到白名单
def add_to_whitelist(username):
    with open(WHITELIST_PATH, 'r+') as f:
        whitelist = json.load(f)
        whitelist.append(username)
        f.seek(0)
        json.dump(whitelist, f)




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
        # 在插入用户信息时，设置默认的管理员属性为 0（非管理员）
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, password, 0))
        conn.commit()
        conn.close()

        add_to_whitelist(username)

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

    return render_template('dashboard.html', username=session['username'])
    
    
# 登出
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


# 管理员
# Admin 路由
@app.route('/admin')
def admin():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Check if current user is admin
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ?", (session['username'],))
    is_admin = c.fetchone()[0]
    conn.close()

    if not is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    # Fetch user list
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users")  # 修改查询语句以包含密码
    users = c.fetchall()
    print(users)  # 打印用户列表
    conn.close()

    return render_template('admin.html', users=users)


# 删除功能
# 删除用户路由
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


if __name__ == '__main__':
    create_table()
    app.run(debug=True)


