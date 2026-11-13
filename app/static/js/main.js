// app/static/js/main.js

// --- Chuyển tab ---
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${tab}`).classList.add('active');

    if (tab === 'files') refreshFileLists();
  });
});

// --- Helpers ---
function showLog(elId, msg) {
  const el = document.getElementById(elId);
  el.textContent += msg + "\n";
  el.scrollTop = el.scrollHeight;
}

function clearLog(elId) {
  document.getElementById(elId).textContent = "";
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1024 / 1024).toFixed(1) + " MB";
}

// --- Polling job ---
async function pollJob(jobId, logElId, onDone) {
  let lastLen = 0;
  const timer = setInterval(async () => {
    try {
      const res = await fetch(`/api/log/${jobId}`);
      const data = await res.json();

      // In log mới
      if (data.log && data.log.length > lastLen) {
        const newLines = data.log.slice(lastLen);
        newLines.forEach(line => showLog(logElId, line));
        lastLen = data.log.length;
      }

      if (data.done) {
        clearInterval(timer);
        onDone(data);
      }
    } catch (e) {
      clearInterval(timer);
      showLog(logElId, "❌ Lỗi kết nối server: " + e.message);
    }
  }, 1000);
}

// --- File lists ---
async function refreshFileLists() {
  try {
    const [dls, outs] = await Promise.all([
      fetch('/api/files/downloads').then(r => r.json()),
      fetch('/api/files/outputs').then(r => r.json())
    ]);

    renderFileList('list-downloads', dls, false);
    renderFileList('list-outputs', outs, true);
  } catch (e) {
    console.error(e);
  }
}

function renderFileList(elId, files, downloadable) {
  const ul = document.getElementById(elId);
  if (!files.length) {
    ul.innerHTML = '<li style="color:#64748b;justify-content:center;">Chưa có file nào</li>';
    return;
  }
  ul.innerHTML = files.map(f => {
    const name = downloadable
      ? `<a href="/api/download-result/${encodeURIComponent(f.name)}">${f.name}</a>`
      : `<span>${f.name}</span>`;
    return `<li>${name} <span class="size">${formatSize(f.size)}</span></li>`;
  }).join('');
}

// Load lần đầu
refreshFileLists();