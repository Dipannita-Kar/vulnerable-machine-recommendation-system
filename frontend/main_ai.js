// js for the ai recommend page

const API_URL = 'http://127.0.0.1:5000';

// limit attack category to 2 picks
document.addEventListener('DOMContentLoaded', () => {
  setupCheckboxLimit('ai_attack_category', 'aiAttackCounter', 2);
  setupCheckboxLimit('aiLearningObjectives', 'aiObjectivesCounter', 3, 'aiLearningObjectivesGeneral');
  setupCheckboxLimit('aiLearningObjectivesGeneral', 'aiObjectivesCounter', 3, 'aiLearningObjectives');
  updateSelectionSummary();
  
  // update summary when inputs change
  document.querySelectorAll('#aiRecommendForm input, #aiRecommendForm select').forEach(el => {
    el.addEventListener('change', updateSelectionSummary);
  });
});

function setupCheckboxLimit(containerId, counterId, max, sharedContainerId=null) {
  const box = document.getElementById(containerId);
  if (!box) return;
  
  box.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => {
      const checked1 = box.querySelectorAll('input:checked').length;
      const checked2 = sharedContainerId ? document.getElementById(sharedContainerId).querySelectorAll('input:checked').length : 0;
      const total = checked1 + checked2;
      
      if (total > max) {
        cb.checked = false;
        return;
      }
      
      const counter = document.getElementById(counterId);
      if (counter) counter.textContent = `${total}/${max} selected`;
    });
  });
}

function updateSelectionSummary() {
  const summary = document.getElementById('aiSelectionSummary');
  if (!summary) return;
  
  const diff = document.getElementById('ai_difficulty').value;
  const os = document.getElementById('ai_os_pref').value;
  const cats = [...document.querySelectorAll('#ai_attack_category input:checked')].map(c => c.value);
  const objs = [
    ...document.querySelectorAll('#aiLearningObjectives input:checked'),
    ...document.querySelectorAll('#aiLearningObjectivesGeneral input:checked')
  ].map(c => c.value);
  const time = document.getElementById('ai_estimated_time').value;
  
  const hasAny = diff || os || cats.length || objs.length || time;
  
  if (!hasAny) {
    summary.innerHTML = `
      <h3 class="sidebar-title">Your Selections</h3>
      <p class="text-muted" style="font-size:0.82rem;">
        Your selections will appear here as you fill the form.
      </p>
    `;
    return;
  }
  
  let html = '<h3 class="sidebar-title">Your Selections</h3><div class="pref-tags">';
  if (diff) html += `<span class="pref-tag pref-required">Difficulty: ${diff}</span>`;
  if (os) html += `<span class="pref-tag pref-required">OS: ${os}</span>`;
  if (cats.length) html += `<span class="pref-tag pref-required">Category: ${cats.join(', ')}</span>`;
  if (objs.length) html += `<span class="pref-tag pref-required">Objectives: ${objs.join(', ')}</span>`;
  if (time) html += `<span class="pref-tag pref-optional">Time: ${time}</span>`;
  html += '</div>';
  summary.innerHTML = html;
}

// main submit
async function getAIRecommendations() {
  const difficulty = document.getElementById('ai_difficulty').value;
  const os_pref = document.getElementById('ai_os_pref').value;
  const attack_categories = [...document.querySelectorAll('#ai_attack_category input:checked')].map(c => c.value);
  const learning_objectives = [
    ...document.querySelectorAll('#aiLearningObjectives input:checked'),
    ...document.querySelectorAll('#aiLearningObjectivesGeneral input:checked')
  ].map(c => c.value);
  const estimated_time = document.getElementById('ai_estimated_time').value || null;
  const n_recommendations = parseInt(document.getElementById('ai_n_recommendations').value) || 5;
  
  const errBox = document.getElementById('aiErrorMsg');
  errBox.classList.add('hidden');
  
  // validation
  if (!difficulty || !os_pref || attack_categories.length === 0) {
    errBox.textContent = 'Please fill all required fields: Difficulty, OS, and at least one Attack Category.';
    errBox.classList.remove('hidden');
    return;
  }
  if (learning_objectives.length === 0) {
    errBox.textContent = 'Please select at least one Learning Objective (pick 1 to 3).';
    errBox.classList.remove('hidden');
    return;
  }
  
  const payload = {
    difficulty,
    attack_categories,
    os_pref,
    learning_objectives,
    estimated_time,
    n_recommendations
  };
  
  const btn = document.getElementById('aiSubmitBtn');
  btn.disabled = true;
  btn.textContent = 'Loading...';
  
  try {
    const res = await fetch(`${API_URL}/recommend-ai`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Request failed');
    }
    
    const data = await res.json();
    
    // store both result and input so the results page can use them
    sessionStorage.setItem('cyberpath_ai_results', JSON.stringify(data));
    sessionStorage.setItem('cyberpath_ai_input', JSON.stringify(payload));
    
    window.location.href = 'results_ai.html';
  } catch (e) {
    errBox.textContent = 'Error: ' + e.message;
    errBox.classList.remove('hidden');
    btn.disabled = false;
    btn.textContent = 'Get AI Recommendations';
  }
}

function resetAIForm() {
  document.querySelectorAll('#aiRecommendForm input, #aiRecommendForm select').forEach(el => {
    if (el.type === 'checkbox') el.checked = false;
    else el.value = '';
  });
  document.getElementById('ai_n_recommendations').value = 5;
  document.getElementById('aiAttackCounter').textContent = '0/2 selected';
  document.getElementById('aiObjectivesCounter').textContent = '0/3 selected';
  document.getElementById('aiErrorMsg').classList.add('hidden');
  updateSelectionSummary();
}