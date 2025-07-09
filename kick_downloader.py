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
    """
    Download a Kick video using undetected-chromedriver and FFmpeg.
    
    Args:
        video_url (str): The Kick video URL (e.g., https://kick.com/chaos333gg/clips/clip_01J97PAS46AE7DZD6HZSJATE66).
        save_path (str): Local path to save the video (e.g., './videos/kick_video.mp4').
        cookies_file (str): Path to Netscape-format cookies.txt file (optional).
    
    Returns:
        bool: True if download is successful, False otherwise.
    """
    logging.info(f"Starting download for {video_url}")
    print(f"Starting download for {video_url}")
    
    driver = None
    try:
        # Set up undetected-chromedriver
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36')
        
        driver = uc.Chrome(options=options, use_subprocess=True)
        
        # Load cookies if provided
        if cookies_file and os.path.exists(cookies_file):
            if load_cookies(driver, cookies_file):
                logging.info("Cookies loaded, navigating to video URL")
                print("Cookies loaded, navigating to video URL")
        
        # Navigate to the video page
        logging.info(f"Navigating to {video_url}")
        print(f"Navigating to {video_url}")
        driver.get(video_url)
        
        # Wait for page to load
        time.sleep(10)  # Increased wait for JavaScript and player
        page_source = driver.page_source
        
        # Search for M3U8 URL
        m3u8_url = find_m3u8_in_source(page_source)
        if m3u8_url:
            logging.info(f"Found M3U8 URL: {m3u8_url}")
            print(f"Found M3U8 URL: {m3u8_url}")
            return download_with_ffmpeg(m3u8_url, save_path)
        
        logging.warning("No M3U8 URL found in page source")
        print("No M3U8 URL found in page source")
        print("Falling back to manual method. Follow these steps:")
        print("1. Open Chrome, go to the video URL.")
        print("2. Press F12 → Network → Media → Filter by 'm3u8'.")
        print("3. Copy the M3U8 URL.")
        print("4. Run: ffmpeg -i \"your_m3u8_url\" -c copy kick_video.mp4")
        return False
    
    except Exception as e:
        logging.error(f"Error: {e}")
        print(f"Error: {e}")
        print("Falling back to manual method. Follow these steps:")
        print("1. Open Chrome, go to the video URL.")
        print("2. Press F12 → Network → Media → Filter by 'm3u8'.")
        print("3. Copy the M3U8 URL.")
        print("4. Run: ffmpeg -i \"your_m3u8_url\" -c copy kick_video.mp4")
        return False
    
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logging.error(f"Error quitting driver: {e}")
                print(f"Error quitting driver: {e}")

# Example usage
if __name__ == "__main__":
    kick_url = "https://kick.com/chaos333gg/clips/clip_01J97PAS46AE7DZD6HZSJATE66"
    save_path = "./videos/kick_video.mp4"
    cookies_file = "cookies.txt"  # Optional: Path to cookies.txt
    download_kick_video(kick_url, save_path, cookies_file)