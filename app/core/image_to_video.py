# app/core/image_to_video.py
import subprocess
import os
import time
from app.config import OUTPUTS_DIR, FFMPEG_PATH

class ImageToVideo:
    def __init__(self, on_log=None):
        self.on_log = on_log or (lambda m: None)

    def _ffmpeg(self):
        if FFMPEG_PATH and os.path.exists(FFMPEG_PATH):
            ffmpeg_exe = os.path.join(FFMPEG_PATH, "ffmpeg.exe")
            if os.path.exists(ffmpeg_exe):
                return ffmpeg_exe
        return "ffmpeg"

    def create(self, image_in, audio_in, out_dir=None, resolution="1280x720", fps=1, 
               sticker_path=None, sticker_size=400, sticker_pos="center"):
        out_dir = out_dir or OUTPUTS_DIR
        os.makedirs(out_dir, exist_ok=True)

        base = os.path.splitext(os.path.basename(audio_in))[0]
        output_file = os.path.join(out_dir, f"{base}_video_{int(time.time())}.mp4")

        w_str, h_str = resolution.split('x')
        w = int(w_str)
        h = int(h_str)

        # TÍNH TOÁN TỌA ĐỘ X
        if sticker_pos == "left":
            x_pos = 20
        elif sticker_pos == "right":
            x_pos = w - sticker_size - 20
        else:
            x_pos = (w - sticker_size) // 2

        # TỌA ĐỘ Y
        y_pos = h - 400

        is_sticker_video = False
        if sticker_path:
            ext = os.path.splitext(sticker_path)[1].lower()
            if ext in ['.mp4', '.webm', '.mov', '.gif']:
                is_sticker_video = True

        # SỬ DỤNG -stream_loop -1 CHO STICKER, ẢNH THÌ KHÔNG CẦN LOOP
        cmd_inputs = ["-loop", "1", "-i", image_in, "-i", audio_in]
        
        if sticker_path and os.path.exists(sticker_path):
            if is_sticker_video:
                # Đặt -stream_loop -1 ngay trước sticker để nó lặp
                cmd_inputs.extend(["-stream_loop", "-1", "-i", sticker_path])
            else:
                cmd_inputs.extend(["-loop", "1", "-i", sticker_path])

        if sticker_path and os.path.exists(sticker_path):
            # Dùng shortest=1 ở overlay
            vf = (
                f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black[bg];"
                f"[2:v]scale={sticker_size}:-1,colorkey=0x00FF00:0.3:0.1,despill=type=green[sticker];"
                f"[bg][sticker]overlay={x_pos}:{y_pos}:shortest=1[outv]"
            )
            
            cmd = [self._ffmpeg(), "-y"] + cmd_inputs + [
                "-filter_complex", vf,
                "-map", "[outv]", "-map", "1:a"
            ]
        else:
            vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p"
            cmd = [self._ffmpeg(), "-y"] + cmd_inputs + [
                "-vf", vf,
                "-map", "0:v", "-map", "1:a"
            ]
            
        cmd.extend([
            "-c:v", "libx264", 
            "-preset", "ultrafast",
            "-tune", "stillimage", 
            "-pix_fmt", "yuv420p", 
            "-r", str(fps),
            "-c:a", "aac", "-b:a", "192k", 
            "-shortest",             # Vẫn giữ -shortest ở đây
            "-movflags", "+faststart",
            output_file
        ])

        self.on_log("Đang chạy lệnh: " + " ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")

        for line in proc.stdout:
            line = line.strip()
            if "time=" in line or "error" in line.lower():
                self.on_log(line)

        proc.wait()
        return output_file if proc.returncode == 0 else None