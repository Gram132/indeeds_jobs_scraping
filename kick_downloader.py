import undetected_chromedriver as uc
import re
import subprocess
import os
import time
import logging

# === Logging config ===
logging.basicConfig(
    filename='kick_download.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def download_with_ffmpeg(m3u8_url, save_path, fallback_partial=False):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    print(f"📥 Downloading video with FFmpeg to {save_path} ...")

    # Main command (re-encoding, better for long videos)
    cmd = [
        'ffmpeg',
        '-y',
        '-loglevel', 'error',
        '-i', m3u8_url,
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', '28',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        save_path
    ]

    if fallback_partial:
        cmd.insert(cmd.index('-i'), '-t')
        cmd.insert(cmd.index('-t') + 1, '600')  # 10 minutes

    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if process.returncode == 0:
            print("✅ Download complete!")
            if os.path.exists(save_path):
                size = os.path.getsize(save_path)
                print(f"✅ File exists at: {save_path}")
                print(f"📦 Size: {size / (1024 * 1024):.2f} MB")
                return True
        else:
            print("❌ FFmpeg failed.")
            logging.error(f"FFmpeg stderr: {process.stderr}")
            return False
    except Exception as e:
        print(f"❌ FFmpeg exception: {e}")
        logging.error(f"FFmpeg exception: {e}")
        return False


def find_m3u8_in_source(page_source):
    pattern = r'https?://[^\s"]+\.m3u8'
    matches = re.findall(pattern, page_source)
    return matches[0] if matches else None


def download_kick_video(video_url, save_path):
    print(f"🚀 Starting download for: {video_url}")
    logging.info(f"Starting for: {video_url}")
    driver = None

    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0')

        driver = uc.Chrome(options=options)

        print("🌐 Navigating to the video page...")
        driver.get(video_url)

        print("⏳ Waiting for page to load...")
        time.sleep(10)

        page_source = driver.page_source
        m3u8_url = find_m3u8_in_source(page_source)

        if m3u8_url:
            print(f"🔗 Found m3u8 URL: {m3u8_url}")
            success = download_with_ffmpeg(m3u8_url, save_path)
            if not success:
                print("⚠️ Retrying with partial (10-minute) download...")
                success = download_with_ffmpeg(m3u8_url, save_path, fallback_partial=True)
            return success
        else:
            print("❌ No m3u8 URL found.")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        logging.error(f"Exception: {e}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logging.warning(f"Driver quit error: {e}")


if __name__ == "__main__":
    list_of_clips = [
        {
        'URL':'https://kick.com/chaos333gg/clips/clip_01JZDJQS6MKYX9GS3XQAJK33RQ',
        'name':'video_001'
        },
        {
        'URL':'https://kick.com/chaos333gg/clips/clip_01JZ9DD9C8FBA3PXT1JJQ6WDC9',
        'name':'video_002'}, 
        ]
    
    for i in list_of_clips :
        kick_url = i['URL']
        save_path = f"./videos/{i['name']}.mp4"
        cookies_file = "cookies.txt"  # Optional: Path to cookies.txt
        success = download_kick_video(kick_url, save_path)
        if not success:
            print("❌ Download failed.")
        else:
            print("✅ All done.")
