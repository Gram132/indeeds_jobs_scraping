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

    # Base ffmpeg command: re-encode for better compatibility especially with long videos
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
        # Limit download to first 10 minutes (600 seconds) if fallback
        cmd.insert(cmd.index('-i'), '-t')
        cmd.insert(cmd.index('-t') + 1, '600')

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

def load_cookies(driver, cookies_file):
    """Load cookies from cookies.txt (Netscape format) into Selenium driver."""
    import http.cookies
    if not os.path.exists(cookies_file):
        print("⚠️ Cookies file not found, skipping cookie load.")
        return

    print(f"🔑 Loading cookies from {cookies_file} ...")
    with open(cookies_file, 'r') as f:
        for line in f:
            if line.startswith('#') or line.strip() == '':
                continue
            # Netscape cookie format: domain \t flag \t path \t secure \t expiration \t name \t value
            parts = line.strip().split('\t')
            if len(parts) != 7:
                continue
            domain, flag, path, secure, expiration, name, value = parts
            cookie_dict = {
                'domain': domain,
                'name': name,
                'value': value,
                'path': path,
                'secure': True if secure == 'TRUE' else False,
                'httpOnly': False,
            }
            try:
                driver.add_cookie(cookie_dict)
            except Exception as e:
                logging.warning(f"Could not add cookie {name}: {e}")

def find_m3u8_in_source(page_source):
    pattern = r'https?://[^\s"]+\.m3u8'
    matches = re.findall(pattern, page_source)
    return matches[0] if matches else None

def download_kick_video(video_url, save_path, cookies_file='cookies.txt'):
    print(f"🚀 Starting download for: {video_url}")
    logging.info(f"Starting download for: {video_url}")
    driver = None

    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')

        driver = uc.Chrome(options=options)

        print("🌐 Opening Kick video page...")
        driver.get(video_url)

        # Load cookies AFTER initial get (domain must match)
        load_cookies(driver, cookies_file)

        # Refresh page after loading cookies for them to take effect
        driver.refresh()

        print("⏳ Waiting for video page to load...")
        time.sleep(15)  # Increase wait for full page + JS video load

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
            print("❌ Failed to extract m3u8 URL.")
            logging.error("Failed to extract m3u8 URL from page source.")
            return False

    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        logging.error(f"Exception: {e}")
        return False

    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logging.warning(f"Driver quit error: {e}")

if __name__ == "__main__":
    # Example clips / videos to download
    video_list = [
        {
            'URL': 'https://kick.com/chaos333gg/clips/clip_01JZDJQS6MKYX9GS3XQAJK33RQ',
            'name': 'video_001'
        },
        {
            'URL': 'https://kick.com/chaos333gg/videos/28252e5d-70c1-4fc2-afa5-cf0f34087065',
            'name': 'long_video_001'
        },
    ]

    for item in video_list:
        url = item['URL']
        path = f"./videos/{item['name']}.mp4"
        print(f"\n⬇️ Downloading: {url}")
        success = download_kick_video(url, path)
        if success:
            print(f"✅ Finished downloading: {path}")
        else:
            print(f"❌ Failed to download: {url}")
