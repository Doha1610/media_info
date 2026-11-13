// app/static/js/image_video.js

// Tự động load danh sách sticker khi web vừa tải xong
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const res = await fetch('/api/stickers');
    const stickers = await res.json();
    const select = document.getElementById('sticker-select');
    
    // Xóa các option cũ (đề phòng bị load 2 lần)
    select.innerHTML = '<option value="">-- Không dùng sticker --</option>';

    // Thêm danh sách sticker vào menu
    stickers.forEach(name => {
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = name;
      select.appendChild(opt);
    });
  } catch (e) {
    console.error("Không thể tải danh sách sticker:", e);
  }
});

async function imageToVideo() {
  const imageFile = document.getElementById('image-file').files[0];
  const audioFile = document.getElementById('image-audio-file').files[0];
  const stickerName = document.getElementById('sticker-select').value; 
  const resolution = document.getElementById('image-resolution').value;
  const fps        = document.getElementById('image-fps').value;
  
  // Lấy thông số kích thước và vị trí từ menu mới
  const stickerSize = document.getElementById('sticker-size').value;
  const stickerPos  = document.getElementById('sticker-position').value;

  if (!imageFile || !audioFile) {
    alert("Vui lòng chọn đủ Ảnh nền và Audio!");
    return;
  }

  clearLog('image-log');
  document.getElementById('image-result').classList.add('hidden');
  showLog('image-log', `🎬 Đang tạo video ${resolution} @ ${fps}fps...`);
  showLog('image-log', `🖼 Ảnh: ${imageFile.name}`);
  showLog('image-log', `🎵 Audio: ${audioFile.name}`);
  
  if (stickerName) {
    showLog('image-log', `🪄 Sẽ dán sticker: ${stickerName} (Size: ${stickerSize}px, Vị trí: ${stickerPos})`);
  }

  const btn = document.querySelector('#tab-image .btn');
  btn.disabled = true;

  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('audio', audioFile);
  
  if (stickerName) {
    formData.append('sticker_name', stickerName);
    formData.append('sticker_size', stickerSize); // Gửi kích thước
    formData.append('sticker_pos', stickerPos);   // Gửi vị trí
  }
  
  formData.append('resolution', resolution);
  formData.append('fps', fps);

  try {
    const res = await fetch('/api/image-to-video', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    if (data.error) {
      showLog('image-log', "❌ " + data.error);
      btn.disabled = false;
      return;
    }

    pollJob(data.job_id, 'image-log', (job) => {
      if (job.ok && job.result) {
        showLog('image-log', "✅ Tạo video thành công!");
        const box = document.getElementById('image-result');
        box.classList.remove('hidden');
        box.innerHTML = `
          <div>✅ Video đã sẵn sàng:</div>
          <div style="margin-top:8px;">
            <a href="/api/download-result/${encodeURIComponent(job.result)}">
              ⬇ Tải xuống: ${job.result}
            </a>
          </div>
        `;
        refreshFileLists();
      } else {
        showLog('image-log', "❌ Tạo video thất bại. Kiểm tra log để biết chi tiết.");
      }
      btn.disabled = false;
    });
  } catch (e) {
    showLog('image-log', "❌ Lỗi kết nối: " + e.message);
    btn.disabled = false;
  }
}