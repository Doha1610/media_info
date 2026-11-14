# app/routes.py
import os
import uuid
import threading
import time
import shutil
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

# ---------- API TỰ ĐỘNG HÓA TOÀN BỘ QUY TRÌNH ----------
@bp.route("/api/auto-workflow", methods=["POST"])
def api_auto_workflow():
    url = request.form.get("url")
    position = request.form.get("position", "Đầu")
    resolution = request.form.get("resolution", "1920x1080")
    fps = int(request.form.get("fps", 1))
    sticker_name = request.form.get("sticker_name")
    sticker_size = int(request.form.get("sticker_size", 400))
    sticker_pos = request.form.get("sticker_pos", "center")
    auto_upload = request.form.get("auto_upload") == "true"
    yt_privacy = request.form.get("yt_privacy", "private")
    yt_title = request.form.get("yt_title", "Video tự động")
    
    image_file = request.files.get("image")
    music_files = request.files.getlist("music")

    if not url or not image_file:
        return jsonify({"error": "Vui lòng nhập Link và chọn Ảnh!"}), 400

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"log": [], "done": False, "ok": None, "result": None}
    log = _log_cb(job_id)

    # Lưu file tạm
    job_temp_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_temp_dir, exist_ok=True)
    
    image_path = os.path.join(job_temp_dir, f"image_{image_file.filename}")
    image_file.save(image_path)

    music_paths = []
    for idx, mf in enumerate(music_files):
        if mf.filename:
            mp = os.path.join(job_temp_dir, f"music_{idx}_{mf.filename}")
            mf.save(mp)
            music_paths.append(mp)

    def worker():
        try:
            # BƯỚC 1: TẢI NHẠC
            log("=== BƯỚC 1: TẢI NHẠC TỪ LINK ===")
            dl = Downloader(on_log=log)
            if not dl.download_audio(url):
                raise Exception("Tải nhạc thất bại.")
            
            # Tìm file mp3 vừa tải
            time.sleep(1) # Đợi 1 chút để file ghi xong
            downloaded_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) if f.endswith('.mp3')]
            if not downloaded_files:
                raise Exception("Không tìm thấy file mp3 nào vừa tải.")
            latest_audio = max(downloaded_files, key=os.path.getctime)
            log(f"Đã tải xong: {os.path.basename(latest_audio)}")

            current_audio = latest_audio

            # BƯỚC 2: GHÉP NHẠC (Nếu có)
            if music_paths:
                log("=== BƯỚC 2: GHÉP NHẠC CHÈN ===")
                mixer = AudioMixer(on_log=log)
                mixed_audio = mixer.insert_music(current_audio, music_paths, position)
                if not mixed_audio:
                    raise Exception("Ghép nhạc thất bại.")
                current_audio = mixed_audio
                log("Ghép nhạc thành công!")

            # BƯỚC 3: TẠO VIDEO TỪ ẢNH
            log("=== BƯỚC 3: TẠO VIDEO TỪ ẢNH ===")
            sticker_path = os.path.join(STICKERS_DIR, sticker_name) if sticker_name else None
            maker = ImageToVideo(on_log=log)
            final_video = maker.create(
                image_in=image_path, 
                audio_in=current_audio,
                resolution=resolution, 
                fps=fps, 
                sticker_path=sticker_path,
                sticker_size=sticker_size,
                sticker_pos=sticker_pos
            )
            if not final_video:
                raise Exception("Tạo video thất bại.")
            
            JOBS[job_id]["result"] = os.path.basename(final_video)
            log("Tạo video thành công!")

            # BƯỚC 4: ĐĂNG YOUTUBE (Nếu có tích)
            if auto_upload:
                log("=== BƯỚC 4: ĐĂNG LÊN YOUTUBE ===")
                uploader = YouTubeUploader(on_log=log)
                vid_id = uploader.upload_video(final_video, yt_title, "Video được tạo tự động bởi Media Tool", yt_privacy)
                log(f"Đăng YouTube thành công! ID: {vid_id}")

            JOBS[job_id]["done"] = True
            JOBS[job_id]["ok"] = True
            log("✅ TOÀN BỘ QUY TRÌNH HOÀN TẤT!")

        except Exception as e:
            log(f"❌ LỖI: {str(e)}")
            JOBS[job_id]["done"] = True
            JOBS[job_id]["ok"] = False
        finally:
            # Dọn dẹp thư mục tạm
            try: shutil.rmtree(job_temp_dir)
            except: pass

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"job_id": job_id})

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

# ---------- Chèn nhạc ----------
@bp.route("/api/mix", methods=["POST"])
def api_mix():
    audio_file = request.files.get("audio")
    music_files = request.files.getlist("music")
    position   = request.form.get("position", "Đầu")

    if not audio_file or not music_files or music_files[0].filename == '':
        return jsonify({"error": "Thiếu file audio gốc hoặc nhạc chèn"}), 400

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"log": [], "done": False, "ok": None, "result": None}

    audio_path = os.path.join(TEMP_DIR, f"{job_id}_audio_{audio_file.filename}")
    audio_file.save(audio_path)

    music_paths = []
    for idx, mf in enumerate(music_files):
        m_path = os.path.join(TEMP_DIR, f"{job_id}_music_{idx}_{mf.filename}")
        mf.save(m_path)
        music_paths.append(m_path)

    def worker():
        mixer = AudioMixer(on_log=_log_cb(job_id))
        result = mixer.insert_music(audio_path, music_paths, position)
        
        JOBS[job_id]["done"] = True
        JOBS[job_id]["ok"] = result is not None
        if result:
            JOBS[job_id]["result"] = os.path.basename(result)
            
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

# ---------- Ảnh → Video ----------
@bp.route("/api/image-to-video", methods=["POST"])
def api_image_to_video():
    image_file = request.files.get("image")
    audio_file = request.files.get("audio")
    sticker_name = request.form.get("sticker_name")
    resolution = request.form.get("resolution", "1280x720")
    fps_raw    = request.form.get("fps", "1")
    
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
            sticker_size=sticker_size,
            sticker_pos=sticker_pos
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