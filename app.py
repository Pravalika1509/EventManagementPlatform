from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
# Testing pull request flow

app = Flask(__name__)
app.secret_key = 'secret_key'

# -----------------------------
# Database connection function
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------
# Create tables if not exist
# -----------------------------
def init_db():
    conn = get_db_connection()

    conn.execute('''CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        date TEXT NOT NULL,
                        venue TEXT NOT NULL
                    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL
                    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS registrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id INTEGER NOT NULL,
                        username TEXT NOT NULL,
                        FOREIGN KEY (event_id) REFERENCES events (id)
                    )''')

    # Preload admin user if not exists
    conn.execute('''INSERT OR IGNORE INTO users (username, password, role)
                    VALUES (?, ?, ?)''', ('admin', 'admin123', 'admin'))

    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

# -----------------------------
# Routes
# -----------------------------

@app.route('/')
def index():
    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events').fetchall()
    conn.close()
    return render_template('index.html', events=events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['user'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid Credentials'
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events').fetchall()
    conn.close()
    return render_template('dashboard.html', events=events)

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        venue = request.form['venue']
        conn = get_db_connection()
        conn.execute('INSERT INTO events (name, date, venue) VALUES (?, ?, ?)', (name, date, venue))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('create_event.html')

@app.route('/register_event/<int:event_id>')
def register_event(event_id):
    if 'user' not in session or session['role'] != 'attendee':
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('INSERT INTO registrations (event_id, username) VALUES (?, ?)', (event_id, session['user']))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# -----------------------------
# Run the Flask app
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
