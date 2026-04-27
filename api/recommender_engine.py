import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as cos_sim

# ── CONSTANTS ─────────────────────────────────────────────────────────────────

# Specific techniques — high discriminating power
# These appear in fewer machines so they help distinguish recommendations
SPECIFIC_OBJECTIVES = {
    'SQL Injection', 'File Upload Bypass', 'File Upload Exploitation',
    'Local File Inclusion', 'Buffer Overflow', 'Encoding/Decoding',
    'Steganography Extraction', 'WordPress Exploitation', 'SMB Enumeration',
    'SUID Exploitation', 'Network Pivoting', 'Hash Cracking',
    'Webshell Execution', 'FTP Enumeration', 'Default Credentials',
    'Source Code Analysis', 'Database Enumeration', 'Command Execution'
}

# General learning goals — appear in many machines, lower weight
GENERAL_OBJECTIVES = {
    'Privilege Escalation', 'Web Enumeration', 'Credential Extraction',
    'Reverse Shell', 'SSH Access', 'Remote Code Execution',
    'Authentication Bypass', 'Sudo Exploitation'
}

# Estimated time ranges in hours
TIME_RANGES = {
    'Less than 1 hour': (0, 1),
    '1-2 hours':        (1, 2),
    '2-3 hours':        (2, 3),
    '3-4 hours':        (3, 4),
    '4+ hours':         (4, 99)
}

# ── HELPER FUNCTIONS ──────────────────────────────────────────────────────────

def split_vulnerability_values(text):
    # Splits vulnerability chain on → only
    # Verified: → is the only chain separator in the dataset
    if not text or pd.isna(text):
        return []
    parts = str(text).split('→')
    cleaned = []
    for part in parts:
        part = part.split('(')[0].strip()
        if part:
            cleaned.append(part)
    return cleaned

def split_semicolon_values(text):
    if not text or pd.isna(text):
        return []
    return [item.strip() for item in str(text).split(';') if item.strip()]

def category_matches(machine_category, attack_categories):
    # Check exact match first
    if machine_category in attack_categories:
        return True
    # Check if any selected category is contained in machine category
    # This handles 'Mixed (Web + Network)' matching when user selects 'Web Exploitation'
    for cat in attack_categories:
        if cat.split(' ')[0] in machine_category:
            return True
    return False

# ── EXPANSION MAP ─────────────────────────────────────────────────────────────
# Kept for potential future use but NOT applied to student vector
# Removed from recommendations after evaluation showed it introduced noise
# at this dataset size (305 machines)

