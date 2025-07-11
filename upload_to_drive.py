import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_NAME = 'kick_streaming'

def upload_to_drive(file_path, upload_name=None):
    creds = None

    # Step 1: Authenticate if token not exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('kick_downloader_token.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Step 2: Build service
    service = build('drive', 'v3', credentials=creds)

    # Step 3: Find or create folder
    folder_id = None
    query = f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = response.get('files', [])

    if folders:
        folder_id = folders[0]['id']
        print(f"📁 Found folder '{FOLDER_NAME}' with ID: {folder_id}")
    else:
        folder_metadata = {
            'name': FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')
        print(f"📁 Created folder '{FOLDER_NAME}' with ID: {folder_id}")

    # Step 4: Prepare and upload the file
    file_metadata = {
        'name': upload_name or os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    print(f"✅ Uploaded to Google Drive with ID: {uploaded_file.get('id')}")

# Example use
if __name__ == '__main__':
    upload_to_drive('./videos/kick_clip_20250711_165534.mp4')
