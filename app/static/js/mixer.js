// app/static/js/mixer.js

async function mixAudio() {
  const audioFile = document.getElementById('audio-file').files[0];
  // SỬ DỤNG .files ĐỂ LẤY TẤT CẢ CÁC FILE ĐÃ CHỌN (Mảng các file)
  const musicFiles = document.getElementById('music-file').files; 
  const position  = document.querySelector('input[name="position"]:checked').value;

  if (!audioFile || musicFiles.length === 0) {
    alert("Vui lòng chọn File Audio gốc và ít nhất 1 File nhạc chèn!");
    return;
  }

  clearLog('mix-log');
  document.getElementById('mix-result').classList.add('hidden');
  showLog('mix-log', `🎵 Đang ghép ${musicFiles.length} file nhạc vào ${position.toLowerCase()}...`);

  const btn = document.querySelector('#tab-mixer .btn');
  btn.disabled = true;

  const formData = new FormData();
  formData.append('audio', audioFile);
  
  // LẶP QUA TỪNG FILE NHẠC VÀ THÊM VÀO FORMDATA
  for (let i = 0; i < musicFiles.length; i++) {
    formData.append('music', musicFiles[i]);
  }
  
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