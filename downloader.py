import os
import json
import subprocess
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_NAME = 'kick_streaming'

def save_secret_to_file(env_var, file_path):
    try:
        content = os.environ[env_var]
        with open(file_path, 'w') as f:
            f.write(content)
    except KeyError:
        raise RuntimeError(f"❌ GitHub Secret `{env_var}` is missing. Please set it in your repo settings.")

def upload_to_drive(file_path, upload_name=None):
    save_secret_to_file('TOKEN_JSON', 'token.json')
    save_secret_to_file('KICK_DOWNLOADER_TOKEN_JSON', 'kick_downloader_token.json')

    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('kick_downloader_token.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    # Create or find target folder
    query = f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = response.get('files', [])
    if folders:
        folder_id = folders[0]['id']
        print(f"📁 Found folder '{FOLDER_NAME}'")
    else:
        folder_metadata = {
            'name': FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')
        print(f"📁 Created folder '{FOLDER_NAME}'")

    # Upload the video
    file_metadata = {
        'name': upload_name or os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"✅ Uploaded to Google Drive: {uploaded_file.get('id')}")

def get_overlay_position(position):
    positions = {
        'bottom_left':  "10:H-h-10",
        'bottom_right': "W-w-10:H-h-10",
        'top_left':     "10:10",
        'top_right':    "W-w-10:10",
        'bottom_center':"(W-w)/2:H-h-10",
        'top_center':   "(W-w)/2:10"
    }
    return positions.get(position, "W-w-10:H-h-10")

def cut_and_watermark_kick_video(m3u8_url, start_time, duration, logo_path="logo.png"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_video = f"raw_kick_clip_{timestamp}.mp4"
    final_video = f"kick_clip_{timestamp}.mp4"

    # Step 1: Download segment
    cut_cmd = [
        "ffmpeg",
        "-user_agent", "Mozilla/5.0",
        "-referer", "https://kick.com/",
        "-ss", start_time,
        "-i", m3u8_url,
        "-t", duration,
        "-c", "copy",
        raw_video
    ]
    print(f"🎬 Cutting clip to: {raw_video}")
    try:
        subprocess.run(cut_cmd, check=True)
    except subprocess.CalledProcessError:
        print("❌ Failed to cut video. Check the m3u8 link or ffmpeg.")
        return

    # Step 2: Add logo
    overlay_pos = get_overlay_position("top_left")
    watermark_cmd = [
        "ffmpeg",
        "-i", raw_video,
        "-i", logo_path,
        "-filter_complex", f"[1]scale=180:-1[logo];[0][logo]overlay={overlay_pos}",
        "-c:a", "copy",
        "-preset", "ultrafast",
        final_video
    ]
    print(f"🖼️ Adding logo to: {final_video}")
    try:
        subprocess.run(watermark_cmd, check=True)
    except subprocess.CalledProcessError:
        print("❌ Failed to apply watermark.")
        return

    # Step 3: Upload
    try:
        upload_to_drive(final_video)
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return

    # Step 4: Cleanup
    os.remove(raw_video)
    os.remove(final_video)
    print("🧹 Cleaned up local files.")

if __name__ == "__main__":
    m3u8_url = "https://stream.kick.com/ivs/v1/196233775518/IA8u3S766VUV/2025/7/8/0/18/6RbZCzVLI71j/media/hls/720p30/playlist.m3u8"
    start_time = "00:01:00"
    duration = "00:00:30"
    logo_path = "./logo/logo.png"
    cut_and_watermark_kick_video(m3u8_url, start_time, duration, logo_path)
