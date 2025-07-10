import os
import time
import re
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_m3u8_url(kick_url):
    print(f"🌐 Opening Kick video: {kick_url}")
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = uc.Chrome(options=options)

    try:
        driver.get(kick_url)
        try:
            # Wait up to 20 seconds for <video> tag to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, 'video'))
            )
            print("✅ Video element loaded.")
        except Exception:
            print("⚠️ Warning: Video element did not load in 20 seconds.")

        page_source = driver.page_source
        m3u8_match = re.search(r'(https:\/\/[^\s"]+\.m3u8)', page_source)
        return m3u8_match.group(1) if m3u8_match else None
    finally:
        driver.quit()

def download_clip_part(m3u8_url, start_time, duration, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cmd = [
        'ffmpeg',
        '-ss', str(start_time),
        '-i', m3u8_url,
        '-t', str(duration),
        '-c', 'copy',
        '-loglevel', 'error',
        output_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def split_long_video(m3u8_url, start_sec, end_sec, part_length_sec=3000):
    total_duration = end_sec - start_sec
    num_parts = (total_duration + part_length_sec - 1) // part_length_sec

    print(f"🔄 Splitting video: {num_parts} parts of {part_length_sec} seconds")
    
    for i in range(num_parts):
        part_start = start_sec + i * part_length_sec
        actual_duration = min(part_length_sec, end_sec - part_start)
        part_file = f"videos/part_{i+1}.mp4"
        print(f"📥 Downloading {part_file} (start: {part_start}s, duration: {actual_duration}s)")
        success = download_clip_part(m3u8_url, part_start, actual_duration, part_file)
        if not success:
            print(f"❌ Failed to download {part_file}")
            break

if __name__ == "__main__":
    kick_url = "https://kick.com/chaos333gg/videos/28252e5d-70c1-4fc2-afa5-cf0f34087065"  # replace this
    start_time = "00:30:00"
    end_time = "02:00:00"

    def to_seconds(hms):
        h, m, s = map(int, hms.split(":"))
        return h * 3600 + m * 60 + s

    m3u8_url = extract_m3u8_url(kick_url)
    if m3u8_url:
        print(f"🔗 Found m3u8 URL: {m3u8_url}")
        split_long_video(
            m3u8_url=m3u8_url,
            start_sec=to_seconds(start_time),
            end_sec=to_seconds(end_time),
            part_length_sec=3000  # 50 minutes
        )
        print("✅ Done.")
    else:
        print("❌ Failed to extract m3u8 URL.")
