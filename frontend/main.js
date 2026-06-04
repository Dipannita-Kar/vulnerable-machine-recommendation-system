const API_URL = 'http://127.0.0.1:5000';

// ─GET CHECKED VALUES 

function getCheckedValues(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];
    const checked = container.querySelectorAll('input[type="checkbox"]:checked');
    return Array.from(checked).map(cb => cb.value);
}

// MAX SELECTION — SINGLE CONTAINER 

function enforceMaxSelection(containerId, max, counterId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            const checked = container.querySelectorAll('input[type="checkbox"]:checked');
            const counter = document.getElementById(counterId);
            if (counter) {
                counter.textContent = `${checked.length}/${max} selected`;
                counter.className = checked.length === max ? 'selection-counter full' : 'selection-counter';
            }
            if (checked.length >= max) {
                checkboxes.forEach(other => { if (!other.checked) other.disabled = true; });
            } else {
                checkboxes.forEach(other => { other.disabled = false; });
            }
            updateSidebar();
        });
    });
}

//  MAX SELECTION — MULTIPLE CONTAINERS COMBINED 

function enforceMaxSelectionCombined(containerIds, max, counterId) {
    const getAllCheckboxes = () => {
        let all = [];
        containerIds.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                all = all.concat(Array.from(container.querySelectorAll('input[type="checkbox"]')));
            }
        });
        return all;
    };

    const getAllChecked = () => getAllCheckboxes().filter(cb => cb.checked);

    getAllCheckboxes().forEach(cb => {
        cb.addEventListener('change', function() {
            const checked = getAllChecked();
            const counter = document.getElementById(counterId);
            if (counter) {
                counter.textContent = `${checked.length}/${max} selected`;
                counter.className = checked.length === max ? 'selection-counter full' : 'selection-counter';
            }
            if (checked.length >= max) {
                getAllCheckboxes().forEach(other => { if (!other.checked) other.disabled = true; });
            } else {
                getAllCheckboxes().forEach(other => { other.disabled = false; });
            }
            updateSidebar();
        });
    });
}

// SIDEBAR SUMMARY

function updateSidebar() {
    const sidebar = document.getElementById('selectionSummary');
    if (!sidebar) return;

    const difficulty  = document.getElementById('difficulty')?.value || '';
    const os_pref     = document.getElementById('os_pref')?.value || '';
    const attack_cats = getCheckedValues('attack_category');
    const objectives  = [
        ...getCheckedValues('learningObjectives'),
        ...getCheckedValues('learningObjectivesGeneral')
    ];
    const vuln_type   = document.getElementById('vuln_type')?.value || '';
    const est_time    = document.getElementById('estimated_time')?.value || '';
    const n_recs      = document.getElementById('n_recommendations')?.value || '5';

    let html = '<h3 class="sidebar-title">Your Selections</h3>';

    html += `<div class="sidebar-item ${difficulty ? 'selected' : 'empty'}">
        <span class="sidebar-label">Difficulty</span>
        <span class="sidebar-value">${difficulty || 'Not selected'}</span>
    </div>`;

    html += `<div class="sidebar-item ${os_pref ? 'selected' : 'empty'}">
        <span class="sidebar-label">Operating System</span>
        <span class="sidebar-value">${os_pref || 'Not selected'}</span>
    </div>`;

    html += `<div class="sidebar-item ${attack_cats.length > 0 ? 'selected' : 'empty'}">
        <span class="sidebar-label">Attack Category</span>
        <span class="sidebar-value">${attack_cats.length > 0 ? attack_cats.join(', ') : 'Not selected'}</span>
    </div>`;

    if (objectives.length > 0) {
        html += `<div class="sidebar-item selected">
            <span class="sidebar-label">Learning Objectives</span>
            <span class="sidebar-value">${objectives.join(', ')}</span>
        </div>`;
    }

    if (vuln_type) {
        html += `<div class="sidebar-item selected">
            <span class="sidebar-label">Vulnerability Type</span>
            <span class="sidebar-value">${vuln_type}</span>
        </div>`;
    }

    if (est_time) {
        html += `<div class="sidebar-item selected">
            <span class="sidebar-label">Estimated Time</span>
            <span class="sidebar-value">${est_time}</span>
        </div>`;
    }

    html += `<div class="sidebar-item selected">
        <span class="sidebar-label">Recommendations</span>
        <span class="sidebar-value">${n_recs}</span>
    </div>`;

    const allRequired = difficulty && os_pref && attack_cats.length > 0;
    html += `<div class="sidebar-ready ${allRequired ? 'ready' : 'not-ready'}">
        ${allRequired ? '✅ Ready to recommend' : '⚠️ Fill required fields'}
    </div>`;

    sidebar.innerHTML = html;
}