def build_expansion_map(df, top_n=5, min_frequency=0.2):
    expansion_map = {}

    all_skills_total = []
    for s in df['Skills_Required'].dropna():
        all_skills_total.extend(split_semicolon_values(s))
    total_skill_counts = pd.Series(all_skills_total).value_counts()
    total_machines = len(df)

    all_obj_total = []
    for s in df['Learning_Objectives'].dropna():
        all_obj_total.extend(split_semicolon_values(s))
    total_obj_counts = pd.Series(all_obj_total).value_counts()

    all_vulns = set()
    for val in df['Vulnerability_Type'].dropna():
        all_vulns.update(split_vulnerability_values(val))

    for vuln in all_vulns:
        mask = df['Vulnerability_Type'].fillna('').apply(
            lambda x: vuln in split_vulnerability_values(x)
        )
        machines = df[mask]
        group_size = len(machines)
        if group_size < 3:
            continue

        all_skills = []
        for s in machines['Skills_Required'].dropna():
            all_skills.extend(split_semicolon_values(s))
        if all_skills:
            skill_counts = pd.Series(all_skills).value_counts()
            balanced_scores = {}
            for skill, count in skill_counts.items():
                freq_in_group = count / group_size
                if freq_in_group >= min_frequency:
                    freq_overall = total_skill_counts.get(skill, 1) / total_machines
                    balanced_scores[skill] = freq_in_group / (freq_overall + 0.01)
            expansion_map[f'vuln_skills_{vuln}'] = pd.Series(
                balanced_scores).sort_values(ascending=False).head(top_n).index.tolist()

        all_objectives = []
        for s in machines['Learning_Objectives'].dropna():
            all_objectives.extend(split_semicolon_values(s))
        if all_objectives:
            obj_counts = pd.Series(all_objectives).value_counts()
            balanced_scores = {}
            for obj, count in obj_counts.items():
                freq_in_group = count / group_size
                if freq_in_group >= min_frequency:
                    freq_overall = total_obj_counts.get(obj, 1) / total_machines
                    balanced_scores[obj] = freq_in_group / (freq_overall + 0.01)
            expansion_map[f'vuln_objs_{vuln}'] = pd.Series(
                balanced_scores).sort_values(ascending=False).head(top_n).index.tolist()

    for cat in df['Attack_Category'].dropna().unique():
        mask = df['Attack_Category'] == cat
        machines = df[mask]
        group_size = len(machines)

        all_skills = []
        for s in machines['Skills_Required'].dropna():
            all_skills.extend(split_semicolon_values(s))
        if all_skills:
            skill_counts = pd.Series(all_skills).value_counts()
            balanced_scores = {}
            for skill, count in skill_counts.items():
                freq_in_group = count / group_size
                if freq_in_group >= min_frequency:
                    freq_overall = total_skill_counts.get(skill, 1) / total_machines
                    balanced_scores[skill] = freq_in_group / (freq_overall + 0.01)
            expansion_map[f'cat_skills_{cat}'] = pd.Series(
                balanced_scores).sort_values(ascending=False).head(top_n).index.tolist()

        all_objectives = []
        for s in machines['Learning_Objectives'].dropna():
            all_objectives.extend(split_semicolon_values(s))
        if all_objectives:
            obj_counts = pd.Series(all_objectives).value_counts()
            balanced_scores = {}
            for obj, count in obj_counts.items():
                freq_in_group = count / group_size
                if freq_in_group >= min_frequency:
                    freq_overall = total_obj_counts.get(obj, 1) / total_machines
                    balanced_scores[obj] = freq_in_group / (freq_overall + 0.01)
            expansion_map[f'cat_objs_{cat}'] = pd.Series(
                balanced_scores).sort_values(ascending=False).head(top_n).index.tolist()

    return expansion_map

# ── CONFIDENCE ────────────────────────────────────────────────────────────────

def get_confidence_label(active_features_count):
    if active_features_count >= 8:
        return "High", None
    elif active_features_count >= 5:
        return "Medium", "Add optional fields for better recommendations."
    else:
        return "Low", "Add more preferences for more accurate recommendations."

# ── FALLBACK ──────────────────────────────────────────────────────────────────

def get_machines_by_category(machine_info, attack_categories, difficulty=None):
    # Uses category_matches to handle Mixed categories correctly
    mask = machine_info['Attack_Category'].apply(
        lambda x: category_matches(str(x), attack_categories)
    )
    if difficulty:
        mask = mask & (machine_info['Difficulty'] == difficulty)
    return machine_info[mask].index.tolist()

def get_available_machines_with_fallback(machine_info, attack_categories, difficulty, min_machines=5):
    # Step 1: exact difficulty + category
    exact_indices = get_machines_by_category(machine_info, attack_categories, difficulty)
    if len(exact_indices) >= min_machines:
        return exact_indices, "exact"

    # Step 2: relax difficulty by one level
    diff_order = ['Easy', 'Medium', 'Hard']
    diff_idx = diff_order.index(difficulty) if difficulty in diff_order else 1
    nearby_diffs = []
    if diff_idx > 0:
        nearby_diffs.append(diff_order[diff_idx - 1])
    if diff_idx < 2:
        nearby_diffs.append(diff_order[diff_idx + 1])

    relaxed_indices = list(set(exact_indices))
    for d in nearby_diffs:
        relaxed_indices.extend(get_machines_by_category(machine_info, attack_categories, d))
    relaxed_indices = list(set(relaxed_indices))
    if len(relaxed_indices) >= min_machines:
        return relaxed_indices, "relaxed_difficulty"

    # Step 3: category only any difficulty
    category_only = get_machines_by_category(machine_info, attack_categories)
    if len(category_only) >= min_machines:
        return category_only, "category_only"

    # Step 4: all machines
    return machine_info.index.tolist(), "all"

