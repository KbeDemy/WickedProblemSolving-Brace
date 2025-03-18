from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

potentiometer_value = 0  # Opslag voor de ESP32-waarde

@app.route('/')
def home():
    return render_template('index.html')  # Laad de webpagina

@app.route('/update', methods=['POST'])
def update_value():
    global potentiometer_value
    potentiometer_value = request.json.get('value', 0)
    return jsonify({"message": "Waarde bijgewerkt", "value": potentiometer_value})

@app.route('/get_value')
def get_value():
    return jsonify({"value": potentiometer_value})  # Stuur de waarde naar JavaScript

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
