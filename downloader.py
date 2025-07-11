import subprocess
import os
from datetime import datetime
from upload_to_drive import upload_to_drive  # ✅ Import the upload function

def get_overlay_position(position):
    positions = {
        'bottom_left':  "10:H-h-10",
        'bottom_right': "W-w-10:H-h-10",
        'top_left':     "10:10",
        'top_right':    "W-w-10:10",
        'bottom_center':"(W-w)/2:H-h-10",
        'top_center':   "(W-w)/2:10"
    }
    return positions.get(position, "W-w-10:H-h-10")  # default: bottom right

def cut_and_watermark_kick_video(m3u8_url, start_time, duration, logo_path="logo.png"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_video = f"raw_kick_clip_{timestamp}.mp4"
    final_video = f"kick_clip_{timestamp}.mp4"

    # Step 1: Cut from m3u8
    cut_cmd = [
        "ffmpeg",
        "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
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
        print("❌ Failed to cut video. Check FFmpeg or m3u8 link.")
        return

    # Step 2: Resize logo and overlay
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
        print(f"✅ Final video ready: {final_video}")
    except subprocess.CalledProcessError:
        print("❌ Failed to apply watermark. Check your logo and video.")
        return

    # Step 3: Upload to Google Drive
    try:
        upload_to_drive(final_video)
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return

    # Step 4: Cleanup local files
    os.remove(raw_video)
    os.remove(final_video)
    print("🧹 Cleaned up local files.")

if __name__ == "__main__":
    m3u8_url = "https://stream.kick.com/ivs/v1/196233775518/IA8u3S766VUV/2025/7/8/0/18/6RbZCzVLI71j/media/hls/720p30/playlist.m3u8"
    start_time = "00:01:00"
    duration = "00:00:30"
    logo_path = "./logo/logo.png"

    cut_and_watermark_kick_video(m3u8_url, start_time, duration, logo_path)
