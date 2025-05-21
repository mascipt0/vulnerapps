from flask import Flask, request, redirect, render_template, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "insecure_secret"

# Inisialisasi database
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    """)
    try:
        # Tambahkan admin default dengan password plaintext
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("admin", "P@ssw0rd", "admin"))
    except sqlite3.IntegrityError:
        pass  # Jika sudah ada
    conn.commit()
    conn.close()

# Home
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

# Login (Injection & Broken Access)
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 🔥 VULNERABLE TO SQL INJECTION
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        print("Executing query:", query)
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = user[1]
            session['role'] = user[3]
            return redirect(url_for('profile'))
        else:
            error = "Invalid credentials"

    return render_template('login.html', error=error)

# Register (Cryptographic Failures)
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 🔥 PASSWORD DISIMPAN DALAM BENTUK PLAINTEXT
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            error = "Username already exists"
        finally:
            conn.close()
    return render_template('register.html', error=error)

# Profile (Broken Access Control)
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    role = session.get('role', 'user')

    return render_template('profile.html', username=username, role=role)

# Admin Page (No access control)
@app.route('/admin')
def admin():
    if 'username' not in session:
        return redirect(url_for('login'))

    # 🔥 NO ROLE CHECK — Broken Access Control
    return render_template('admin.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
