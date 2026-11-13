// app/static/js/download.js

async function downloadMedia(mode) {
  const url = document.getElementById('url-input').value.trim();
  if (!url) {
    alert("Vui lòng nhập link video!");
    return;
  }

  clearLog('download-log');
  showLog('download-log', `🚀 Bắt đầu tải Nhạc (MP3)...`);
  showLog('download-log', `📎 URL: ${url}`);

  // Vô hiệu hóa nút trong khi đang tải để tránh click đúp
  document.querySelectorAll('#tab-download .btn').forEach(b => b.disabled = true);

  try {
    const res = await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, mode: 'audio' }) // Ép cứng luôn là tải audio
    });
    const data = await res.json();

    if (data.error) {
      showLog('download-log', "❌ " + data.error);
      document.querySelectorAll('#tab-download .btn').forEach(b => b.disabled = false);
      return;
    }

    // Theo dõi tiến trình tải qua job_id
    pollJob(data.job_id, 'download-log', (job) => {
      if (job.ok) {
        showLog('download-log', "✅ Tải nhạc thành công! Video gốc đã được tự động xóa.");
        refreshFileLists(); // Cập nhật lại danh sách file ở tab File
      } else {
        showLog('download-log', "❌ Tải thất bại. Hãy chắc chắn bạn đã cài đặt và cấu hình FFmpeg đúng cách.");
      }
      // Mở lại nút sau khi hoàn tất
      document.querySelectorAll('#tab-download .btn').forEach(b => b.disabled = false);
    });
  } catch (e) {
    showLog('download-log', "❌ Lỗi kết nối: " + e.message);
    document.querySelectorAll('#tab-download .btn').forEach(b => b.disabled = false);
  }
}