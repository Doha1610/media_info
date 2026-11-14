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
  if (!el) return;
  el.textContent += msg + "\n";
  el.scrollTop = el.scrollHeight;
}

function clearLog(elId) {
  const el = document.getElementById(elId);
  if (el) el.textContent = "";
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
    let nameHtml = downloadable
      ? `<a href="/api/download-result/${encodeURIComponent(f.name)}">${f.name}</a>`
      : `<span>${f.name}</span>`;
      
    // Nếu là file video mp4 ở tab outputs, hiện thêm nút Đăng YouTube
    let uploadBtn = "";
    if (elId === 'list-outputs' && f.name.endsWith('.mp4')) {
        uploadBtn = `<button class="btn primary" style="padding: 4px 8px; font-size: 11px; margin-left: 10px; cursor: pointer;" onclick="openYoutubeModal('${f.name}')">Đăng YT</button>`;
    }

    return `<li style="display: flex; justify-content: space-between; align-items: center;">
              <div style="flex: 1; word-break: break-all;">${nameHtml} <span class="size">(${formatSize(f.size)})</span></div> 
              <div>${uploadBtn}</div>
            </li>`;
  }).join('');
}

// ==========================================
// XỬ LÝ FORM ĐĂNG YOUTUBE (MODAL)
// ==========================================

let currentYtFilename = "";

function openYoutubeModal(filename) {
  currentYtFilename = filename;
  
  // Reset form
  document.getElementById('yt-title').value = filename.replace(".mp4", "");
  document.getElementById('yt-desc').value = "";
  document.getElementById('yt-schedule').value = "";
  document.getElementById('yt-privacy').value = "private";
  document.getElementById('yt-log').textContent = "";
  document.getElementById('btn-submit-yt').disabled = false;
  
  // Hiển thị form và cập nhật trạng thái ô chọn ngày giờ
  document.getElementById('yt-modal').style.display = 'block';
  toggleSchedule();
}

function toggleSchedule() {
  const privacy = document.getElementById('yt-privacy').value;
  const scheduleGroup = document.getElementById('yt-schedule-group');
  if (privacy === 'private') {
    scheduleGroup.style.display = 'block';
  } else {
    scheduleGroup.style.display = 'none';
  }
}

async function submitYoutube() {
  const title = document.getElementById('yt-title').value;
  const desc = document.getElementById('yt-desc').value;
  const privacy = document.getElementById('yt-privacy').value;
  const scheduleInput = document.getElementById('yt-schedule').value; 
  
  let scheduleFormatted = null;
  // Nếu có chọn ngày giờ và chế độ là private
  if (scheduleInput && privacy === 'private') {
    // scheduleInput có dạng "2026-11-20T20:00". Ta cần thêm :00+07:00
    scheduleFormatted = scheduleInput + ":00+07:00"; 
  }

  const btn = document.getElementById('btn-submit-yt');
  btn.disabled = true;
  clearLog('yt-log');
  showLog('yt-log', "⏳ Đang gửi yêu cầu lên server...");
  showLog('yt-log', "⚠️ Nếu đây là lần đầu, hãy nhìn xuống cửa sổ Terminal (đen) để copy link đăng nhập!");

  try {
    const res = await fetch('/api/youtube-upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        filename: currentYtFilename, 
        title: title, 
        description: desc, 
        privacy: privacy,
        schedule_time: scheduleFormatted
      })
    });
    const data = await res.json();
    
    if (data.error) {
      showLog('yt-log', "❌ Lỗi: " + data.error);
      btn.disabled = false;
    } else {
      // Bắt đầu theo dõi tiến trình
      pollJob(data.job_id, 'yt-log', (job) => {
        if (job.ok) {
          showLog('yt-log', "✅ Đăng thành công! Video ID: " + job.video_id);
          refreshFileLists();
        } else {
          showLog('yt-log', "❌ Đăng thất bại.");
          btn.disabled = false;
        }
      });
    }
  } catch (e) {
    showLog('yt-log', "❌ Lỗi kết nối: " + e.message);
    btn.disabled = false;
  }
}

// --- Hàm Đổi Tài Khoản Google (Xóa token) ---
async function resetYoutubeToken() {
  if (confirm("Bạn có chắc muốn đăng xuất tài khoản Google hiện tại? Lần đăng tiếp theo bạn sẽ phải đăng nhập lại.")) {
    try {
      const res = await fetch('/api/youtube-reset-token', { method: 'POST' });
      const data = await res.json();
      if (data.ok) {
        alert("Đã đăng xuất tài khoản cũ! Hãy bấm Đăng Video để đăng nhập tài khoản mới.");
      } else {
        alert("Thông báo: " + data.message);
      }
    } catch (e) {
      alert("Lỗi khi đăng xuất: " + e.message);
    }
  }
}

// Load lần đầu
refreshFileLists();