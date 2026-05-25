# loads everything needed for the v2 ai recommender
import joblib
import os
import pandas as pd

# path to the v2 saved models folder
HERE = os.path.dirname(os.path.abspath(__file__))
V2_DIR = os.path.join(HERE, '..', 'saved_models', 'ai_recommender')

print("loading v2 ai recommender artifacts...")

xgb_model = joblib.load(os.path.join(V2_DIR, 'xgboost_ranker.pkl'))
rf_model = joblib.load(os.path.join(V2_DIR, 'random_forest_ranker.pkl'))
lr_model = joblib.load(os.path.join(V2_DIR, 'linear_regression.pkl'))
machine_features = joblib.load(os.path.join(V2_DIR, 'machine_features.pkl'))
machine_info = joblib.load(os.path.join(V2_DIR, 'machine_info_v2.pkl'))
obj_encoder = joblib.load(os.path.join(V2_DIR, 'obj_encoder.pkl'))

# pulling out useful columns and counts
feature_columns = list(machine_features.columns)
n_machines = len(machine_info)

# value mappings used for building student vectors
diff_map = {'Easy': 1, 'Medium': 2, 'Hard': 3}

time_to_hours = {
    '<1 hour':   0.5,
    '1-2 hours': 1.5,
    '2-3 hours': 2.5,
    '3-4 hours': 3.5,
    '4+ hours':  4.5
}

skill_to_num = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3}

print(f"  loaded xgboost, rf, linear regression")
print(f"  machine features: {machine_features.shape}")
print(f"  machines: {n_machines}")
print(f"  feature columns: {len(feature_columns)}")