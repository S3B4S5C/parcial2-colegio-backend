# utils/ml_model.py
import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), './modelo_rendimiento.pkl')
model = None

def get_ml_model():
    global model
    if model is None:
        model = joblib.load(MODEL_PATH)
    return model
