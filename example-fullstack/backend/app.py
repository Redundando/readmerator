"""Simple Flask API example."""
from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/api/data')
def get_data():
    # Example using requests library
    response = requests.get('https://api.example.com/data')
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True)
