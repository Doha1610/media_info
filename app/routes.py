# app/routes.py
import os
import uuid
import threading
from app.core.youtube_uploader import YouTubeUploader
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

# ---------- API Đăng YouTube ----------
@bp.route("/api/youtube-upload", methods=["POST"])
def api_youtube_upload():
    data = request.get_json()
    filename = data.get("filename")
    title = data.get("title", "Video của tôi")
    description = data.get("description", "")
    privacy = data.get("privacy", "private")
    schedule_time = data.get("schedule_time") # Định dạng: "2026-12-31T15:00:00+07:00"

    if not filename:
        return jsonify({"error": "Thiếu tên file"}), 400

    # Lấy đường dẫn file từ thư mục OUTPUTS
    full_path = os.path.join(OUTPUTS_DIR, filename)
    if not os.path.exists(full_path):
        return jsonify({"error": "Không tìm thấy file video"}), 404

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"log": [], "done": False, "ok": None}

    def worker():
        try:
            uploader = YouTubeUploader(on_log=_log_cb(job_id))
            video_id = uploader.upload_video(full_path, title, description, privacy, schedule_time)
            JOBS[job_id]["done"] = True
            JOBS[job_id]["ok"] = True
            JOBS[job_id]["video_id"] = video_id
        except Exception as e:
            JOBS[job_id]["log"].append(f"Lỗi: {str(e)}")
            JOBS[job_id]["done"] = True
            JOBS[job_id]["ok"] = False

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"job_id": job_id})

# ---------- API Đổi Tài Khoản Google (Xóa token) ----------
@bp.route("/api/youtube-reset-token", methods=["POST"])
def api_youtube_reset_token():
    token_path = "token.json"
    if os.path.exists(token_path):
        try:
            os.remove(token_path)
            return jsonify({"ok": True, "message": "Đã xóa token thành công"})
        except Exception as e:
            return jsonify({"ok": False, "message": f"Lỗi khi xóa: {str(e)}"}), 500
    return jsonify({"ok": False, "message": "Không có token để xóa"})

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

# ---------- Chèn nhạc (Đã cập nhật nhận nhiều file) ----------
@bp.route("/api/mix", methods=["POST"])
def api_mix():
    audio_file = request.files.get("audio")
    # NHẬN DANH SÁCH NHIỀU FILE NHẠC
    music_files = request.files.getlist("music")
    position   = request.form.get("position", "Đầu")

    if not audio_file or not music_files or music_files[0].filename == '':
        return jsonify({"error": "Thiếu file audio gốc hoặc nhạc chèn"}), 400

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"log": [], "done": False, "ok": None, "result": None}

    # Lưu file audio gốc
    audio_path = os.path.join(TEMP_DIR, f"{job_id}_audio_{audio_file.filename}")
    audio_file.save(audio_path)

    # Lưu TẤT CẢ các file nhạc và lấy danh sách đường dẫn
    music_paths = []
    for idx, mf in enumerate(music_files):
        m_path = os.path.join(TEMP_DIR, f"{job_id}_music_{idx}_{mf.filename}")
        mf.save(m_path)
        music_paths.append(m_path)

    def worker():
        mixer = AudioMixer(on_log=_log_cb(job_id))
        # Truyền danh sách music_paths vào hàm
        result = mixer.insert_music(audio_path, music_paths, position)
        
        JOBS[job_id]["done"] = True
        JOBS[job_id]["ok"] = result is not None
        if result:
            JOBS[job_id]["result"] = os.path.basename(result)
            
        # Dọn dẹp tất cả file tạm
        for p in [audio_path] + music_paths:
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