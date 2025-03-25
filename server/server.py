from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from datetime import datetime, timedelta
import json
import os
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Database initialization
def init_db():
    conn = sqlite3.connect('brace_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_values
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  value REAL NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Initialize database when running as main module
if __name__ == '__main__':
    init_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            if request.method == 'POST' and request.path == '/update':
                return jsonify({'error': 'Unauthorized'}), 401
            if request.path.startswith('/get_'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Ongeldige inloggegevens')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/update', methods=['POST'])
def update_value():
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
        
    try:
        data = request.get_json()
        new_value = float(data.get('value'))
        
        # Gebruik alleen de huidige tijd, geen externe timestamp
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect('brace_data.db')
        c = conn.cursor()
        c.execute('INSERT INTO sensor_values (value, timestamp) VALUES (?, ?)',
                 (new_value, timestamp))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'value': new_value,
            'timestamp': timestamp
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/get_current_value')
@login_required
def get_current_value():
    conn = sqlite3.connect('brace_data.db')
    c = conn.cursor()
    c.execute('SELECT value FROM sensor_values ORDER BY timestamp DESC LIMIT 1')
    result = c.fetchone()
    conn.close()
    
    if result:
        return jsonify({'value': result[0]})
    return jsonify({'value': 0})

@app.route('/get_values')
@login_required
def get_values():
    conn = sqlite3.connect('brace_data.db')
    c = conn.cursor()
    c.execute('SELECT value, timestamp FROM sensor_values ORDER BY timestamp DESC LIMIT 500')
    values = [{'value': row[0], 'timestamp': row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(values)

@app.route('/get_week_overview')
@login_required
def get_week_overview():
    conn = sqlite3.connect('brace_data.db')
    c = conn.cursor()
    
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    
    week_data = []
    for i in range(7):
        day_start = start_of_week + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        # Get all values for the day in chronological order
        c.execute('''
            SELECT value, timestamp 
            FROM sensor_values 
            WHERE timestamp >= ? AND timestamp < ?
            ORDER BY timestamp ASC
        ''', (day_start.isoformat(), day_end.isoformat()))
        
        values = c.fetchall()
        total_movement = 0
        
        # Calculate total movement by looking at changes between consecutive values
        for j in range(1, len(values)):
            current_value = values[j][0]
            previous_value = values[j-1][0]
            # Calculate absolute difference between consecutive readings
            movement = abs(current_value - previous_value)
            total_movement += movement
        
        week_data.append({
            'value': total_movement,
            'count': len(values)
        })
    
    conn.close()
    return jsonify(week_data)

@app.route('/get_day_values/<int:day_index>')
@login_required
def get_day_values(day_index):
    if not 0 <= day_index <= 6:
        return jsonify({'error': 'Invalid day index'}), 400
        
    conn = sqlite3.connect('brace_data.db')
    c = conn.cursor()
    
    # Get the start of the current week (Monday)
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    day_start = start_of_week + timedelta(days=day_index)
    day_end = day_start + timedelta(days=1)
    
    c.execute('''
        SELECT value, timestamp
        FROM sensor_values
        WHERE timestamp >= ? AND timestamp < ?
        ORDER BY timestamp ASC
    ''', (day_start.isoformat(), day_end.isoformat()))
    
    values = [{'value': row[0], 'timestamp': row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(values)

@app.route('/exercises')
@login_required
def exercises():
    return render_template('exercises.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
