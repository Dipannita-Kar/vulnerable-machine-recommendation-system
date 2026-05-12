from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from model_loader import load_models, load_dataset
from recommender_engine import build_expansion_map, recommend
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Load everything once when API starts
print("Starting CyberPath API...")
models        = load_models()
df            = load_dataset()
expansion_map = build_expansion_map(df)
print("CyberPath API ready")

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('../frontend', path)

@app.route('/recommend', methods=['POST'])
def get_recommendations():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No JSON data received'}), 400

    # Required fields
    difficulty         = data.get('difficulty')
    attack_categories  = data.get('attack_categories')
    os_pref            = data.get('os_pref')

    if not all([difficulty, attack_categories, os_pref]):
        return jsonify({
            'error': 'difficulty, attack_categories and os_pref are required'
        }), 400

    # Ensure attack_categories is a list
    if isinstance(attack_categories, str):
        attack_categories = [attack_categories]

    # Optional fields
    vuln_type           = data.get('vuln_type') or None
    learning_objectives = data.get('learning_objectives') or None
    estimated_time      = data.get('estimated_time') or None
    platform            = data.get('platform') or None

    # Safely convert n_recommendations to integer
    try:
        n_recommendations = int(data.get('n_recommendations', 5))
    except (TypeError, ValueError):
        return jsonify({'error': 'n_recommendations must be an integer'}), 400

    # Run recommendation engine
    try:
        results, fallback_msg, match_mode, reason, confidence, confidence_msg = recommend(
            models              = models,
            expansion_map       = expansion_map,
            difficulty          = difficulty,
            attack_categories   = attack_categories,
            os_pref             = os_pref,
            vuln_type           = vuln_type,
            learning_objectives = learning_objectives,
            estimated_time      = estimated_time,
            platform            = platform,
            n_recommendations   = n_recommendations
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    return jsonify({
        'difficulty': ['Easy', 'Medium', 'Hard'],
        'os_pref':    ['Linux', 'Windows'],
        'attack_category': [
            'Web Exploitation',
            'Network Exploitation',
            'Binary Exploitation',
            'Cryptographic Exploitation',
            'Mixed (Web + Network)',
            'Credential-Based Exploitation'
        ],
        'learning_objectives_specific': [
            'SQL Injection', 'File Upload Bypass', 'File Upload Exploitation',
            'Local File Inclusion', 'Buffer Overflow', 'Encoding/Decoding',
            'Steganography Extraction', 'WordPress Exploitation', 'SMB Enumeration',
            'SUID Exploitation', 'Network Pivoting', 'Hash Cracking',
            'Webshell Execution', 'FTP Enumeration', 'Default Credentials',
            'Source Code Analysis', 'Database Enumeration', 'Command Execution'
        ],
        'learning_objectives_general': [
            'Privilege Escalation', 'Web Enumeration', 'Credential Extraction',
            'Reverse Shell', 'SSH Access', 'Remote Code Execution',
            'Authentication Bypass', 'Sudo Exploitation'
        ],
        'vuln_type': [
            'SQL Injection', 'Information Disclosure', 'Local File Inclusion',
            'Web Enumeration', 'Weak Credentials', 'WordPress Exploitation',
            'SMB Enumeration', 'Default Credentials', 'Command Injection',
            'Source Code Analysis'
        ],
        'estimated_time': [
            'Less than 1 hour', '1-2 hours', '2-3 hours',
            '3-4 hours', '4+ hours'
        ],
        'platform': ['VulnHub', 'HackTheBox']
    })

@app.route('/model-stats', methods=['GET'])
def model_stats():
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