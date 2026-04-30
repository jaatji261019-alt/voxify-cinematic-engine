from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import requests
import os
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from uuid import uuid4

app = FastAPI(title="Voxify Cinematic Engine 🎬")

# ================= CONFIG =================
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

MAX_SCENES = 6
IMAGE_DURATION = 3


# ================= IMAGE FETCH =================
def get_image(prompt, idx):
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt} cinematic lighting 4k"
        img_path = f"{TEMP_DIR}/img_{idx}_{uuid4().hex}.jpg"

        res = requests.get(url, timeout=15)

        if res.status_code != 200:
            return None

        with open(img_path, "wb") as f:
            f.write(res.content)

        return img_path

    except Exception as e:
        print("Image error:", e)
        return None


# ================= AUDIO DOWNLOAD =================
def download_audio(audio_url):
    try:
        path = f"{TEMP_DIR}/audio_{uuid4().hex}.mp3"

        res = requests.get(audio_url, timeout=20)

        if res.status_code != 200:
            return None

        with open(path, "wb") as f:
            f.write(res.content)

        return path

    except Exception as e:
        print("Audio error:", e)
        return None


# ================= VIDEO =================
@app.post("/cinematic")
async def create_video(data: dict):
    try:
        text = data.get("text")
        audio_url = data.get("audioUrl")

        if not text or not audio_url:
            raise HTTPException(status_code=400, detail="Missing text/audio")

        # ================= AUDIO =================
        audio_path = download_audio(audio_url)
        if not audio_path:
            raise HTTPException(status_code=500, detail="Audio download failed")

        # ================= SCENES =================
        scenes = [s.strip() for s in text.split(".") if s.strip()][:MAX_SCENES]

        clips = []

        for i, scene in enumerate(scenes):
            img_path = get_image(scene, i)

            if not img_path:
                continue

            clip = (
                ImageClip(img_path)
                .set_duration(IMAGE_DURATION)
                .resize((720, 1280))
                .fadein(0.5)
                .fadeout(0.5)
            )

            clips.append(clip)

        if not clips:
            raise HTTPException(status_code=500, detail="No images generated")

        # ================= MERGE =================
        video = concatenate_videoclips(clips, method="compose")

        audio = AudioFileClip(audio_path)
        video = video.set_audio(audio)

        # ================= OUTPUT =================
        output_path = f"{TEMP_DIR}/video_{uuid4().hex}.mp4"

        video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=2,
            preset="ultrafast"
        )

        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename="voxify_cinematic.mp4"
        )

    except HTTPException as e:
        raise e

    except Exception as e:
        print("Server error:", e)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
