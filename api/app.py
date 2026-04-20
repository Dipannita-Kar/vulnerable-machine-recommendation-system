from flask import Flask, request, jsonify
from flask_cors import CORS
from model_loader import load_models, load_dataset
from recommender_engine import build_expansion_map, recommend

app = Flask(__name__)
CORS(app)

# Load everything once when API starts
# All requests use these loaded models — no reloading per request
print("Starting CyberPath API...")
models        = load_models()
df            = load_dataset()
expansion_map = build_expansion_map(df)
print("CyberPath API ready")

# ── ROUTES ─────

@app.route('/')
def home():
    return jsonify({'status': 'CyberPath API is running', 'version': '1.0'})

@app.route('/recommend', methods=['POST'])
def get_recommendations():
    data = request.get_json()

    # Protect against missing JSON body
    if not data:
        return jsonify({'error': 'No JSON data received'}), 400

    # Required fields
    difficulty      = data.get('difficulty')
    attack_category = data.get('attack_category')
    os_pref         = data.get('os_pref')

    # Validate required fields
    if not all([difficulty, attack_category, os_pref]):
        return jsonify({
            'error': 'difficulty, attack_category and os_pref are required'
        }), 400

    # Optional fields
    vuln_type           = data.get('vuln_type') or None
    learning_objectives = data.get('learning_objectives') or None
    skills              = data.get('skills') or None
    entry_point         = data.get('entry_point') or None
    platform            = data.get('platform') or None

    # Safely convert n_recommendations to integer
    try:
        n_recommendations = int(data.get('n_recommendations', 5))
    except (TypeError, ValueError):
        return jsonify({'error': 'n_recommendations must be an integer'}), 400

    results, fallback_msg, match_mode, reason, confidence, confidence_msg = recommend(
        models          = models,
        expansion_map   = expansion_map,
        difficulty      = difficulty,
        attack_category = attack_category,
        os_pref         = os_pref,
        vuln_type       = vuln_type,
        learning_objectives = learning_objectives,
        skills          = skills,
        entry_point     = entry_point,
        platform        = platform,
        n_recommendations = n_recommendations
    )

    return jsonify({
        'results':        results,
        'match_mode':     match_mode,
        'reason':         reason,
        'confidence':     confidence,
        'confidence_msg': confidence_msg,
        'fallback_msg':   fallback_msg
    })

@app.route('/options', methods=['GET'])
def get_options():
    # Returns all valid dropdown options for the frontend
    # os_pref key matches what /recommend expects
    return jsonify({
        'difficulty': ['Easy', 'Medium', 'Hard'],
        'os_pref':    ['Linux', 'Windows', 'FreeBSD'],
        'attack_category': [
            'Web Exploitation',
            'Network Exploitation',
            'Binary Exploitation',
            'Cryptographic Exploitation',
            'Mixed (Web + Network)',
            'Credential-Based Exploitation'
        ],
        'vuln_type': [
            'SQL Injection', 'File Upload',
            'Local File Inclusion (LFI)',
            'Remote Code Execution', 'Command Injection',
            'Blind SQL Injection', 'Insecure Deserialization',
            'WordPress Exploitation', 'Buffer Overflow',
            'SMB Enumeration', 'Weak Credentials'
        ],
        'learning_objectives': [
            'SQL Injection', 'File Upload', 'Privilege Escalation',
            'Credential Extraction', 'Reverse Shell', 'Web Enumeration',
            'SSH Access', 'Brute Force', 'SMB Enumeration',
            'Network Pivoting', 'Buffer Overflow', 'Steganography',
            'Hash Cracking', 'Directory Bruteforce', 'Port Scanning'
        ],
        'platform': ['VulnHub', 'HackTheBox']
    })

@app.route('/model-stats', methods=['GET'])
def model_stats():
    # Returns model performance stats for display
    return jsonify({
        'accuracy':    90.16,
        'cv_accuracy': 91.41,
        'total_machines': 305,
        'difficulty_breakdown': {
            'Easy':   40,
            'Medium': 159,
            'Hard':   106
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)