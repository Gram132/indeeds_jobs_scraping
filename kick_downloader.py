import undetected_chromedriver as uc
import re
import subprocess
import os
import sys
import time
import logging

# Set up logging to file
logging.basicConfig(
    filename='kick_download.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_cookies(driver, cookies_file):
    """Load cookies from a Netscape-format cookies.txt file."""
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
                logging.error(f"Failed to add cookie {cookie['name']}: {e}")
                print(f"Failed to add cookie {cookie['name']}: {e}")
        logging.info("Cookies loaded successfully")
        print("Cookies loaded successfully")
        driver.refresh()
        return True
    except Exception as e:
        logging.error(f"Error loading cookies: {e}")
        print(f"Error loading cookies: {e}")
        return False

def download_with_ffmpeg(m3u8_url, save_path):
    """Download video using FFmpeg via subprocess."""
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
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
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW  # Avoid Windows console popups
        )
        if process.returncode == 0:
            logging.info(f"Video downloaded successfully to {save_path}")
            print(f"Video downloaded successfully to {save_path}")
            return True
        else:
            logging.error(f"FFmpeg failed: {process.stderr}")
            print(f"FFmpeg failed: {process.stderr}")
            return False
    except Exception as e:
        logging.error(f"FFmpeg error: {e}")
        print(f"FFmpeg error: {e}")
        return False

def find_m3u8_in_source(page_source):
    """Search page source for M3U8 URLs."""
    m3u8_pattern = r'https?://[^\s"]+\.m3u8'
    matches = re.findall(m3u8_pattern, page_source)
    return matches[0] if matches else None

def download_kick_video(video_url, save_path, cookies_file=None):
    logging.info(f"Starting download: {video_url}")
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')

        driver = uc.Chrome(options=options)

        # ✅ Only try to load cookies if the file exists
        if cookies_file and os.path.exists(cookies_file):
            logging.info("Cookies file found, loading cookies...")
            load_cookies(driver, cookies_file)
        else:
            logging.info("No cookies file found. Continuing without cookies.")

        driver.get(video_url)
        time.sleep(10)
        page_source = driver.page_source

        m3u8_url = find_m3u8_in_source(page_source)
        if m3u8_url:
            logging.info(f"Found m3u8: {m3u8_url}")
            return download_with_ffmpeg(m3u8_url, save_path)
        else:
            logging.warning("No m3u8 URL found.")
            return False

    except Exception as e:
        logging.error(f"Error: {e}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logging.error(f"Driver quit error: {e}")

# Example usage
if __name__ == "__main__":
    kick_url = "https://kick.com/chaos333gg/clips/clip_01J97PAS46AE7DZD6HZSJATE66"
    save_path = "./videos/kick_video.mp4"
    cookies_file = "cookies.txt"  # Optional: Path to cookies.txt
    download_kick_video(kick_url, save_path, cookies_file)