def get_fallback_message(mode, attack_categories, difficulty):
    cat_str = ', '.join(attack_categories)
    if mode == "exact":
        return None, "Exact Match", None
    elif mode == "relaxed_difficulty":
        return (
            f"Limited {difficulty} machines found for '{cat_str}'. Showing nearby difficulty levels.",
            "Relaxed Difficulty",
            f"Not enough exact {difficulty} matches — showing nearby difficulty levels too."
        )
    elif mode == "category_only":
        return (
            f"Limited {difficulty} machines for '{cat_str}'. Showing all difficulty levels.",
            "Category Match",
            f"Exact difficulty match not available — showing all difficulty levels for '{cat_str}'."
        )
    else:
        return (
            "Very limited machines found. Showing best overall matches.",
            "Broad Match",
            "Dataset has very few machines matching your preferences."
        )

# ── SIMILARITY ────────────────────────────────────────────────────────────────

def masked_cosine_similarity(student_vector, machine_matrix):
    # Compare only on features student actually specified
    # Zero features ignored so they do not dilute the score
    student_array = student_vector.values[0]
    active_mask = student_array != 0
    if active_mask.sum() == 0:
        active_mask = np.ones(len(active_mask), dtype=bool)
    student_active = student_array[active_mask].reshape(1, -1)
    machines_active = machine_matrix.values[:, active_mask]
    return cos_sim(student_active, machines_active)[0]

# ── MATCH SCORE FUNCTIONS ─────────────────────────────────────────────────────

def compute_objective_match(machine_objectives_str, requested_objectives):
    # Specific objectives weighted 1.0, general objectives weighted 0.5
    if not requested_objectives:
        return 1.0, [], []
    machine_objectives = set(split_semicolon_values(machine_objectives_str or ''))
    matched = []
    missing = []
    total_weight = 0
    matched_weight = 0
    for obj in requested_objectives:
        weight = 1.0 if obj in SPECIFIC_OBJECTIVES else 0.5
        total_weight += weight
        if obj in machine_objectives:
            matched.append(obj)
            matched_weight += weight
        else:
            missing.append(obj)
    score = matched_weight / total_weight if total_weight > 0 else 0
    return score, matched, missing

def compute_vuln_match(machine_vuln_str, requested_vuln):
    # Check if requested vulnerability appears anywhere in machine chain
    if not requested_vuln:
        return 1.0, True
    machine_vulns = set(split_vulnerability_values(machine_vuln_str or ''))
    matched = requested_vuln in machine_vulns
    return (1.0 if matched else 0.0), matched

def compute_time_match(machine_time_hours, requested_time_str):
    if not requested_time_str or requested_time_str not in TIME_RANGES:
        return 1.0, True
    try:
        machine_hours = float(machine_time_hours)
    except (TypeError, ValueError):
        return 0.5, False
    low, high = TIME_RANGES[requested_time_str]
    if low <= machine_hours <= high:
        return 1.0, True
    diff = min(abs(machine_hours - low), abs(machine_hours - high))
    if diff <= 1.5:
        return 0.5, False
    return 0.0, False

def compute_os_match(machine_os, requested_os):
    if not requested_os:
        return 1.0, True
    matched = str(machine_os) == str(requested_os)
    return (1.0 if matched else 0.0), matched

def compute_difficulty_match(machine_difficulty, requested_difficulty):
    if machine_difficulty == requested_difficulty:
        return 1.0
    diff_order = {'Easy': 1, 'Medium': 2, 'Hard': 3}
    diff = abs(diff_order.get(machine_difficulty, 2) - diff_order.get(requested_difficulty, 2))
    return 0.5 if diff == 1 else 0.0

# ── STUDENT VECTOR ────────────────────────────────────────────────────────────

def build_student_vector(
    X, expansion_map,
    difficulty,
    attack_categories,
    os_pref,
    vuln_type=None,
    learning_objectives=None,
    estimated_time=None,
    platform=None
):
    # Build vector using only what student explicitly selected
    # Expansion map removed — tested and found to introduce noise
    # at 305 machine dataset size

    student_vector = pd.DataFrame(
        np.zeros((1, X.shape[1])),
        columns=X.columns
    )

    # Difficulty — weight 2.0
    diff_map = {'Easy': 0.0, 'Medium': 0.5, 'Hard': 1.0}
    if 'implicit_difficulty' in student_vector.columns:
        student_vector['implicit_difficulty'] = diff_map.get(difficulty, 0.5) * 2.0

    # Attack categories — weight 3.0
    for cat in attack_categories:
        attack_col = f"attack_{cat}"
        if attack_col in student_vector.columns:
            student_vector[attack_col] = 3.0

    # OS — weight 1.0
    os_col = f"os_{os_pref}"
    if os_col in student_vector.columns:
        student_vector[os_col] = 1.0

    # Vulnerability type — weight 1.5
    if vuln_type:
        vuln_col = f"vuln__{vuln_type}"
        if vuln_col in student_vector.columns:
            student_vector[vuln_col] = 1.5

    # Learning objectives — specific=3.0, general=1.5
    if learning_objectives:
        for obj in learning_objectives:
            obj_col = f"obj__{obj}"
            if obj_col in student_vector.columns:
                weight = 3.0 if obj in SPECIFIC_OBJECTIVES else 1.5
                student_vector[obj_col] = weight

    # Platform
    if platform:
        plat_map = {'VulnHub': 0.0, 'HackTheBox': 1.0}
        if 'Platform_ID' in student_vector.columns:
            student_vector['Platform_ID'] = plat_map.get(platform, 0.0)

    return student_vector

