const API_URL = 'http://127.0.0.1:5000';

// Get checked values from a checkbox grid
function getCheckedValues(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];
    const checked = container.querySelectorAll('input[type="checkbox"]:checked');
    return Array.from(checked).map(cb => cb.value);
}

// Get recommendations from API
async function getRecommendations() {
    // Get required fields
    const difficulty     = document.getElementById('difficulty').value;
    const os_pref        = document.getElementById('os_pref').value;
    const attack_cats    = getCheckedValues('attack_category');
    const n_recs         = parseInt(document.getElementById('n_recommendations').value) || 5;

    // Validate required fields
    if (!difficulty) {
        showError('Please select a difficulty level.');
        return;
    }
    if (!os_pref) {
        showError('Please select an operating system.');
        return;
    }
    if (attack_cats.length === 0) {
        showError('Please select at least one attack category.');
        return;
    }

    // Get optional fields
    const vuln_types  = getCheckedValues('vuln_type');
    const objectives  = getCheckedValues('learningObjectives');
    const platform    = document.getElementById('platform').value || null;

    // Hide error, show loading
    hideError();
    setLoading(true);

    try {
        const response = await fetch(`${API_URL}/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                difficulty:          difficulty,
                attack_category:     attack_cats[0],
                os_pref:             os_pref,
                vuln_type:           vuln_types.length > 0 ? vuln_types[0] : null,
                learning_objectives: objectives.length > 0 ? objectives : null,
                platform:            platform,
                n_recommendations:   n_recs
            })
        });

        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        // Save results to sessionStorage and go to results page
        sessionStorage.setItem('cyberpath_results', JSON.stringify(data));
        sessionStorage.setItem('cyberpath_input', JSON.stringify({
            difficulty, os_pref,
            attack_category: attack_cats[0],
            vuln_type: vuln_types[0] || null,
            learning_objectives: objectives,
            platform: platform || 'All Platforms'
        }));

        window.location.href = 'results.html';

    } catch (err) {
        showError('Could not connect to API. Make sure the Flask server is running on port 5000.');
    } finally {
        setLoading(false);
    }
}

// Reset form
function resetForm() {
    document.getElementById('difficulty').value = '';
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
    document.getElementById('n_recommendations').value = 5;
    hideError();
}

// Show error message
function showError(msg) {
    const el = document.getElementById('errorMsg');
    if (el) {
        el.textContent = msg;
        el.classList.remove('hidden');
    }
}

// Hide error message
function hideError() {
    const el = document.getElementById('errorMsg');
    if (el) el.classList.add('hidden');
}

// Show/hide loading state on button
function setLoading(loading) {
    const btn = document.getElementById('submitBtn');
    if (!btn) return;
    if (loading) {
        btn.disabled = true;
        btn.textContent = 'Finding machines...';
    } else {
        btn.disabled = false;
        btn.textContent = 'Get Recommendations';
    }
}