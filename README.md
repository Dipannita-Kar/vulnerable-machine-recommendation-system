# Vulnerable Machine Recommendation System
This is my Masters project for COMP6016 at Curtin University.
CyberPath : AI-Powered Vulnerable Machine Recommendation System
CyberPath is a web  application that recommends intentionally vulnerable machines from VulnHub to cybersecurity students based on their learning preferences. The system uses machine learning to match students with appropriate practice machines based on difficulty, attack category, operating system, and learning objectives.

### Features

Iteration 1 — Rule-Based Recommender: Content-based recommendation engine using a trained Random Forest difficulty classifier, masked cosine similarity, two-tier learning objective weighting, and a four-level fallback mechanism.
Iteration 2 (The final product)— AI Recommender: Supervised XGBoost recommendation model trained on 610,000 synthetic student-machine interaction pairs, providing relevance-scored recommendations with quality labels.
Difficulty Predictor: Standalone tool that uses the trained Random Forest classifier to predict the difficulty level of any machine in the dataset with confidence percentage.
Transparency: Per-machine matched and missing feature explanations for every recommendation so students understand exactly why each machine was suggested.


### Project Structure
```
Vuln Recommendation system/
├── api/
│   ├── app.py                  # Main Flask application — all 7 endpoints
│   ├── model_loader.py         # Loads Iteration 1 model artefacts at startup
│   ├── model_loader_ai.py      # Loads Iteration 2 model artefacts at startup
│   ├── recommender_engine.py   # Iteration 1 recommendation logic
│   └── recommender_ai.py       # Iteration 2 XGBoost recommendation logic
├── frontend/
│   ├── index.html              # Homepage
│   ├── recommend.html          # Iteration 1 preference form
│   ├── results.html            # Iteration 1 results page
│   ├── recommend_ai.html       # Iteration 2 preference form
│   ├── results_ai.html         # Iteration 2 results page
│   ├── predict.html            # Difficulty predictor page
│   ├── about.html              # About page
│   ├── main.js                 # Iteration 1 JavaScript
│   ├── main_ai.js              # Iteration 2 JavaScript
│   └── style.css               # Shared stylesheet
├── data/
│   ├── dataset_final.csv       # 305-machine dataset for Iteration 1 (18 columns)
│   └── dataset_v2_ai_clean.csv # Cleaned dataset for Iteration 2
├── notebooks/
│   └── ai_recommender.ipynb   # Full Iteration 2 training pipeline (9 cells)
├── saved_models/
│   ├── random_forest.pkl       # Trained RF difficulty classifier
│   ├── feature_matrix.pkl      # 305x771 weighted feature matrix
│   ├── feature_weights.pkl     # RF-derived feature importance weights
│   ├── encoders.pkl            # Fitted sklearn encoders
│   ├── scaler.pkl              # Fitted MinMaxScaler
│   ├── machine_info.pkl        # Machine information dataframe
│   ├── target_y.pkl            # Difficulty labels
│   └── ai_recommender/
│       ├── xgboost_ranker.pkl      # Trained XGBoost ranking model
│       ├── machine_features.pkl    # 305x111 machine feature matrix
│       ├── machine_info_v2.pkl     # Machine info for Iteration 2
│       ├── obj_encoder.pkl         # Fitted MultiLabelBinarizer
│       └── plots/                  # Evaluation plots
└── README.md
```
### Requirements

Python 3.12.5 or later
pip


Installation
Step 1 — Clone the repository
bashgit clone https://github.com/Dipannita-Kar/vulnerable-machine-recommendation-system
cd vulnerable-machine-recommendation-system
Step 2 — Install dependencies
bashpip install flask flask-cors pandas numpy scikit-learn xgboost joblib matplotlib
Step 3 — Verify model artefacts
Make sure the following files are present before running:
Iteration 1 (saved_models/):

random_forest.pkl
feature_matrix.pkl
feature_weights.pkl
encoders.pkl
scaler.pkl
machine_info.pkl
target_y.pkl

Iteration 2 (saved_models/ai_recommender/):

xgboost_ranker.pkl
machine_features.pkl
machine_info_v2.pkl
obj_encoder.pkl

Step 4 — Run the application
bashcd api
python app.py
Open your browser and go to: http://127.0.0.1:5000

### Large Files (Excluded from Repository)

The following files exceed GitHub's 100 MB limit and are excluded via .gitignore:

| File | Size | How to Regenerate |
|------|------|-------------------|
| training_data.csv | ~528 MB | Run notebooks/ai_recommender.ipynb cells 7 and 8 |
| random_forest_ranker.pkl | ~70 MB | Run notebooks/ai_recommender.ipynb cell 9 |

To regenerate, open notebooks/ai_recommender.ipynb and run all cells from top to bottom. This takes approximately 15 minutes.

API Endpoints
Here's the original simpler version:

| Endpoint          | Method | What it does |
|----------         |--------|--------------|
| `/`               | GET    | Serves the homepage |
| `/recommend`      | POST   | Iteration 1 recommendations |
| `/options`        | GET    | Returns valid dropdown values for the form |
| `/model-stats`    | GET    | RF accuracy and dataset breakdown |
| `/recommend-ai`   | POST   | Iteration 2 XGBoost recommendations |
| `/predict-difficulty` | POST | Predicts difficulty for a named machine |
| `/get-machine-names` | GET | Returns all 305 machine names (for autocomplete) |

### How to Use
Iteration 1 — Rule-Based Recommender (initial approach)

Go to http://127.0.0.1:5000
Click Rule-Based Recommender
Select your difficulty, OS, and attack category (required)
Optionally add learning objectives, vulnerability type, and estimated time
Click Get Recommendations

Iteration 2 — AI Recommender (Final product) 

Go to http://127.0.0.1:5000
Click AI Recommender
Select your difficulty, OS, attack category, and at least one learning objective (all required)
Optionally add estimated time
Click Get AI Recommendations

Difficulty Predictor

Go to http://127.0.0.1:5000
Click Difficulty Predictor
Type a machine name — suggestions appear automatically
Click Predict Difficulty


### Dataset
The dataset contains 305 VulnHub machines with 18 attributes including:

Difficulty (Easy, Medium, Hard)
Attack Category (6 classes)
Learning Objectives (99 unique objectives)
Kill Chain Stages
Skills Required
Estimated Time
Attack Path Length
Entry Point
Vulnerability Type

All data was collected from publicly available VulnHub walkthroughs and penetration testing write-ups.


### KeyKnown Limitations

-The frontend is designed for desktop browsers. Mobile layout is not optimised.
-The Flask development server is not suitable for production deployment.
-Large generated files (training_data.csv and random_forest_ranker.pkl) must be regenerated locally.


### Future Work

-Deploy to real students and collect interaction data to retrain the model on real user preferences.
-Expand dataset to include TryHackMe and HackTheBox machines
-Add user accounts and recommendation history
-Generate structured multi-step learning paths
-Optimise frontend for mobile devices


### Technologies Used
ComponentTechnologyBackendPython 3.12.5, Flask 3.1.7Machine Learningscikit-learn, XGBoostData Processingpandas, NumPyModel SerialisationjoblibFrontendHTML5, CSS3, JavaScriptVersion ControlGit, GitHub

Author
Dipannita Kar
Curtin University — COMP6016 Masters Project
May 2025

Data Source
VulnHub — https://www.vulnhub.com
Vulnhub-CTF-Writeups : https://github.com/Ignitetechnologies/Vulnhub-CTF-Writeups/blob/master/README.md
