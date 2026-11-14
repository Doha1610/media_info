# app/core/youtube_uploader.py
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubeUploader:
    def __init__(self, on_log=None):
        self.on_log = on_log or (lambda m: None)
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        self.CLIENT_SECRETS_FILE = "client_secret.json"
        self.TOKEN_FILE = "token.json"
        self.youtube = None

    def authenticate(self):
        creds = None
        if os.path.exists(self.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # SỬ DỤNG CHẾ ĐỘ THỦ CÔNG THAY VÌ TỰ ĐỘNG MỞ TRÌNH DUYỆT
                flow = InstalledAppFlow.from_client_secrets_file(self.CLIENT_SECRETS_FILE, self.SCOPES)
                flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob' # Chế độ copy/paste code
                
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                self.on_log("="*60)
                self.on_log("VUI LÒNG COPY ĐƯỜNG LINK SAU VÀ DÁN VÀO TRÌNH DUYỆT:")
                self.on_log(auth_url)
                self.on_log("="*60)
                self.on_log("Sau khi đăng nhập và cấp quyền, trình duyệt sẽ hiện một MÃ CODE.")
                self.on_log("Hãy copy mã code đó và dán vào cửa sổ đen (Terminal) này rồi ấn Enter:")
                
                # Đợi người dùng nhập mã code từ bàn phím
                code = input("Nhập mã code: ")
                flow.fetch_token(code=code)
                creds = flow.credentials

            with open(self.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        self.youtube = build('youtube', 'v3', credentials=creds)

    def upload_video(self, file_path, title, description, privacy_status="private", publish_at=None):
        if not self.youtube:
            self.authenticate()

        self.on_log(f"Đang chuẩn bị upload: {title}")
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': privacy_status
            }
        }

        if publish_at and privacy_status == 'private':
            body['status']['publishAt'] = publish_at 
            self.on_log(f"Đã đặt lịch đăng vào: {publish_at}")

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        request = self.youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                self.on_log(f"Đang tải lên... {int(status.progress() * 100)}%")

        self.on_log(f"✅ Upload thành công! Video ID: {response['id']}")
        return response['id']