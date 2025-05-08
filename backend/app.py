import io
import os
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS  # Added for CORS support
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet import preprocess_input as resnet_preprocess
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D, Dropout, Dense
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Client Initialization
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})
  #  Enable CORS for Vue frontend (Vite default)

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "checkpointBAGGINGagg", "ResNet50_best.h5")
CLASS_NAMES = ['Black Pod Rot', 'Healthy', 'Pod Borer']
INPUT_SHAPE = (224, 224, 3)

# Load model
def load_model():
    base_model = ResNet50(include_top=False, weights='imagenet', input_shape=INPUT_SHAPE)
    x = GlobalAveragePooling2D()(base_model.output)
    x = Dropout(0.6)(x)
    predictions = Dense(len(CLASS_NAMES), activation='softmax')(x)
    model = Model(inputs=base_model.input, outputs=predictions)
    model.load_weights(MODEL_PATH)
    return model

model = load_model()

# Image preprocessing
def prepare_image(image):
    image = image.resize(INPUT_SHAPE[:2])
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    return resnet_preprocess(image)

# Save prediction to Supabase
from datetime import datetime

def save_prediction(image_url, predicted_class, confidence):
    try:
        response = supabase.table('predictions').insert({
            'image_id': image_url,
            'predicted_class': predicted_class,
            'confidence': float(confidence),
            'created_at': datetime.utcnow().isoformat()
        }).execute()

        print("Supabase prediction insert response:", response)

        if response.error:
            print(f"Error saving prediction: {response.error.message}")
            return None

        if not response.data or 'id' not in response.data[0]:
            print("Prediction ID not returned from Supabase.")
            return None

        return response.data[0]['id']

    except Exception as e:
        print(f"Prediction error: {str(e)}")
        return None



# Save feedback to Supabase
def save_feedback(user_id, prediction_id, feedback_text):
    try:
        response = supabase.table('feedbacks').insert({
            'user_id': user_id,
            'prediction_id': prediction_id,
            'feedback_text': feedback_text,
        }).execute()
        if response.error:
            print(f"Error saving feedback: {response.error.message}")
        return response.data
    except Exception as e:
        print(f"Error in saving feedback: {str(e)}")
        return None

# Predict endpoint
@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files or 'user_id' not in request.form or 'image_url' not in request.form:
        return jsonify({'error': 'Missing image, user_id, or image_url'}), 400

    file = request.files['image']
    image_url = request.form['image_url']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        image = load_img(io.BytesIO(file.read()))
        processed_img = prepare_image(image)
        preds = model.predict(processed_img)
        pred_idx = np.argmax(preds)
        confidence = float(f"{preds[0][pred_idx] * 100:.2f}")
        predicted_class = CLASS_NAMES[pred_idx]

        # Save prediction ONCE and log result
        prediction_id = save_prediction(image_url, predicted_class, confidence)

        if prediction_id is None:
            print("Failed to insert prediction into Supabase.")
            return jsonify({'error': 'Failed to save prediction to database'}), 500

        print(f"Saved prediction with ID: {prediction_id}")

        return jsonify({
            'prediction': predicted_class,
            'confidence': confidence,
            'prediction_id': prediction_id
        })

    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'error': 'Prediction failed', 'details': str(e)}), 500

  
# Feedback endpoint
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    user_id = data.get('user_id')
    prediction_id = data.get('prediction_id')
    feedback_text = data.get('feedback_text')

    if not user_id or not prediction_id or not feedback_text:
        return jsonify({'error': 'Missing data for feedback submission'}), 400

    try:
        result = save_feedback(user_id, prediction_id, feedback_text)
        if result:
            return jsonify({'message': 'Feedback submitted successfully!'})
        else:
            return jsonify({'error': 'Failed to submit feedback'}), 500
    except Exception as e:
        #  Provide detailed error info
        error_message = f"Prediction failed: {str(e)}"
        print(error_message)
        return jsonify({'error': error_message}), 500

    
@app.route('/') 
def index():
    return jsonify({'message': 'Flask backend is running.'})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
