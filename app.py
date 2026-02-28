from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import math

app = Flask(__name__)
app.secret_key = "employee_secret_key"

# Pagination settings
EMPLOYEES_PER_PAGE = 5

# ---------- DATABASE CONNECTION ----------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- CREATE DATABASE & TABLE ----------
def init_db():
    conn = sqlite3.connect("database.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employee (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            department TEXT,
            salary TEXT
        )
    """)
    conn.close()

init_db()

# ---------- LOGIN PAGE ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simple Admin Login
        if username == "admin" and password == "admin":
            session['admin'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid Credentials")

    return render_template('login.html')

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

# ---------- READ (Dashboard) ----------
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))

    # Get current page from query parameter (default to page 1)
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    conn = get_db()
    
    # Get total count of employees
    total_employees = conn.execute("SELECT COUNT(*) as count FROM employee").fetchone()['count']
    total_pages = math.ceil(total_employees / EMPLOYEES_PER_PAGE) if total_employees > 0 else 1
    
    # Ensure page is not beyond total pages
    if page > total_pages:
        page = total_pages
    
    # Calculate offset for SQL query
    offset = (page - 1) * EMPLOYEES_PER_PAGE
    
    # Get employees for current page
    employees = conn.execute(
        "SELECT * FROM employee LIMIT ? OFFSET ?",
        (EMPLOYEES_PER_PAGE, offset)
    ).fetchall()
    conn.close()

    return render_template(
        'dashboard.html',
        employees=employees,
        current_page=page,
        total_pages=total_pages,
        total_employees=total_employees
    )

# ---------- CREATE (Add Employee) ----------
@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if 'admin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        salary = request.form['salary']

        conn = get_db()
        conn.execute(
            "INSERT INTO employee (name, email, department, salary) VALUES (?, ?, ?, ?)",
            (name, email, department, salary)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template('add.html')

# ---------- UPDATE (Edit Employee) ----------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        salary = request.form['salary']

        conn.execute(
            "UPDATE employee SET name=?, email=?, department=?, salary=? WHERE id=?",
            (name, email, department, salary, id)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    employee = conn.execute("SELECT * FROM employee WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template('edit.html', employee=employee)

# ---------- DELETE ----------
@app.route('/delete/<int:id>')
def delete_employee(id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    conn.execute("DELETE FROM employee WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

# ---------- CAROUSEL (All Pages on Single Slide) ----------
@app.route('/carousel')
def carousel():
    return render_template('carousel.html')

# ---------- RUN SERVER ----------
if __name__ == "__main__":
    app.run(debug=True)