# ── MAIN RECOMMEND FUNCTION ───────────────────────────────────────────────────

def recommend(
    models, expansion_map,
    difficulty,
    attack_categories,
    os_pref,
    vuln_type=None,
    learning_objectives=None,
    estimated_time=None,
    platform=None,
    n_recommendations=5
):
    if isinstance(attack_categories, str):
        attack_categories = [attack_categories]

    X               = models['X']
    machine_info    = models['machine_info']
    rf_best         = models['rf_best']
    feature_weights = models['feature_weights']

    # Build student vector from explicit inputs only
    student_vector = build_student_vector(
        X, expansion_map,
        difficulty, attack_categories, os_pref,
        vuln_type, learning_objectives,
        estimated_time, platform
    )

    # Get available machines with fallback
    available_indices, mode = get_available_machines_with_fallback(
        machine_info, attack_categories, difficulty
    )
    fallback_msg, match_mode, reason = get_fallback_message(
        mode, attack_categories, difficulty
    )

    # Platform filter
    if platform:
        available_indices = [
            i for i in available_indices
            if machine_info.iloc[i]['Platform'] == platform
        ]
        if len(available_indices) == 0:
            return [], None, "No Match", \
                f"No '{platform}' machines found. Try 'All Platforms'.", "Low", None

    # Compute cosine similarity
    X_available = X.iloc[available_indices]
    student_vector_weighted = student_vector * feature_weights
    X_available_weighted    = X_available * feature_weights
    cosine_scores = masked_cosine_similarity(
        student_vector_weighted, X_available_weighted
    )

    results = []
    for local_idx, global_idx in enumerate(available_indices):
        machine  = machine_info.iloc[global_idx]
        cosine   = float(cosine_scores[local_idx])
        rf_pred  = rf_best.predict(X.iloc[global_idx:global_idx+1])[0]
        rf_label = {1: 'Easy', 2: 'Medium', 3: 'Hard'}[int(rf_pred)]

        # Compute all match scores
        obj_score, matched_objs, missing_objs = compute_objective_match(
            machine.get('Learning_Objectives', ''),
            learning_objectives or []
        )
        vuln_score, vuln_matched = compute_vuln_match(
            machine.get('Vulnerability_Type', ''), vuln_type
        )
        time_score, time_matched = compute_time_match(
            machine.get('Estimated_Time_Hours', None), estimated_time
        )
        os_score, os_matched = compute_os_match(
            machine.get('OS', ''), os_pref
        )
        diff_score = compute_difficulty_match(
            str(machine.get('Difficulty', '')), difficulty
        )

        # Small RF bonus when RF predicted difficulty agrees with student request
        rf_bonus = 0.05 if rf_label == difficulty else 0.0

        # Final score
        if estimated_time:
            final_score = (
                0.50 * obj_score +
                0.15 * vuln_score +
                0.15 * time_score +
                0.10 * os_score +
                0.10 * cosine +
                rf_bonus
            )
        else:
            final_score = (
                0.50 * obj_score +
                0.15 * vuln_score +
                0.10 * os_score +
                0.25 * cosine +
                rf_bonus
            )

        # Hard rule — 0 objectives matched → push to bottom
        if learning_objectives and len(matched_objs) == 0:
            final_score = final_score * 0.1

        # Determine tier based on learning objectives
        if learning_objectives:
            if len(matched_objs) == len(learning_objectives) and \
               str(machine.get('Difficulty')) == difficulty and \
               category_matches(str(machine.get('Attack_Category')), attack_categories):
                tier = "Perfect Match"
            elif len(matched_objs) > 0 and \
                 str(machine.get('Difficulty')) == difficulty and \
                 category_matches(str(machine.get('Attack_Category')), attack_categories):
                tier = "Partial Match"
            else:
                tier = "Fallback"
        else:
            if str(machine.get('Difficulty')) == difficulty and \
               category_matches(str(machine.get('Attack_Category')), attack_categories):
                tier = "Perfect Match"
            else:
                tier = "Partial Match"

        # Build matched and missing features
        matched_features = []
        missing_features = []

        if str(machine.get('Difficulty')) == difficulty:
            matched_features.append(f"Difficulty: {difficulty}")
        else:
            missing_features.append(
                f"You requested '{difficulty}' but this machine is '{machine.get('Difficulty')}'"
            )

        if category_matches(str(machine.get('Attack_Category')), attack_categories):
            matched_features.append(f"Attack Category: {machine.get('Attack_Category')}")
        else:
            missing_features.append(
                f"You requested '{', '.join(attack_categories)}' but this machine is '{machine.get('Attack_Category')}'"
            )

        if os_matched:
            matched_features.append(f"OS: {os_pref}")
        else:
            missing_features.append(
                f"You requested '{os_pref}' but this machine runs '{machine.get('OS')}'"
            )

        for obj in matched_objs:
            matched_features.append(f"Learning Objective: {obj}")
        for obj in missing_objs:
            missing_features.append(
                f"You requested '{obj}' but this machine does not have it"
            )

        if vuln_type:
            if vuln_matched:
                matched_features.append(f"Vulnerability Type: {vuln_type}")
            else:
                missing_features.append(
                    f"You requested '{vuln_type}' but this machine does not have it"
                )

        if estimated_time:
            if time_matched:
                matched_features.append(f"Estimated Time: {estimated_time}")
            else:
                missing_features.append(
                    f"You requested '{estimated_time}' but this machine takes '{machine.get('Estimated_Time')}'"
                )

        # Weighted relevance score — consistent with scoring formula
        if estimated_time:
            relevance_score = round((
                0.50 * obj_score +
                0.15 * vuln_score +
                0.15 * time_score +
                0.10 * os_score +
                0.10 * diff_score
            ) * 100, 1)
        else:
            relevance_score = round((
                0.50 * obj_score +
                0.15 * vuln_score +
                0.10 * os_score +
                0.25 * diff_score
            ) * 100, 1)

        results.append({
            'rank':                    0,
            'machine_name':            str(machine['Machine_Name']),
            'platform':                str(machine['Platform']),
            'os':                      str(machine['OS']),
            'difficulty':              str(machine['Difficulty']),
            'rf_predicted_difficulty': rf_label,
            'attack_category':         str(machine['Attack_Category']),
            'entry_point':             str(machine.get('Entry_Point', '')),
            'estimated_time':          str(machine.get('Estimated_Time', '')),
            'estimated_time_hours':    float(machine.get('Estimated_Time_Hours', 0) or 0),
            'attack_path_length':      int(machine.get('Attack_Path_Length', 0) or 0),
            'skills_required':         str(machine.get('Skills_Required', '')),
            'learning_objectives':     str(machine.get('Learning_Objectives', '')),
            'vulnerability_type':      str(machine.get('Vulnerability_Type', '')),
            'kill_chain_stages':       str(machine.get('Kill_Chain_Stages', '')),
            'similarity_score':        round(float(cosine) * 100, 2),
            'final_score':             round(float(final_score) * 100, 2),
            'relevance_score':         float(relevance_score),
            'tier':                    tier,
            'matched_features':        matched_features,
            'missing_features':        missing_features,
            'objective_match':         f"{len(matched_objs)}/{len(learning_objectives)}" if learning_objectives else "N/A"
        })

    # Sort by tier first then final score
    tier_order = {'Perfect Match': 0, 'Partial Match': 1, 'Fallback': 2}
    results = sorted(results, key=lambda x: (
        tier_order.get(x['tier'], 3),
        -x['final_score']
    ))

    for i, r in enumerate(results[:n_recommendations]):
        r['rank'] = i + 1

    active_count = int((student_vector.values[0] != 0).sum())
    confidence_label, confidence_msg = get_confidence_label(active_count)

    return (
        results[:n_recommendations],
        fallback_msg,
        match_mode,
        reason,
        confidence_label,
        confidence_msg
    )