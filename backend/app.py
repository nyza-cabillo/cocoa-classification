import io
import os
import numpy as np
from flask import Flask, request, jsonify
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet import preprocess_input as resnet_preprocess
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D, Dropout, Dense
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Supabase Client Initialization
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = Flask(__name__)

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

# Preprocess image
def prepare_image(image):
    image = image.resize(INPUT_SHAPE[:2])
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    return resnet_preprocess(image)

# Save prediction to Supabase
def save_prediction(user_id, image_url, predicted_class, confidence):
    try:
        # Save to prediction table
        response = supabase.table('prediction').insert({
            'user_id': user_id,
            'image_url': image_url,
            'predicted_class': predicted_class,
            'confidence': confidence,
            'created_at': datetime.utcnow().isoformat()
        }).execute()

        # Return response
        if response.error:
            print(f"Error saving prediction: {response.error.message}")
        return response.data[0]['id']  # Return prediction_id
    except Exception as e:
        print(f"Error in saving prediction: {str(e)}")
        return None

# Save feedback to Supabase
def save_feedback(user_id, prediction_id, feedback_text):
    try:
        # Save feedback to feedback table
        response = supabase.table('feedback').insert({
            'user_id': user_id,
            'prediction_id': prediction_id,
            'feedback_text': feedback_text,
            'created_at': datetime.utcnow().isoformat()
        }).execute()

        # Return feedback result
        if response.error:
            print(f"Error saving feedback: {response.error.message}")
        return response.data
    except Exception as e:
        print(f"Error in saving feedback: {str(e)}")
        return None

# Prediction route
@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Load and preprocess the image
        image = load_img(io.BytesIO(file.read()))
        processed_img = prepare_image(image)

        # Make prediction
        preds = model.predict(processed_img)
        pred_idx = np.argmax(preds)
        confidence = float(f"{preds[0][pred_idx]:.4f}")
        predicted_class = CLASS_NAMES[pred_idx]

        # Return result as JSON
        return jsonify({
            'prediction': predicted_class,
            'confidence': confidence
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Feedback route
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    user_id = data.get('user_id')
    prediction_id = data.get('prediction_id')
    feedback_text = data.get('feedback_text')

    if not user_id or not prediction_id or not feedback_text:
        return jsonify({'error': 'Missing data for feedback submission'}), 400

    try:
        # Save feedback to Supabase
        result = save_feedback(user_id, prediction_id, feedback_text)
        
        if result:
            return jsonify({'message': 'Feedback submitted successfully!'})
        else:
            return jsonify({'error': 'Failed to submit feedback'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
