const API_BASE = '/api';
let currentRecordId = null;

// DOM Elements
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const predictBtn = document.getElementById('predict-btn');
const resultCard = document.getElementById('result-card');
const previewImage = document.getElementById('preview-image');
const resultsList = document.getElementById('results-list');
const feedbackSection = document.getElementById('feedback-section');
const correctBtn = document.getElementById('correct-btn');
const incorrectBtn = document.getElementById('incorrect-btn');
const correctionForm = document.getElementById('correction-form');
const classSelect = document.getElementById('class-select');
const customClassInput = document.getElementById('custom-class-input');
const submitFeedback = document.getElementById('submit-feedback');
const thankYou = document.getElementById('thank-you');
const historyList = document.getElementById('history-list');

// Initialize
if (uploadZone) {
  uploadZone.onclick = () => fileInput.click();
  fileInput.onchange = handleFileSelect;
  predictBtn.onclick = handlePredict;
  correctBtn.onclick = () => sendFeedback(true);
  incorrectBtn.onclick = () => {
    correctionForm.style.display = 'block';
    feedbackSection.querySelector('.feedback-options').style.display = 'none';
  };
  submitFeedback.onclick = () => {
    let finalClass = classSelect.value;
    if (finalClass === '其他(自行輸入)') {
      finalClass = customClassInput.value || '其他';
    }
    sendFeedback(false, finalClass);
  };

  classSelect.onchange = () => {
    if (classSelect.value === '其他(自行輸入)') {
      customClassInput.style.display = 'block';
      customClassInput.focus();
    } else {
      customClassInput.style.display = 'none';
    }
  };

  loadClasses();
}

async function loadClasses() {
  const res = await fetch(`${API_BASE}/classes`);
  const classes = await res.json();
  classes.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c;
    opt.textContent = c;
    classSelect.appendChild(opt);
  });

  // Add OOD and Other options
  const oodOpt = document.createElement('option');
  oodOpt.value = 'OOD';
  oodOpt.textContent = 'Out of Distribution';
  classSelect.appendChild(oodOpt);

  const otherOpt = document.createElement('option');
  otherOpt.value = '其他(自行輸入)';
  otherOpt.textContent = '其他(自行輸入)';
  classSelect.appendChild(otherOpt);
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    previewImage.src = e.target.result;
    previewImage.style.display = 'block';
    resultCard.style.display = 'block';

    // Reset UI to initial state for new image
    predictBtn.style.display = 'flex';
    predictBtn.textContent = '開始辨識';
    predictBtn.disabled = false;

    resultsList.innerHTML = '';
    feedbackSection.style.display = 'none';
    correctionForm.style.display = 'none';
    thankYou.style.display = 'none';
  };
  reader.readAsDataURL(file);
}

async function handlePredict() {
  const file = fileInput.files[0];
  if (!file) return;

  predictBtn.disabled = true;
  predictBtn.textContent = '上傳中...';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const data = await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      let dotInterval;

      // Track upload progress
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          console.log(`e.loaded: ${e.loaded}, e.total: ${e.total}`)
          const percent = Math.round((e.loaded / e.total) * 100);
          if (percent < 100) {
            predictBtn.textContent = `上傳中 (${percent}%)...`;
          } else {
            predictBtn.textContent = '圖片處理中...';
          }
        }
      };

      // Fired when the upload is physically complete
      xhr.upload.onload = () => {
        let count = 0;
        predictBtn.textContent = '模型辨識中';
        dotInterval = setInterval(() => {
          count = (count + 1) % 4;
          predictBtn.textContent = '模型辨識中' + '.'.repeat(count);
        }, 500);
      };

      xhr.onload = () => {
        if (dotInterval) clearInterval(dotInterval);
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.response));
        } else {
          try {
            const errData = JSON.parse(xhr.response);
            reject(new Error(errData.detail || '辨識失敗'));
          } catch {
            reject(new Error('伺服器錯誤'));
          }
        }
      };

      xhr.onerror = () => {
        if (dotInterval) clearInterval(dotInterval);
        reject(new Error('網路連線失敗'));
      };

      xhr.open('POST', `${API_BASE}/predict`);
      xhr.send(formData);
    });

    currentRecordId = data.id;
    displayResults(data.predictions);
    feedbackSection.style.display = 'block';
    feedbackSection.querySelector('.feedback-options').style.display = 'flex';
  } catch (err) {
    alert(err.message);
  } finally {
    predictBtn.disabled = false;
    predictBtn.textContent = '重新辨識';
  }
}

