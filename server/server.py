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


@app.route('/get_moment_values')
@login_required
def get_moment_values():
    print("Fetching moment values (latest 500)...")
    conn = sqlite3.connect('brace_data.db')
    c = conn.cursor()
    c.execute('SELECT angle, timestamp FROM sensor_values ORDER BY timestamp DESC LIMIT 500')
    values = [{'angle': row[0], 'timestamp': row[1]} for row in reversed(c.fetchall())]
    conn.close()
    return jsonify(values)


@app.route('/get_day_overview')
@login_required
def get_day_overview():
    print("Fetching day overview (delta per minuut)...")
    conn = sqlite3.connect('brace_data.db')
    c = conn.cursor()

    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    c.execute('''SELECT angle, timestamp FROM sensor_values
                 WHERE timestamp >= ? AND timestamp < ?
                 ORDER BY timestamp ASC''', (start.isoformat(), end.isoformat()))
    data = c.fetchall()

    minute_data = []
    last_minute = None
    deltas = []
    for i in range(1, len(data)):
        ts = datetime.fromisoformat(data[i][1])
        minute = ts.replace(second=0, microsecond=0)
        delta = abs(data[i][0] - data[i - 1][0])

        if last_minute is None or minute != last_minute:
            deltas.append(delta)
            last_minute = minute
        else:
            deltas[-1] += delta

    conn.close()
    print(f"Day overview: {len(deltas)} punten.")
    return jsonify(deltas)



@app.route('/get_total_history')
@login_required
def get_total_history():
    print("Fetching total history (delta per dag)...")
    conn = sqlite3.connect('brace_data.db')
    c = conn.cursor()

    c.execute('''SELECT angle, timestamp FROM sensor_values ORDER BY timestamp ASC''')
    all_values = c.fetchall()
    conn.close()

    history = {}
    for i in range(1, len(all_values)):
        angle_prev, ts_prev = all_values[i-1]
        angle_curr, ts_curr = all_values[i]

        day = datetime.fromisoformat(ts_curr).strftime('%Y-%m-%d')
        delta = abs(angle_curr - angle_prev)
        history[day] = history.get(day, 0) + delta

    result = [{'dag': day, 'delta': history[day]} for day in sorted(history)]
    print(f"Totaal historiek: {len(result)} dagen.")
    return jsonify(result)

@app.route('/exercises')
@login_required
def exercises():
    print("Exercises route accessed.")
    return render_template('exercises.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
