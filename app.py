from flask import Flask, jsonify

import webbrowser
import threading
import main

app = Flask(__name__)

@app.route("/")

def home():
    return "test"

@app.route("/weather/<city>/<country_code>")
def get_weather(city, country_code):
    weather_data = main.fetch_weather_data(city, country_code)
    return jsonify(weather_data)

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    # Start the Flask app in a separate thread
    threading.Timer(1, open_browser).start()
    app.run()