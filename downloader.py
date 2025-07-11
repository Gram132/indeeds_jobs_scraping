import subprocess
import os
from datetime import datetime
from upload_to_drive import upload_to_drive

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

def cut_and_watermark_kick_video(m3u8_url, start_time, duration, logo_path="logo.png", streamer_name="MoroccanStreamer123", font_path=""):
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

    # Step 2: Add logo + seamless scrolling text banner
    overlay_pos = get_overlay_position("top_left")

    # Create the scrolling message repeated twice for seamless loop
    base_message = (
        f"🎥 Clip by: {streamer_name} — Follow him on Kick.com and show some support! "
        f"Let's grow the Moroccan streaming scene together! 🇲🇦💚"
    )
    repeat_message = base_message + "    " + base_message  # spaces between repeats

    # Format drawtext filter for seamless scrolling (scrolls over twice the text width)
    drawtext = (
        f"drawtext=text='{repeat_message}':"
        f"fontcolor=green:fontsize=30:"
        f"x=w-mod(t*100\\,text_w*2):y=h-th-20:"
        f"box=1:boxcolor=red@1.0:boxborderw=10"
    )

    # Add font if specified
    if font_path:
        drawtext = f"drawtext=fontfile='{font_path}':" + drawtext[len("drawtext="):]

    # FFmpeg filter chain: logo overlay + scrolling text
    filter_complex = f"[1]scale=180:-1[logo];[0][logo]overlay={overlay_pos}, {drawtext}"

    watermark_cmd = [
        "ffmpeg",
        "-i", raw_video,
        "-i", logo_path,
        "-filter_complex", filter_complex,
        "-c:a", "copy",
        "-preset", "ultrafast",
        final_video
    ]

    print(f"🖼️ Adding logo and seamless scrolling text to: {final_video}")
    try:
        subprocess.run(watermark_cmd, check=True)
        print(f"✅ Final video ready: {final_video}")
    except subprocess.CalledProcessError:
        print("❌ Failed to apply watermark and text.")
        return

    # Step 3: Upload to Drive
    try:
        upload_to_drive(final_video)
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return

    # Step 4: Clean up
    os.remove(raw_video)
    os.remove(final_video)
    print("🧹 Cleaned up local files.")



cut_and_watermark_kick_video(
    m3u8_url="https://stream.kick.com/ivs/v1/196233775518/IA8u3S766VUV/2025/7/4/19/31/zGqB0p1c0rTx/media/hls/720p30/playlist.m3u8",
    start_time="00:01:00",
    duration="00:02:00",
    logo_path="./logo/logo.png",
    streamer_name="Chaos333",
)






"""
if __name__ == "__main__":
    m3u8_url_list =[
        {
            "m3u8_url":"https://stream.kick.com/ivs/v1/196233775518/wsB6eI5iA6yn/2025/7/7/17/27/ABvqDhn376cm/media/hls/1080p60/playlist.m3u8",
            "start":"00:15:50",
            "duration":"01:41:00"
            
        },
        {
            "m3u8_url":"https://stream.kick.com/ivs/v1/196233775518/eoPm4ekt0lqJ/2025/6/30/22/35/Rey5tRgFCnpk/media/hls/1080p60/playlist.m3u8",
            "start":"01:12:00",
            "duration":"01:12:00"
        },
        {
            "m3u8_url":"https://stream.kick.com/ivs/v1/196233775518/HaIvcroXy7Rb/2025/6/30/22/1/anAKNmqO2s8I/media/hls/1080p/playlist.m3u8",
            "start":"01:47:47",
            "duration":"01:44:00"
        },
        {
            "m3u8_url":"",
            "start":"03:07:40",
            "duration":"00:56:20"
        },
    ]
    for m3u8 in m3u8_url_list :
        start_time = m3u8['start']
        duration = m3u8['duration']
        logo_path = "./logo/logo.png"
        
        cut_and_watermark_kick_video(m3u8['m3u8_url'], start_time, duration, logo_path)
        time.sleep(120)

"""