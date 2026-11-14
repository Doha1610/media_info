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

    def insert_music(self, audio_in, music_list, position="Đầu", out_dir=None):
        """
        audio_in: File audio gốc
        music_list: Danh sách (list) các đường dẫn file nhạc cần chèn
        """
        out_dir = out_dir or OUTPUTS_DIR
        os.makedirs(out_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(audio_in))[0]
        output_file = os.path.join(out_dir, f"{base_name}_mixed_{int(time.time())}.mp3")

        # Sắp xếp thứ tự đầu vào: 
        # Nếu chèn "Đầu" thì Nhạc đứng trước, Audio gốc đứng sau. 
        # Nếu chèn "Cuối" thì Audio gốc đứng trước, Nhạc đứng sau.
        if position == "Đầu":
            inputs = music_list + [audio_in]
        else:
            inputs = [audio_in] + music_list

        # Xây dựng câu lệnh FFmpeg
        cmd = [self._ffmpeg(), "-y"]
        for inp in inputs:
            cmd.extend(["-i", inp])

        # Tạo bộ lọc concat động cho N file (N = số file nhạc + 1 file audio gốc)
        # Ví dụ có 3 file: [0:a][1:a][2:a]concat=n=3:v=0:a=1[outa]
        n_files = len(inputs)
        fc = "".join(f"[{i}:a]" for i in range(n_files))
        fc += f"concat=n={n_files}:v=0:a=1[outa]"

        cmd.extend([
            "-filter_complex", fc,
            "-map", "[outa]",
            "-c:a", "libmp3lame", "-q:a", "2",
            output_file
        ])

        self.on_log(f"Đang chạy lệnh ghép {n_files} file...")
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace"
        )
        
        # Đọc log của FFmpeg
        for line in proc.stdout:
            line = line.strip()
            if "time=" in line or "error" in line.lower():
                self.on_log(line)

        proc.wait()
        return output_file if proc.returncode == 0 else None