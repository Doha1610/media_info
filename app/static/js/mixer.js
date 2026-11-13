// app/static/js/mixer.js

async function mixAudio() {
  const audioFile = document.getElementById('audio-file').files[0];
  const musicFile = document.getElementById('music-file').files[0];
  const position  = document.querySelector('input[name="position"]:checked').value;

  if (!audioFile || !musicFile) {
    alert("Vui lòng chọn đủ 2 file!");
    return;
  }

  clearLog('mix-log');
  document.getElementById('mix-result').classList.add('hidden');
  showLog('mix-log', `🎵 Đang ghép nhạc vào ${position.toLowerCase()}...`);

  const btn = document.querySelector('#tab-mixer .btn');
  btn.disabled = true;

  const formData = new FormData();
  formData.append('audio', audioFile);
  formData.append('music', musicFile);
  formData.append('position', position);

  try {
    const res = await fetch('/api/mix', { method: 'POST', body: formData });
    const data = await res.json();

    if (data.error) {
      showLog('mix-log', "❌ " + data.error);
      btn.disabled = false;
      return;
    }

    pollJob(data.job_id, 'mix-log', (job) => {
      if (job.ok && job.result) {
        showLog('mix-log', "✅ Ghép thành công!");
        const box = document.getElementById('mix-result');
        box.classList.remove('hidden');
        box.innerHTML = `
          <div>✅ File đã sẵn sàng:</div>
          <div style="margin-top:8px;">
            <a href="/api/download-result/${encodeURIComponent(job.result)}">
              ⬇ Tải xuống: ${job.result}
            </a>
          </div>
        `;
        refreshFileLists();
      } else {
        showLog('mix-log', "❌ Ghép thất bại. Kiểm tra FFmpeg đã cài chưa.");
      }
      btn.disabled = false;
    });
  } catch (e) {
    showLog('mix-log', "❌ " + e.message);
    btn.disabled = false;
  }
}