// GET RECOMMENDATIONS 

async function getRecommendations() {
    const difficulty  = document.getElementById('difficulty').value;
    const os_pref     = document.getElementById('os_pref').value;
    const attack_cats = getCheckedValues('attack_category');
    const n_recs      = parseInt(document.getElementById('n_recommendations').value) || 5;

    if (!difficulty) { showError('Please select a difficulty level.'); return; }
    if (!os_pref)    { showError('Please select an operating system.'); return; }
    if (attack_cats.length === 0) { showError('Please select at least one attack category.'); return; }

    const objectives = [
        ...getCheckedValues('learningObjectives'),
        ...getCheckedValues('learningObjectivesGeneral')
    ];
    const vuln_type = document.getElementById('vuln_type')?.value || null;
    const est_time  = document.getElementById('estimated_time')?.value || null;
    const platform  = document.getElementById('platform')?.value || null;

    hideError();
    setLoading(true);

    try {
        const response = await fetch(`${API_URL}/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                difficulty:          difficulty,
                attack_categories:   attack_cats,
                os_pref:             os_pref,
                vuln_type:           vuln_type || null,
                learning_objectives: objectives.length > 0 ? objectives : null,
                estimated_time:      est_time || null,
                platform:            platform || null,
                n_recommendations:   n_recs
            })
        });

        const data = await response.json();

        if (data.error) { showError(data.error); return; }

        sessionStorage.setItem('cyberpath_results', JSON.stringify(data));
        sessionStorage.setItem('cyberpath_input', JSON.stringify({
            difficulty,
            os_pref,
            attack_categories: attack_cats,
            vuln_type:         vuln_type || null,
            learning_objectives: objectives,
            estimated_time:    est_time || null,
            platform:          platform || 'VulnHub',
            n_recommendations: n_recs
        }));

        window.location.href = 'results.html';

    } catch (err) {
        showError('Could not connect to API. Make sure the Flask server is running on port 5000.');
    } finally {
        setLoading(false);
    }
}

// RESET FORM 

function resetForm() {
    ['difficulty', 'os_pref', 'vuln_type', 'estimated_time'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.checked  = false;
        cb.disabled = false;
    });

    document.querySelectorAll('.selection-counter').forEach(c => {
        const max = c.dataset.max || '3';
        c.textContent = `0/${max} selected`;
        c.className = 'selection-counter';
    });

    const nRecs = document.getElementById('n_recommendations');
    if (nRecs) nRecs.value = 5;

    hideError();
    updateSidebar();
}

// ── HELPERS ───

function showError(msg) {
    const el = document.getElementById('errorMsg');
    if (el) { el.textContent = msg; el.classList.remove('hidden'); }
}

function hideError() {
    const el = document.getElementById('errorMsg');
    if (el) el.classList.add('hidden');
}

function setLoading(loading) {
    const btn = document.getElementById('submitBtn');
    if (!btn) return;
    btn.disabled    = loading;
    btn.textContent = loading ? 'Finding machines...' : 'Get Recommendations';
}

// INIT

document.addEventListener('DOMContentLoaded', function() {
    enforceMaxSelectionCombined(
        ['learningObjectives', 'learningObjectivesGeneral'],
        3,
        'objectivesCounter'
    );
    enforceMaxSelection('attack_category', 2, 'attackCounter');

    ['difficulty', 'os_pref', 'vuln_type', 'estimated_time', 'n_recommendations'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', updateSidebar);
    });

    updateSidebar();
});