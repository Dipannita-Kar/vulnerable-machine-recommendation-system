# This file contains all recommendation logic

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as cos_sim


# ── HELPER FUNCTIONS ─

def split_vulnerability_values(text):
    # Splits vulnerability chain on → and removes parenthetical details
    # Verified: → is the only chain separator in my dataset
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
    # Splits semicolon separated values like Skills_Required
    if not text or pd.isna(text):
        return []
    return [item.strip() for item in str(text).split(';') if item.strip()]

# ── EXPANSION MAP ────────────────────

def build_expansion_map(df, top_n=5, min_frequency=0.2):
    # Learns distinctive related features per vulnerability type and attack category
    # Uses balanced TF-IDF scoring to avoid generic skills like Enumeration
    # appearing everywhere and to find truly distinctive skills per category

    expansion_map = {}

    # Total counts across all machines for IDF calculation
    all_skills_total = []
    for s in df['Skills_Required'].dropna():
        all_skills_total.extend(split_semicolon_values(s))
    total_skill_counts = pd.Series(all_skills_total).value_counts()
    total_machines = len(df)

    all_obj_total = []
    for s in df['Learning_Objectives'].dropna():
        all_obj_total.extend(split_semicolon_values(s))
    total_obj_counts = pd.Series(all_obj_total).value_counts()

    # Expand from vulnerability types
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

        # Skills expansion
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

        # Objectives expansion
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

    # Expand from attack categories
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

# ── CONFIDENCE ─

def get_confidence_label(active_features_count):
    if active_features_count >= 8:
        return "High", None
    elif active_features_count >= 5:
        return "Medium", "Add optional fields for better recommendations."
    else:
        return "Low", "Add more preferences for more accurate recommendations."

# ── FALLBACK ──

def get_machines_by_category(machine_info, attack_category, difficulty=None):
    mask = machine_info['Attack_Category'] == attack_category
    if difficulty:
        mask = mask & (machine_info['Difficulty'] == difficulty)
    return machine_info[mask].index.tolist()

def get_available_machines_with_fallback(machine_info, attack_category, difficulty, min_machines=5):
    exact_indices = get_machines_by_category(machine_info, attack_category, difficulty)
    if len(exact_indices) >= min_machines:
        return exact_indices, "exact"

    category_only = get_machines_by_category(machine_info, attack_category)
    if len(category_only) >= min_machines:
        return category_only, "category_only"

    diff_mask = machine_info['Difficulty'] == difficulty
    diff_indices = machine_info[diff_mask].index.tolist()
    if len(diff_indices) >= min_machines:
        return diff_indices, "difficulty_only"

    return machine_info.index.tolist(), "all"

def get_fallback_message(mode, attack_category, difficulty):
    if mode == "exact":
        return None, "Exact Match", None
    elif mode == "category_only":
        return (
            f"No {difficulty} machines found for '{attack_category}'. Showing all '{attack_category}' machines.",
            "Category Match",
            f"Exact difficulty match not available — showing all difficulty levels for '{attack_category}'."
        )
    elif mode == "difficulty_only":
        return (
            f"Very few '{attack_category}' machines exist. Showing best '{difficulty}' machines from related categories.",
            "Difficulty Match",
            f"'{attack_category}' has insufficient machines — showing '{difficulty}' machines from broader categories."
        )
    else:
        return (
            "Very limited machines found. Showing best overall matches.",
            "Broad Match",
            "Dataset has very few machines matching your preferences."
        )

# ── SIMILARITY ──

def masked_cosine_similarity(student_vector, machine_matrix):
    # Only compare on features student actually specified
    # Ignores zero features so sparse vectors give meaningful scores
    student_array = student_vector.values[0]
    active_mask = student_array != 0
    if active_mask.sum() == 0:
        active_mask = np.ones(len(active_mask), dtype=bool)
    student_active = student_array[active_mask].reshape(1, -1)
    machines_active = machine_matrix.values[:, active_mask]
    return cos_sim(student_active, machines_active)[0]

# ── STUDENT VECTOR ──────

