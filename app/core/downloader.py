# app/core/downloader.py
import os
import shutil
import subprocess

from app.config import DOWNLOADS_DIR, FFMPEG_PATH

class Downloader:
    def __init__(self, on_log=None):
        self.on_log = on_log or (lambda m: None)

    def _run(self, cmd):
        if shutil.which(cmd[0]) is None:
            self.on_log(f"Không tìm thấy lệnh: {cmd[0]}")
            return 1

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            self.on_log(f"Không thể khởi chạy {cmd[0]}: {exc}")
            return 1

        for line in proc.stdout or []:
            if line.strip():
                self.on_log(line.strip())

        proc.wait()
        return proc.returncode

    def _prepare_out_dir(self, out_dir):
        out_dir = out_dir or DOWNLOADS_DIR
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def download_video(self, url, out_dir=None):
        out_dir = self._prepare_out_dir(out_dir)
        tpl = os.path.join(out_dir, "%(title)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
        ]
        
        # Truyền thư mục bin cho yt-dlp
        if FFMPEG_PATH and os.path.exists(FFMPEG_PATH):
            cmd.extend(["--ffmpeg-location", FFMPEG_PATH])
            
        cmd.extend(["-o", tpl, url])
        return self._run(cmd) == 0

    def download_audio(self, url, out_dir=None):
        out_dir = self._prepare_out_dir(out_dir)
        tpl = os.path.join(out_dir, "%(title)s.%(ext)s")

        cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
        ]
        
        # Truyền thư mục bin cho yt-dlp
        if FFMPEG_PATH and os.path.exists(FFMPEG_PATH):
            cmd.extend(["--ffmpeg-location", FFMPEG_PATH])
            
        cmd.extend(["-o", tpl, url])
        return self._run(cmd) == 0