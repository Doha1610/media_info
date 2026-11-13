# app/core/audio_mixer.py
import subprocess
import os
import time
from app.config import OUTPUTS_DIR, FFMPEG_PATH


class AudioMixer:
    def __init__(self, on_log=None):
        self.on_log = on_log or (lambda m: None)

    def _ffmpeg(self):
        # Lấy đường dẫn ffmpeg.exe từ thư mục bin đã khai báo trong config
        if FFMPEG_PATH and os.path.exists(FFMPEG_PATH):
            ffmpeg_exe = os.path.join(FFMPEG_PATH, "ffmpeg.exe")
            if os.path.exists(ffmpeg_exe):
                return ffmpeg_exe
        return "ffmpeg" # Fallback về biến môi trường nếu không tìm thấy

    def insert_music(self, audio_in, music_in, position="Đầu", out_dir=None):
        out_dir = out_dir or OUTPUTS_DIR
        os.makedirs(out_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(audio_in))[0]
        output_file = os.path.join(out_dir, f"{base_name}_mixed_{int(time.time())}.mp3")

        # Cấu hình filter để nối 2 file âm thanh
        if position == "Đầu":
            # Nhạc chèn trước, Audio gốc sau
            fc = "[1:a][0:a]concat=n=2:v=0:a=1[outa]"
        else:
            # Audio gốc trước, Nhạc chèn sau
            fc = "[0:a][1:a]concat=n=2:v=0:a=1[outa]"

        cmd = [
            self._ffmpeg(), "-y",
            "-i", audio_in,
            "-i", music_in,
            "-filter_complex", fc,
            "-map", "[outa]",
            "-c:a", "libmp3lame", "-q:a", "2",
            output_file
        ]

        self.on_log("Đang chạy lệnh: " + " ".join(cmd))
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace"
        )
        
        # Đọc log của FFmpeg (chỉ in ra những dòng cần thiết để tránh rối mắt)
        for line in proc.stdout:
            line = line.strip()
            if "time=" in line or "error" in line.lower():
                self.on_log(line)

        proc.wait()
        return output_file if proc.returncode == 0 else None