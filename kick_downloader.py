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

def load_cookies(driver, cookies_file):
    if not os.path.exists(cookies_file):
        print("No cookies.txt found — skipping cookie load.")
        return False

    try:
        with open(cookies_file, 'r') as f:
            cookies = []
            for line in f:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split('\t')
                    if len(parts) >= 7:
                        cookies.append({
                            'name': parts[5],
                            'value': parts[6],
                            'domain': parts[0],
                            'path': parts[2],
                            'secure': parts[3].lower() == 'true',
                            'expires': int(parts[4]) if parts[4].isdigit() else None
                        })
        driver.get('https://kick.com')
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logging.warning(f"Failed to add cookie {cookie['name']}: {e}")
        print("✅ Cookies loaded.")
        driver.refresh()
        return True
    except Exception as e:
        logging.error(f"Cookie load error: {e}")
        return False

def download_with_ffmpeg(m3u8_url, save_path):
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        print(f"📥 Downloading video with FFmpeg to {save_path} ...")
        cmd = [
            'ffmpeg',
            '-i', m3u8_url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            save_path
        ]
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if process.returncode == 0:
            print("✅ Download complete!")
            logging.info(f"Video downloaded: {save_path}")
            return True
        else:
            print("❌ FFmpeg failed.")
            logging.error(f"FFmpeg error: {process.stderr}")
            return False
    except Exception as e:
        print(f"❌ FFmpeg exception: {e}")
        logging.error(f"FFmpeg exception: {e}")
        return False

def find_m3u8_in_source(page_source):
    pattern = r'https?://[^\s"]+\.m3u8'
    matches = re.findall(pattern, page_source)
    return matches[0] if matches else None

def download_kick_video(video_url, save_path, cookies_file=None):
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

        if cookies_file:
            load_cookies(driver, cookies_file)

        print("🌐 Navigating to the video page...")
        driver.get(video_url)

        time.sleep(10)
        print("⏳ Waiting for page to load...")

        page_source = driver.page_source
        m3u8_url = find_m3u8_in_source(page_source)

        if m3u8_url:
            print(f"🔗 Found m3u8 URL: {m3u8_url}")
            return download_with_ffmpeg(m3u8_url, save_path)
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
    # You can change these to be dynamic later
    video_url = "https://kick.com/chaos333gg/clips/clip_01J97PAS46AE7DZD6HZSJATE66"
    save_path = "./videos/kick_video.mp4"
    cookies_file = "cookies.txt"

    success = download_kick_video(video_url, save_path, cookies_file)
    if not success:
        print("❌ Download failed.")
    else:
        print("✅ All done.")
