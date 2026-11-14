# 🎬 Media Tool - Tải Nhạc & Tạo Video Tự Động

**Media Tool** là một ứng dụng web mạnh mẽ được xây dựng bằng Python (Flask) kết hợp với FFmpeg và yt-dlp. Công cụ này giúp bạn tự động hóa việc tải nhạc từ YouTube/Facebook, ghép nhạc, và đặc biệt là tạo video từ ảnh tĩnh kèm theo nhạc nền và sticker (sóng nhạc) vô cùng ấn tượng.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Tính năng nổi bật

- **⬇️ Tải Nhạc (MP3):** Tải âm thanh chất lượng cao từ YouTube/Facebook. Tự động trích xuất MP3 và xóa file video gốc để tiết kiệm dung lượng.
- **🎵 Chèn Nhạc:** Ghép thêm một đoạn nhạc (intro/outro) vào đầu hoặc cuối file âm thanh hiện có.
- **🖼 Ảnh → Video:** Tạo video MP4 từ một bức ảnh tĩnh và file âm thanh.
- **🪄 Sticker Động:** Tự động xóa phông xanh (chroma key) và chèn sticker (như sóng nhạc) lặp vô hạn lên video.
- **🎯 Tùy chỉnh linh hoạt:** Chọn kích thước, vị trí (Trái/Giữa/Phải) và độ cao của sticker.
- **📁 Quản lý file:** Xem và tải xuống trực tiếp các file đã xử lý ngay trên giao diện web.
- **🌙 Giao diện hiện đại:** Thiết kế Dark Mode, responsive, thao tác mượt mà không cần tải lại trang.

---

## 📂 Cấu trúc thư mục

```text
media_tool/
│
├── app/                        # Thư mục chứa mã nguồn chính
│   ├── __init__.py             # Khởi tạo Flask app
│   ├── config.py               # Cấu hình đường dẫn, biến môi trường
│   ├── routes.py               # API endpoints
│   │
│   ├── core/                   # Xử lý logic chính (Backend)
│   │   ├── downloader.py       # Xử lý tải nhạc bằng yt-dlp
│   │   ├── audio_mixer.py      # Xử lý ghép nhạc bằng FFmpeg
│   │   └── image_to_video.py   # Xử lý tạo video, xóa phông, chèn sticker
│   │
│   └── static/                 # Giao diện Frontend
│       ├── index.html          # Giao diện chính
│       ├── css/style.css       # CSS Dark Mode
│       └── js/                 # Logic giao diện (AJAX)
│
├── downloads/                  # Nơi lưu file nhạc tải về
├── outputs/                    # Nơi lưu video/nhạc sau khi xử lý
├── stickers/                   # Thư viện chứa video/ảnh sticker (nền xanh)
├── temp/                       # File tạm trong quá trình render
│
├── .gitignore                  # Bỏ qua các file rác, file tải về
├── remove_green.py             # Script phụ trợ tách nền xanh sticker
├── requirements.txt            # Các thư viện Python cần thiết
├── run.py                      # File khởi chạy server
└── README.md                   # Tài liệu hướng dẫn
```
🚀 Hướng dẫn cài đặt
1. Yêu cầu hệ thống
Python 3.10 trở lên.

FFmpeg (Bắt buộc phải cài đặt để xử lý âm thanh và video).

2. Cài đặt FFmpeg
Windows: Tải bản build sẵn tại gyan.dev, giải nén và thêm thư mục bin vào biến môi trường PATH của Windows.

macOS: brew install ffmpeg

Linux (Ubuntu/Debian): sudo apt install ffmpeg

3. Cài đặt các thư viện Python
Mở Terminal/CMD tại thư mục dự án và chạy:

bash
pip install -r requirements.txt
4. Cấu hình FFmpeg (Quan trọng)
Mở file app/config.py, tìm dòng FFMPEG_PATH và sửa lại đường dẫn trỏ tới file ffmpeg.exe trên máy bạn (nếu bạn không dùng biến môi trường PATH).

python
FFMPEG_PATH = r"D:\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe"
5. Cấu hình YouTube API (Để đăng video)
Truy cập Google Cloud Console, tạo dự án và bật YouTube Data API v3.

Tạo OAuth client ID (chọn loại Desktop app).

Tải file JSON về, đổi tên thành client_secret.json và để vào thư mục gốc dự án.

Chạy tool, bấm nút Đăng YT. Tool sẽ yêu cầu bạn đăng nhập Google để lấy quyền. Sau khi cấp quyền, file token.json sẽ tự động được tạo ra.

6. Khởi chạy ứng dụng
bash
python run.py
Trình duyệt sẽ tự động mở trang web tại địa chỉ: http://127.0.0.1:5000

🛠️ Hướng dẫn sử dụng
Tạo Video từ Ảnh và Sticker:
Chuyển sang tab 🖼 Ảnh → Video.

Tải lên Ảnh nền và File Audio của bạn.

Ở mục Chọn Sticker, chọn một file video/ảnh có sẵn trong thư mục stickers.

Chọn Kích thước và Vị trí (Trái/Giữa/Phải) cho sticker.

Bấm Tạo Video và đợi trong giây lát. Video sẽ xuất hiện ở khung kết quả để bạn tải về.

💡 Mẹo: Để sticker hiển thị đẹp nhất (không bị viền đen), hãy đảm bảo video sticker của bạn có phông nền màu xanh lá cây (Green Screen). Tool sẽ tự động dùng thuật toán chromakey để xóa phông và giữ lại hình ảnh.

Đăng Video lên YouTube:
Chuyển sang tab 📁 File.

Bên cạnh mỗi file video .mp4, bấm nút Đăng YT.

Một bảng nhập liệu hiện ra, cho phép bạn nhập Tiêu đề, Mô tả, chọn chế độ (Riêng tư/Công khai) và chọn ngày giờ đăng (nếu muốn hẹn giờ).

Bấm Bắt đầu Đăng và theo dõi tiến trình ngay trên màn hình.

