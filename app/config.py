# app/config.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HOST = "127.0.0.1"
PORT = 5000

DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
OUTPUTS_DIR   = os.path.join(BASE_DIR, "outputs")
LOGS_DIR      = os.path.join(BASE_DIR, "logs")
TEMP_DIR      = os.path.join(BASE_DIR, "temp")
STICKERS_DIR = os.path.join(BASE_DIR, "stickers")
os.makedirs(STICKERS_DIR, exist_ok=True)
for _d in (DOWNLOADS_DIR, OUTPUTS_DIR, LOGS_DIR, TEMP_DIR):
    os.makedirs(_d, exist_ok=True)

SUPPORTED_AUDIO_EXT = [".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg"]

# TRỎ TỚI THƯ MỤC BIN, KHÔNG CÓ ĐUÔI .EXE
FFMPEG_PATH = r"D:\ffmpeg-9.0.1-essentials_build\bin"

MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB