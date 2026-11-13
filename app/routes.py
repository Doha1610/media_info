# app/routes.py
import os
import uuid
import threading
from flask import Blueprint, request, jsonify, send_file, send_from_directory
from app.config import (
    DOWNLOADS_DIR, OUTPUTS_DIR, TEMP_DIR, STICKERS_DIR,
    SUPPORTED_AUDIO_EXT, MAX_CONTENT_LENGTH
)
from app.core.downloader import Downloader
from app.core.audio_mixer import AudioMixer
from app.core.image_to_video import ImageToVideo

bp = Blueprint("api", __name__)

# Lưu trữ log tạm cho từng job
JOBS = {}

def _log_cb(job_id):
    def _cb(msg):
        JOBS.setdefault(job_id, {"log": [], "done": False, "ok": None})
        JOBS[job_id]["log"].append(msg)
    return _cb

# ---------- Trang chủ ----------
@bp.route("/")
def index():
    return send_from_directory("static", "index.html")

# ---------- Tải video/nhạc ----------
@bp.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json() or {}
    url = (data.get("url") or "").strip()
    mode = data.get("mode", "video")

    if not url:
        return jsonify({"error": "Thiếu URL"}), 400

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"log": [], "done": False, "ok": None}

    def worker():
        dl = Downloader(on_log=_log_cb(job_id))
        ok = dl.download_video(url) if mode == "video" else dl.download_audio(url)
        JOBS[job_id]["done"] = True
        JOBS[job_id]["ok"] = ok

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"job_id": job_id})

@bp.route("/api/log/<job_id>")
def api_log(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job không tồn tại"}), 404
    return jsonify(job)

# ---------- Chèn nhạc ----------
@bp.route("/api/mix", methods=["POST"])
def api_mix():
    audio_file = request.files.get("audio")
    music_file = request.files.get("music")
    position   = request.form.get("position", "Đầu")

    if not audio_file or not music_file:
        return jsonify({"error": "Thiếu file"}), 400

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"log": [], "done": False, "ok": None, "result": None}

    audio_path = os.path.join(TEMP_DIR, f"{job_id}_audio_{audio_file.filename}")
    music_path = os.path.join(TEMP_DIR, f"{job_id}_music_{music_file.filename}")
    audio_file.save(audio_path)
    music_file.save(music_path)

    def worker():
        mixer = AudioMixer(on_log=_log_cb(job_id))
        result = mixer.insert_music(audio_path, music_path, position)
        JOBS[job_id]["done"] = True
        JOBS[job_id]["ok"] = result is not None
        if result:
            JOBS[job_id]["result"] = os.path.basename(result)
        for p in (audio_path, music_path):
            try: os.remove(p)
            except: pass

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"job_id": job_id})

# ---------- Lấy danh sách Sticker ----------
@bp.route("/api/stickers", methods=["GET"])
def api_list_stickers():
    files = []
    if os.path.exists(STICKERS_DIR):
        for f in os.listdir(STICKERS_DIR):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.mp4', '.webm', '.gif')):
                files.append(f)
    files.sort()
    return jsonify(files)

# ---------- Ảnh → Video (Có hỗ trợ Sticker) ----------
@bp.route("/api/image-to-video", methods=["POST"])
def api_image_to_video():
    image_file = request.files.get("image")
    audio_file = request.files.get("audio")
    sticker_name = request.form.get("sticker_name")
    resolution = request.form.get("resolution", "1280x720")
    fps_raw    = request.form.get("fps", "1")
    
    # Nhận thông số vị trí và kích thước
    sticker_size = int(request.form.get("sticker_size", 400))
    sticker_pos  = request.form.get("sticker_pos", "center")

    if not image_file or not audio_file:
        return jsonify({"error": "Thiếu ảnh hoặc audio"}), 400

    try:
        fps = max(1, min(int(fps_raw), 60))
    except ValueError:
        fps = 1

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"log": [], "done": False, "ok": None, "result": None}

    image_path = os.path.join(TEMP_DIR, f"{job_id}_img_{image_file.filename}")
    audio_path = os.path.join(TEMP_DIR, f"{job_id}_audio_{audio_file.filename}")
    image_file.save(image_path)
    audio_file.save(audio_path)

    sticker_path = None
    if sticker_name:
        temp_sticker = os.path.join(STICKERS_DIR, sticker_name)
        if os.path.exists(temp_sticker):
            sticker_path = temp_sticker

    def worker():
        maker = ImageToVideo(on_log=_log_cb(job_id))
        result = maker.create(
            image_path, audio_path,
            resolution=resolution, fps=fps,
            sticker_path=sticker_path,
            sticker_size=sticker_size,  # Truyền kích thước
            sticker_pos=sticker_pos     # Truyền vị trí
        )
        JOBS[job_id]["done"] = True
        JOBS[job_id]["ok"] = result is not None
        if result:
            JOBS[job_id]["result"] = os.path.basename(result)
            
        for p in (image_path, audio_path):
            if p and os.path.exists(p):
                try: os.remove(p)
                except: pass

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"job_id": job_id})

# ---------- Tải kết quả ----------
@bp.route("/api/download-result/<filename>")
def api_download_result(filename):
    return send_from_directory(OUTPUTS_DIR, filename, as_attachment=True)

# ---------- Liệt kê file ----------
@bp.route("/api/files/downloads")
def api_list_downloads():
    files = []
    for f in os.listdir(DOWNLOADS_DIR):
        p = os.path.join(DOWNLOADS_DIR, f)
        if os.path.isfile(p):
            files.append({"name": f, "size": os.path.getsize(p), "mtime": os.path.getmtime(p)})
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return jsonify(files)

@bp.route("/api/files/outputs")
def api_list_outputs():
    files = []
    for f in os.listdir(OUTPUTS_DIR):
        p = os.path.join(OUTPUTS_DIR, f)
        if os.path.isfile(p):
            files.append({"name": f, "size": os.path.getsize(p), "mtime": os.path.getmtime(p)})
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return jsonify(files)