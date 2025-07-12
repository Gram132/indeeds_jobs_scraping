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

def escape_text_for_drawtext(text):
    return text.replace(":", r'\:').replace("'", r"\\'")

def cut_and_watermark_kick_video(m3u8_url, start_time, duration, logo_path="logo.png", streamer_name="MoroccanStreamer123", font_path=""):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_video = f"raw_kick_clip_{timestamp}.mp4"
    final_video = f"kick_clip_{timestamp}.mp4"

    # Step 1: Download clip from m3u8
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

    # Step 2: Add watermark + scrolling text
    overlay_pos = get_overlay_position("top_left")

    base_message = (
        f"Clip by: {streamer_name} - Follow him on Kick.com and show some support! "
        f"Catch amazing gameplay, reactions, and stories! "
        f"Support the Moroccan streaming scene! "
    )
    repeat_message = base_message + "     " + base_message
    safe_text = escape_text_for_drawtext(repeat_message)

    if font_path:
        drawtext_filter = (
            f"drawtext=fontfile='{font_path}':"
            f"text='{safe_text}':"
            f"fontcolor=#53fc18:fontsize=30:"
            f"x=w-mod(t*100\\,text_w*2):y=h-th-20:"
            f"box=1:boxcolor=#b31015@1.0:boxborderw=10"
        )
    else:
        drawtext_filter = (
            f"drawtext=text='{safe_text}':"
            f"fontcolor=#53fc18:fontsize=30:"
            f"x=w-mod(t*100\\,text_w*2):y=h-th-20:"
            f"box=1:boxcolor=#b31015@1.0:boxborderw=10"
        )

    filter_complex = f"[1]scale=180:-1[logo];[0][logo]overlay={overlay_pos},{drawtext_filter}"

    watermark_cmd = [
        "ffmpeg",
        "-y",  # Overwrite output if exists
        "-i", raw_video,
        "-i", logo_path,
        "-filter_complex", filter_complex,
        "-c:a", "copy",
        "-preset", "ultrafast",
        final_video
    ]

    print(f"🖼️ Running FFmpeg to apply logo and scrolling text...")
    print("🔧 Command preview:\n", " ".join(watermark_cmd))

    try:
        result = subprocess.run(watermark_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = result.stdout.decode()
        if result.returncode != 0:
            print("❌ FFmpeg failed:\n", output)
            return
        print(f"✅ Final video ready: {final_video}")
    except Exception as e:
        print(f"❌ FFmpeg exception: {e}")
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







if __name__ == "__main__":
    
    m3u8_url_list =[
        {
            "m3u8_url":"https://stream.kick.com/ivs/v1/196233775518/HaIvcroXy7Rb/2025/6/30/22/1/anAKNmqO2s8I/media/hls/1080p/playlist.m3u8",
            "start":"01:47:47",
            "duration":"01:44:00",
            "Streamer":"Mahamawda",

        },
        {
            "m3u8_url":"",
            "start":"03:07:40",
            "duration":"00:56:20",
            "Streamer":"Bougassaa",

        },
    ]

    for m3u8 in m3u8_url_list :
        m3u8Url= m3u8['m3u8_url']
        start_time = m3u8['start']
        duration = m3u8['duration']
        logo_path = "./logo/logo.png"
        streamer = m3u8['Streamer']
        
        # 🧪 Run the script
        cut_and_watermark_kick_video(
            m3u8_url=m3u8Url,
            start_time=start_time ,
            duration=duration ,
            logo_path=logo_path ,
            streamer_name=streamer,
            font_path="./font/Merriweather.ttf"  # Make sure this path and file are correct
        )