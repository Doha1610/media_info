# run.py
import webbrowser
import threading
from app import create_app
from app.config import HOST, PORT


def open_browser():
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    app = create_app()
    # Tự mở trình duyệt sau 1 giây
    threading.Timer(1.0, open_browser).start()
    print(f"🚀 Server đang chạy tại http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)