def build_student_vector_expanded(
    X, expansion_map,
    difficulty,
    attack_category,
    os_pref,
    vuln_type=None,
    learning_objectives=None,
    skills=None,
    entry_point=None,
    platform=None,
    expansion_weight=0.5
):
    student_vector = pd.DataFrame(
        np.zeros((1, X.shape[1])),
        columns=X.columns
    )

    # Required inputs — weight 1.0
    diff_map = {'Easy': 0.0, 'Medium': 0.5, 'Hard': 1.0}
    if 'implicit_difficulty' in student_vector.columns:
        student_vector['implicit_difficulty'] = diff_map.get(difficulty, 0.5)

    attack_col = f"attack_{attack_category}"
    if attack_col in student_vector.columns:
        student_vector[attack_col] = 1.0

    os_col = f"os_{os_pref}"
    if os_col in student_vector.columns:
        student_vector[os_col] = 1.0

    # Optional inputs — weight 1.0 if provided
    if vuln_type:
        vuln_col = f"vuln__{vuln_type}"
        if vuln_col in student_vector.columns:
            student_vector[vuln_col] = 1.0

    if learning_objectives:
        for obj in learning_objectives:
            obj_col = f"obj__{obj}"
            if obj_col in student_vector.columns:
                student_vector[obj_col] = 1.0

    if skills:
        for skill in skills:
            skill_col = f"skill__{skill}"
            if skill_col in student_vector.columns:
                student_vector[skill_col] = 1.0

    if entry_point:
        entry_col = f"entry_{entry_point}"
        if entry_col in student_vector.columns:
            student_vector[entry_col] = 1.0

    if platform:
        plat_map = {'VulnHub': 0.0, 'HackTheBox': 1.0}
        if 'Platform_ID' in student_vector.columns:
            student_vector['Platform_ID'] = plat_map.get(platform, 0.0)

    # Expanded inputs — weight 0.5 (soft enrichment from dataset)
    if vuln_type:
        for key, prefix in [
            (f'vuln_skills_{vuln_type}', 'skill__'),
            (f'vuln_objs_{vuln_type}', 'obj__')
        ]:
            if key in expansion_map:
                for item in expansion_map[key]:
                    col = f"{prefix}{item}"
                    if col in student_vector.columns and student_vector[col].values[0] == 0:
                        student_vector[col] = expansion_weight

    for key, prefix in [
        (f'cat_skills_{attack_category}', 'skill__'),
        (f'cat_objs_{attack_category}', 'obj__')
    ]:
        if key in expansion_map:
            for item in expansion_map[key]:
                col = f"{prefix}{item}"
                if col in student_vector.columns and student_vector[col].values[0] == 0:
                    student_vector[col] = expansion_weight

    return student_vector

# ── MAIN RECOMMEND FUNCTION ────

def recommend(
    models, expansion_map,
    difficulty,
    attack_category,
    os_pref,
    vuln_type=None,
    learning_objectives=None,
    skills=None,
    entry_point=None,
    platform=None,
    n_recommendations=5
):
    X               = models['X']
    machine_info    = models['machine_info']
    rf_best         = models['rf_best']
    feature_weights = models['feature_weights']

    # Build expanded student vector
    student_vector = build_student_vector_expanded(
        X, expansion_map,
        difficulty, attack_category, os_pref,
        vuln_type, learning_objectives,
        skills, entry_point, platform
    )

    # Get available machines with fallback
    available_indices, mode = get_available_machines_with_fallback(
        machine_info, attack_category, difficulty
    )
    fallback_msg, match_mode, reason = get_fallback_message(
        mode, attack_category, difficulty
    )

    # Prefer related categories in difficulty_only fallback
    if mode == "difficulty_only":
        related_categories = {
            'Binary Exploitation':          ['Web Exploitation', 'Network Exploitation'],
            'Cryptographic Exploitation':   ['Web Exploitation', 'Mixed (Web + Network)'],
            'Credential-Based Exploitation':['Web Exploitation', 'Network Exploitation'],
            'Mixed (Web + Network)':        ['Web Exploitation', 'Network Exploitation'],
        }
        if attack_category in related_categories:
            related = related_categories[attack_category]
            related_indices = []
            for rel_cat in related:
                rel_mask = (machine_info['Attack_Category'] == rel_cat) & \
                           (machine_info['Difficulty'] == difficulty)
                related_indices.extend(machine_info[rel_mask].index.tolist())
            if len(related_indices) >= 5:
                available_indices = related_indices
                reason = (
                    f"'{attack_category}' has very few machines. "
                    f"Showing '{difficulty}' machines from related categories: {', '.join(related)}."
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

    # Compute similarity
    X_available = X.iloc[available_indices]
    student_vector_weighted  = student_vector * feature_weights
    X_available_weighted     = X_available * feature_weights
    similarities = masked_cosine_similarity(
        student_vector_weighted, X_available_weighted
    )

    # Confidence label
    active_features_count = (student_vector.values[0] != 0).sum()
    confidence_label, confidence_msg = get_confidence_label(active_features_count)

    # Build results
    top_local_indices  = similarities.argsort()[::-1][:20]
    top_global_indices = [available_indices[i] for i in top_local_indices]

    results = []
    for local_idx, global_idx in zip(top_local_indices, top_global_indices):
        machine    = machine_info.iloc[global_idx]
        similarity = similarities[local_idx]
        rf_pred    = rf_best.predict(X.iloc[global_idx:global_idx+1])[0]
        rf_label   = {1: 'Easy', 2: 'Medium', 3: 'Hard'}[rf_pred]

        warnings = []
        if machine['Difficulty'] != difficulty:
            warnings.append(f"Difficulty mismatch: wanted {difficulty}, got {machine['Difficulty']}")
        if machine['Attack_Category'] != attack_category:
            warnings.append(f"Category mismatch: wanted {attack_category}, got {machine['Attack_Category']}")

        results.append({
            'rank':                    0,
            'machine_name':            machine['Machine_Name'],
            'platform':                machine['Platform'],
            'os':                      machine['OS'],
            'difficulty':              machine['Difficulty'],
            'rf_predicted_difficulty': rf_label,
            'attack_category':         machine['Attack_Category'],
            'entry_point':             machine['Entry_Point'],
            'estimated_time':          machine['Estimated_Time'],
            'similarity_score':        round(float(similarity) * 100, 2),
            'warnings':                warnings
        })

    # Sort and rank
    results = sorted(results, key=lambda x: x['similarity_score'], reverse=True)
    for i, r in enumerate(results[:n_recommendations]):
        r['rank'] = i + 1

    return (
        results[:n_recommendations],
        fallback_msg,
        match_mode,
        reason,
        confidence_label,
        confidence_msg
    )