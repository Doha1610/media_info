# remove_green.py
import os
import subprocess
from app.config import STICKERS_DIR, FFMPEG_PATH

def _ffmpeg():
    if FFMPEG_PATH and os.path.exists(FFMPEG_PATH):
        return os.path.join(FFMPEG_PATH, "ffmpeg.exe")
    return "ffmpeg"

def tach_nen_xanh():
    print("=== CÔNG CỤ TÁCH NỀN XANH STICKER ===")
    if not os.path.exists(STICKERS_DIR):
        print("Không tìm thấy thư mục stickers!")
        return

    files = [f for f in os.listdir(STICKERS_DIR) if f.endswith(('.mp4', '.mov')) and not f.endswith('_trans.webm')]
    
    if not files:
        print("Không có video nào cần tách nền.")
        return

    for i, filename in enumerate(files):
        input_path = os.path.join(STICKERS_DIR, filename)
        output_filename = f"{os.path.splitext(filename)[0]}_trans.webm"
        output_path = os.path.join(STICKERS_DIR, output_filename)

        if os.path.exists(output_path):
            print(f"[{i+1}/{len(files)}] Bỏ qua (đã tách rồi): {filename}")
            continue

        print(f"[{i+1}/{len(files)}] Đang tách nền: {filename} ...")

        # Sử dụng chromakey để xóa màu xanh, xuất ra WebM với nền trong suốt
        cmd = [
            _ffmpeg(), "-y",
            "-i", input_path,
            "-vf", "chromakey=0x00FF00:0.3:0.1,despill=type=green",
            "-c:v", "libvpx-vp9",  # Chuẩn nén hỗ trợ nền trong suốt
            "-pix_fmt", "yuva420p", # Định dạng pixel có kênh Alpha (trong suốt)
            "-b:v", "2M",           # Bitrate 2Mbps cho nét
            output_path
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(output_path):
            print(f"  -> Thành công: {output_filename}")
        else:
            print(f"  -> Lỗi khi xử lý {filename}")

if __name__ == "__main__":
    tach_nen_xanh()
    print("=== HOÀN TẤT ===")