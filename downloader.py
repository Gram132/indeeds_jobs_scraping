import subprocess
import os
import logging

logging.basicConfig(
    filename='kick_download.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def download_with_ytdlp(video_url, save_path, cookies_file=None):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    print(f"⬇️ Downloading: {video_url}")
    logging.info(f"Downloading {video_url}")

    cmd = [
        'yt-dlp',
        video_url,
        '-o', save_path,
        '--no-progress',
        '--newline',
        '--quiet'
    ]

    if cookies_file:
        cmd.extend(['--cookies', cookies_file])

    # Add headers to help bypass some restrictions
    cmd.extend([
        '--add-header', 'Referer:https://kick.com/',
        '--add-header', 'User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    ])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Download complete: {save_path}")
            logging.info(f"Download success: {save_path}")
            return True
        else:
            print(f"❌ yt-dlp failed:\n{result.stderr}")
            logging.error(f"yt-dlp error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ yt-dlp exception: {e}")
        logging.error(f"yt-dlp exception: {e}")
        return False


def download_with_streamlink(video_url, save_path, cookies_file=None):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    print(f"⚡ Attempting streamlink fallback: {video_url}")
    logging.info(f"Streamlink fallback for {video_url}")

    # Streamlink requires cookies in Netscape format, make sure your cookies file is compatible
    cmd = [
        'streamlink',
        video_url,
        'best',
        '-o', save_path
    ]

    # If you have cookies, you can pass them like --http-cookie "name=value" or from file
    # streamlink does NOT support --cookies file like yt-dlp, so you may need to add headers if needed
    # For now, let's assume no cookies for streamlink or add headers if you want

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Streamlink download complete: {save_path}")
            logging.info(f"Streamlink download success: {save_path}")
            return True
        else:
            print(f"❌ Streamlink failed:\n{result.stderr}")
            logging.error(f"Streamlink error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Streamlink exception: {e}")
        logging.error(f"Streamlink exception: {e}")
        return False


def download_kick_video(video_url, save_path, cookies_file=None):
    # First try yt-dlp
    success = download_with_ytdlp(video_url, save_path, cookies_file)
    if success:
        return True

    # If yt-dlp fails, fallback to streamlink
    print("⚠️ yt-dlp failed, trying streamlink fallback...")
    return download_with_streamlink(video_url, save_path, cookies_file)


if __name__ == "__main__":
    list_of_videos = [
        {
            'URL': 'https://kick.com/chaos333gg/clips/clip_01JZDJQS6MKYX9GS3XQAJK33RQ',
            'name': 'clip_001'
        },
        {
            'URL': 'https://kick.com/chaos333gg/videos/28252e5d-70c1-4fc2-afa5-cf0f34087065',
            'name': 'long_video_001'
        },
    ]

    cookies_file = 'cookies.txt'  # Your cookies file path in Netscape format

    for video in list_of_videos:
        url = video['URL']
        out_path = f'./videos/{video["name"]}.mp4'
        if not download_kick_video(url, out_path, cookies_file=cookies_file):
            print(f"❌ Failed to download: {url}")
        else:
            print(f"✅ Successfully downloaded: {out_path}")