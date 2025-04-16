from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from datetime import datetime, timedelta
import json
import os
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Database initialization
def init_db():
    try:
        conn = sqlite3.connect('brace_data.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sensor_values
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      angle REAL NOT NULL,
                      temperature REAL NOT NULL,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
        print("Database initialized or already exists.")
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == '__main__':
    init_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            print("Unauthorized access attempt.")
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
    print("Index route accessed.")
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Login attempt: {username}")
        
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            print("Login successful.")
            return redirect(url_for('index'))
        else:
            print("Login failed. Invalid credentials.")
            return render_template('login.html', error='Ongeldige inloggegevens')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    print("Logged out successfully.")
    return redirect(url_for('login'))

@app.route('/update', methods=['POST'])
def update_value():
    if not request.is_json:
        print("Error: Content-Type is not application/json")
        return jsonify({'error': 'Content-Type must be application/json'}), 400
        
    try:
        data = request.get_json()
        print("Received JSON:", data)  # Debug print to check incoming data
        
        angle_raw = data.get('angle')
        temperature_raw = data.get('temperature')

        if angle_raw is None or temperature_raw is None:
            print("Error: Missing angle or temperature")
            return jsonify({'error': 'Missing angle or temperature'}), 400
        
        try:
            angle = float(angle_raw)
            temperature = float(temperature_raw)
            print(f"Parsed values - Angle: {angle}, Temperature: {temperature}")
        except ValueError:
            print("Error: Invalid data type for angle or temperature")
            return jsonify({'error': 'Invalid data type for angle or temperature'}), 400
        
        # Insert into database
        timestamp = datetime.now().isoformat()
        conn = sqlite3.connect('brace_data.db')
        c = conn.cursor()
        c.execute('INSERT INTO sensor_values (angle, temperature, timestamp) VALUES (?, ?, ?)',
                 (angle, temperature, timestamp))
        conn.commit()
        conn.close()
        print(f"Data inserted into database: {angle}, {temperature}, {timestamp}")
        
        return jsonify({
            'success': True,
            'angle': angle,
            'temperature': temperature,
            'timestamp': timestamp
        })
    except Exception as e:
        print(f"Error in /update route: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/get_current_value')
@login_required
def get_current_value():
    print("Fetching current value...")
    conn = sqlite3.connect('brace_data.db')
    c = conn.cursor()
    c.execute('SELECT angle, temperature FROM sensor_values ORDER BY timestamp DESC LIMIT 1')
    result = c.fetchone()
    conn.close()
    
    if result:
        print(f"Current value fetched: Angle: {result[0]}, Temperature: {result[1]}")
        return jsonify({'angle': result[0], 'temperature': result[1]})
    
    print("No current value found.")
    return jsonify({'angle': 0, 'temperature': 0})

@app.route('/get_values')
@login_required
def get_values():
    print("Fetching recent values...")
    conn = sqlite3.connect('brace_data.db')
    c = conn.cursor()
    c.execute('SELECT angle, timestamp FROM sensor_values ORDER BY timestamp ASC')

    rows = c.fetchall()
    conn.close()

    values = [{'angle': row[0], 'timestamp': row[1]} for row in rows]
    print(f"Fetched {len(values)} values.")

    
    return jsonify(values)

@app.route('/get_week_overview')
@login_required
def get_week_overview():
    print("Fetching week overview...")
    conn = sqlite3.connect('brace_data.db')
    c = conn.cursor()
    
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    
    week_data = []
    for i in range(7):
        day_start = start_of_week + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        c.execute('''SELECT angle, timestamp FROM sensor_values WHERE timestamp >= ? AND timestamp < ? ORDER BY timestamp ASC''',
                  (day_start.isoformat(), day_end.isoformat()))
        
        values = c.fetchall()
        total_movement = 0
        
        for j in range(1, len(values)):
            current_value = values[j][0]
            previous_value = values[j-1][0]
            movement = abs(current_value - previous_value)
            total_movement += movement
        
        week_data.append({
            'value': total_movement,
            'count': len(values)
        })
    
    conn.close()
    print(f"Week overview data: {week_data}")
    return jsonify(week_data)

@app.route('/get_day_values/<int:day_index>')
@login_required
def get_day_values(day_index):
    print(f"Fetching data for day {day_index}...")
    
    if not 0 <= day_index <= 6:
        return jsonify({'error': 'Invalid day index'}), 400
        
    conn = sqlite3.connect('brace_data.db')
    c = conn.cursor()
    
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    day_start = start_of_week + timedelta(days=day_index)
    day_end = day_start + timedelta(days=1)
    
    c.execute('''SELECT angle, timestamp FROM sensor_values WHERE timestamp >= ? AND timestamp < ? ORDER BY timestamp ASC''',
              (day_start.isoformat(), day_end.isoformat()))
    
    values = [{'angle': row[0], 'timestamp': row[1]} for row in c.fetchall()]
    conn.close()
    
    print(f"Fetched {len(values)} values for day {day_index}.")
    return jsonify(values)

@app.route('/exercises')
@login_required
def exercises():
    print("Exercises route accessed.")
    return render_template('exercises.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
