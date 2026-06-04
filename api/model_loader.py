import joblib
import os
import pandas as pd

# Note: knn_model.pkl is not loaded here
# The recommender uses masked cosine similarity instead
# This performs better for sparse student vectors

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'saved_models')
DATA_DIR = os.path.join(BASE_DIR, 'data')

def load_models():
    print("Loading models...")

    X               = joblib.load(os.path.join(MODELS_DIR, 'feature_matrix.pkl'))
    y               = joblib.load(os.path.join(MODELS_DIR, 'target_y.pkl'))
    encoders        = joblib.load(os.path.join(MODELS_DIR, 'encoders.pkl'))
    machine_info    = joblib.load(os.path.join(MODELS_DIR, 'machine_info.pkl'))
    rf_best         = joblib.load(os.path.join(MODELS_DIR, 'random_forest.pkl'))
    feature_weights = joblib.load(os.path.join(MODELS_DIR, 'feature_weights.pkl'))
    scaler          = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))

    print("Models loaded successfully")

    return {
        'X':               X,
        'y':               y,
        'encoders':        encoders,
        'machine_info':    machine_info,
        'rf_best':         rf_best,
        'feature_weights': feature_weights,
        'scaler':          scaler
    }

def load_dataset():
    df = pd.read_csv(os.path.join(DATA_DIR, 'dataset_final.csv'))
    print(f"Dataset loaded: {len(df)} machines")
    return df