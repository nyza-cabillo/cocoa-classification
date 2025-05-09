from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from your frontend

@app.route('/predict', methods=['POST'])  # <--- This is key
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image_file = request.files['image']
    # Add your prediction logic here

    return jsonify({'prediction': 'Healthy', 'confidence': 95.2})
