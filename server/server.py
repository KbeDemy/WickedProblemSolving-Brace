from flask import Flask, request, jsonify, render_template import json import os from datetime
import datetime # Import voor timestamp

app = Flask(__name__) json_file = "sensor_data.json" MAX_DATA_POINTS = 1000 # Optioneel:
Beperk het aantal opgeslagen waarden

# Functie om JSON-bestand in te laden
def load_sensor_data():
    if os.path.exists(json_file):
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data  # Geldige lijst
        except json.JSONDecodeError:
            pass  # Bestand is corrupt of leeg
    return []  # Retourneer een lege lijst als er iets misgaat

# Functie om JSON-bestand op te slaan
def save_sensor_data(data):
    try:
        with open(json_file, "w") as f:
            json.dump(data, f, indent=4)
    except IOError:
        print("Fout bij opslaan van sensorwaarden!")

sensor_data = load_sensor_data()  # Laad bestaande data bij opstarten

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/update', methods=['POST'])
def update_value():
    global sensor_data
    new_value = request.json.get('value', 0)

    # Genereer timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Voeg nieuwe waarde toe
    sensor_data.append({"value": new_value, "timestamp": timestamp})

    # Beperk de grootte van de lijst
    if len(sensor_data) > MAX_DATA_POINTS:
        sensor_data.pop(0)  # Verwijder oudste waarde

    # Sla op in JSON-bestand
    save_sensor_data(sensor_data)

    return jsonify({"message": "Waarde bijgewerkt", "values": sensor_data})

@app.route('/get_values')
def get_values():
    return jsonify(sensor_data)  # Stuur volledige lijst naar client

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
