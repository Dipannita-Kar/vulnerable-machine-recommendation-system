# v2 ai recommender - pure ml scoring with xgboost
# returns top-n machines for a given student profile

import numpy as np
import pandas as pd
from model_loader_ai import (
    xgb_model, machine_features, machine_info,
    feature_columns, n_machines,
    diff_map, time_to_hours
)


def build_student_vector(difficulty, attack_categories, os_pref,
                         learning_objectives=None, estimated_time=None,
                         skill_level=None):
    # turn student form input into a vector matching the machine feature columns
    vec = pd.Series(0.0, index=feature_columns)
    
    vec['diff_num'] = diff_map.get(difficulty, 2)
    vec['Estimated_Time_Hours'] = time_to_hours.get(estimated_time, 2.5)
    
    # student doesnt input these so using defaults based on difficulty
    path_default = {'Easy': 4, 'Medium': 6, 'Hard': 9}
    chain_default = {'Easy': 3, 'Medium': 5, 'Hard': 7}
    vec['Attack_Path_Length'] = path_default.get(difficulty, 6)
    vec['kill_chain_count'] = chain_default.get(difficulty, 5)
    
    if isinstance(attack_categories, str):
        attack_categories = [attack_categories]
    for cat in attack_categories:
        col = 'cat_' + cat
        if col in vec.index:
            vec[col] = 1
    
    os_col = 'os_' + os_pref
    if os_col in vec.index:
        vec[os_col] = 1
    
    if learning_objectives:
        for obj in learning_objectives:
            col = 'obj_' + obj
            if col in vec.index:
                vec[col] = 1
    
    return vec


def get_match_label(top_score):
    # translate top score to quality label for the ui
    if top_score >= 0.80:
        return "Excellent matches found"
    elif top_score >= 0.50:
        return "Good matches found"
    elif top_score >= 0.30:
        return "Partial matches - your exact combination is rare"
    else:
        return "Your combination is very rare - showing closest available"


def get_per_machine_breakdown(student_inputs, machine_row):
    # show what matches and what doesnt for each recommended machine
    matched = []
    missing = []
    
    if student_inputs['difficulty'] == machine_row['Difficulty']:
        matched.append(f"Difficulty: {machine_row['Difficulty']}")
    else:
        missing.append(f"Difficulty: wanted {student_inputs['difficulty']}, got {machine_row['Difficulty']}")
    
    cats = student_inputs.get('categories', [])
    if isinstance(cats, str):
        cats = [cats]
    cat_match = (machine_row['Attack_Category'] in cats) or (
        machine_row['Attack_Category'] == 'Mixed (Web + Network)'
        and any(c in ['Web Exploitation', 'Network Exploitation'] for c in cats)
    )
    if cat_match:
        matched.append(f"Category: {machine_row['Attack_Category']}")
    else:
        missing.append(f"Category: wanted {cats}, got {machine_row['Attack_Category']}")
    
    if student_inputs['os'] == machine_row['OS']:
        matched.append(f"OS: {machine_row['OS']}")
    else:
        missing.append(f"OS: wanted {student_inputs['os']}, got {machine_row['OS']}")
    
    if student_inputs.get('objectives'):
        machine_objs = set(o.strip() for o in str(machine_row['Learning_Objectives']).split(';') if o.strip())
        for obj in student_inputs['objectives']:
            if obj in machine_objs:
                matched.append(f"Objective: {obj}")
            else:
                missing.append(f"Objective: {obj} not in this machine")
    
    if student_inputs.get('time'):
        if student_inputs['time'] == machine_row['Estimated_Time']:
            matched.append(f"Time: {machine_row['Estimated_Time']}")
        else:
            missing.append(f"Time: wanted {student_inputs['time']}, got {machine_row['Estimated_Time']}")
    
    return matched, missing


def recommend(difficulty, attack_categories, os_pref,
              learning_objectives=None, estimated_time=None,
              skill_level=None, n=5):
    # build the student vector
    svec = build_student_vector(
        difficulty, attack_categories, os_pref,
        learning_objectives, estimated_time, skill_level
    ).values
    
    # pair student with every machine and score
    student_block = np.tile(svec, (n_machines, 1))
    X_inf = np.hstack([student_block, machine_features.values])
    scores = xgb_model.predict(X_inf)
    
    # sort by score desc, break ties with shorter path first
    path_lengths = machine_info['Attack_Path_Length'].values
    order = np.lexsort((path_lengths, -scores))
    top_idx = order[:n]
    
    # build response
    student_inputs = {
        'difficulty': difficulty,
        'categories': attack_categories,
        'os': os_pref,
        'objectives': learning_objectives or [],
        'time': estimated_time,
        'skill': skill_level
    }
    
    top_score = float(scores[top_idx[0]])
    quality_label = get_match_label(top_score)
    
    recommendations = []
    for idx in top_idx:
        m = machine_info.iloc[idx]
        matched, missing = get_per_machine_breakdown(student_inputs, m)
        
        recommendations.append({
            'machine_id': str(m['Machine_ID']),
            'machine_name': m['Machine_Name'],
            'platform': m['Platform'],
            'difficulty': m['Difficulty'],
            'attack_category': m['Attack_Category'],
            'os': m['OS'],
            'estimated_time': m['Estimated_Time'],
            'attack_path_length': int(m['Attack_Path_Length']),
            'vulnerability_type': m['Vulnerability_Type'],
            'entry_point': m['Entry_Point'],
            'kill_chain_stages': m['Kill_Chain_Stages'],
            'skills_required': m['Skills_Required'],
            'learning_objectives': m['Learning_Objectives'],
            'predicted_relevance': round(float(scores[idx]), 3),
            'matched_features': matched,
            'missing_features': missing
        })
    
    return {
        'quality_label': quality_label,
        'top_score': round(top_score, 3),
        'student_inputs': student_inputs,
        'recommendations': recommendations,
        'model_used': 'XGBoost'
    }