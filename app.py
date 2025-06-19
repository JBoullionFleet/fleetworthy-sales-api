# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS # Import CORS for handling cross-origin requests

app = Flask(__name__)
# Enable CORS for all origins. In a production environment, you would restrict this
# to specific domains. For now, this allows your frontend to connect.
CORS(app)

@app.route('/')
def home():
    """
    A simple home route to confirm the server is running.
    """
    return "Fleetworthy Sales Agent API is running!"

@app.route('/hello', methods=['POST'])
def hello_world():
    """
    API endpoint that accepts a POST request with a JSON body.
    It expects a 'name' field in the JSON and returns a personalized greeting.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    name = data.get('name')

    if name:
        response_message = f"Hello, {name}! Welcome to the Fleetworthy Sales Portal."
        return jsonify({"message": response_message}), 200
    else:
        return jsonify({"error": "Name field is required"}), 400

if __name__ == '__main__':
    # This runs the Flask app in debug mode.
    # For deployment, a production-ready WSGI server like Gunicorn is used.
    app.run(debug=True, host='0.0.0.0', port=5000)

