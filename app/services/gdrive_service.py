import os
import io
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

class GDriveService:
    def __init__(self, credentials_dir):
        self.credentials_dir = credentials_dir
        self.service = self._init_service()

    def _init_service(self):
        sa_path = os.path.join(self.credentials_dir, "service_account.json")
        client_secret_path = os.path.join(self.credentials_dir, "client_secret.json")
        token_path = os.path.join(self.credentials_dir, "token.json")

        if os.path.exists(sa_path):
            creds = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
            return build("drive", "v3", credentials=creds)
        elif os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            return build("drive", "v3", credentials=creds)
        elif os.path.exists(client_secret_path):
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, "w") as f:
                f.write(creds.to_json())
            return build("drive", "v3", credentials=creds)
        else:
            raise FileNotFoundError("Nenhuma credencial do Google Drive encontrada em credentials/")

    def upload_file(self, file_stream, filename, mimetype=None, parent_folder_id=None):
        file_metadata = {"name": filename}
        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]
        media = MediaIoBaseUpload(file_stream, mimetype=mimetype, resumable=True)
        file = self.service.files().create(body=file_metadata, media_body=media, fields="id, name").execute()
        return file.get("id")

    def download_file(self, file_id):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh
