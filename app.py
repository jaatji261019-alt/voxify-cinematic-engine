from fastapi import FastAPI
from fastapi.responses import FileResponse
import requests
import os
from moviepy.editor import *
from uuid import uuid4

app = FastAPI()

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# 🎨 FREE AI IMAGE (Pollinations)
def get_image(prompt, idx):
    url = f"https://image.pollinations.ai/prompt/{prompt} cinematic lighting 4k"
    img_path = f"{TEMP_DIR}/img_{idx}.jpg"

    img = requests.get(url).content
    with open(img_path, "wb") as f:
        f.write(img)

    return img_path


# 🎬 CREATE CINEMATIC VIDEO
@app.post("/cinematic")
async def create_video(data: dict):
    text = data.get("text")
    audio_url = data.get("audioUrl")

    if not text or not audio_url:
        return {"error": "Missing text/audio"}

    # 🎧 download audio
    audio_path = f"{TEMP_DIR}/audio.mp3"
    audio_data = requests.get(audio_url).content
    with open(audio_path, "wb") as f:
        f.write(audio_data)

    # ✂️ split scenes
    scenes = text.split(".")
    clips = []

    for i, scene in enumerate(scenes):
        if not scene.strip():
            continue

        img_path = get_image(scene, i)

        clip = ImageClip(img_path).set_duration(3)
        clip = clip.resize((720, 1280))

        clips.append(clip)

    # 🎬 merge all
    video = concatenate_videoclips(clips, method="compose")

    audio = AudioFileClip(audio_path)
    video = video.set_audio(audio)

    output_path = f"{TEMP_DIR}/output_{uuid4().hex}.mp4"
    video.write_videofile(output_path, fps=24)

    return FileResponse(output_path, media_type="video/mp4", filename="cinematic.mp4")