function displayResults(predictions) {
  resultsList.innerHTML = '';
  predictions.forEach((p, i) => {
    const div = document.createElement('div');
    div.className = 'result-item';
    div.innerHTML = `
      <div style="flex: 1;">
        <div style="display: flex; justify-content: space-between;">
          <span style="font-weight: 600;">${p.class}</span>
          <span style="color: var(--text-muted);">${(p.probability * 100).toFixed(2)}%</span>
        </div>
        <div class="probability-bar">
          <div class="probability-fill" style="width: ${p.probability * 100}%; background: ${i === 0 ? 'var(--accent)' : 'var(--primary)'}"></div>
        </div>
      </div>
    `;
    resultsList.appendChild(div);
  });
}

async function sendFeedback(isCorrect, correctedClass = null) {
  const formData = new FormData();
  formData.append('id', currentRecordId);
  formData.append('is_correct', isCorrect);
  if (correctedClass) formData.append('corrected_class', correctedClass);

  try {
    await fetch(`${API_BASE}/feedback`, {
      method: 'POST',
      body: formData
    });
    feedbackSection.querySelector('.feedback-options').style.display = 'none';
    correctionForm.style.display = 'none';
    thankYou.style.display = 'block';
  } catch (err) {
    alert('提交失敗');
  }
}

// Admin Logic
async function loadHistory() {
  if (!historyList) return;

  const res = await fetch(`${API_BASE}/history`);
  const history = await res.json();

  historyList.innerHTML = history.map(item => {
    // Fallback for legacy records
    const thumbPath = (item.thumbnail_path || item.image_path).replace('server_data/', '/server_data/');
    const origPath = (item.original_path || item.image_path).replace('server_data/', '/server_data/');
    console.log(thumbPath);
    console.log(origPath);

    return `
    <div class="history-item animate">
      <img src="${thumbPath}" class="history-img" alt="縮圖">
      <div class="history-info">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <div>
            <h3 style="margin-bottom: 0.25rem;">${item.pred1_class}</h3>
            <p style="font-size: 0.875rem; color: var(--text-muted);">${item.timestamp}</p>
          </div>
          <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem;">
            <span class="status-badge ${getStatusClass(item.is_correct)}">
              ${getStatusText(item.is_correct)}
            </span>
            <a href="${origPath}" target="_blank" class="view-original-link">查看原圖</a>
          </div>
        </div>
        <div style="margin-top: 1rem; font-size: 0.875rem;">
          <div style="display: flex; gap: 0.5rem; color: var(--text-muted);">
            <span>Top 2: ${item.pred2_class} (${(item.pred2_prob * 100).toFixed(1)}%)</span>
            <span>|</span>
            <span>Top 3: ${item.pred3_class} (${(item.pred3_prob * 100).toFixed(1)}%)</span>
          </div>
          ${item.is_correct === 0 ? `<div class="correction-badge">修正為：${item.corrected_class}</div>` : ''}
        </div>
      </div>
    </div>
    `;
  }).join('');
}

function getStatusClass(status) {
  if (status === 1) return 'status-correct';
  if (status === 0) return 'status-incorrect';
  return 'status-pending';
}

function getStatusText(status) {
  if (status === 1) return '正確';
  if (status === 0) return '不正確';
  return '未核實';
}
