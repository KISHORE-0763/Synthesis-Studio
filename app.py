# ==============================================================================
# Synthesis Studio: AI Presenter & Reel Editor
# Author: [Your Name]
# Version: 2.0
#
# This version includes a print statement for debugging deployment issues.
# It contains two features: AI Presenter Generation and AI Viral Captions.
# ==============================================================================

# --- Core Libraries ---
import streamlit as st
from PIL import Image
import os
import requests
import time

# --- AI & Video Processing Libraries ---
import replicate
from moviepy.editor import *

# ==============================================================================
# 1. PAGE CONFIGURATION & API MANAGEMENT
# ==============================================================================

st.set_page_config(
    page_title="Synthesis Studio",
    page_icon="🤖",
    layout="wide"
)

# This print statement helps us confirm in the logs that the latest code is running.
print("--- Using App Version 2.0 with simplified requirements ---")

# Securely load API keys from Streamlit's secrets manager
D_ID_API_KEY = st.secrets.get("D_ID_API_KEY")
REPLICATE_API_TOKEN = st.secrets.get("REPLICATE_API_TOKEN")

# Set the Replicate API token as an environment variable for the library to use
if REPLICATE_API_TOKEN:
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
else:
    # This error will show up on the page if the Replicate key is missing.
    st.error("Replicate API token not found. Please add it to your Streamlit secrets to enable AI features.")

# ==============================================================================
# 2. HELPER FUNCTIONS (The "Backend" Logic)
# ==============================================================================

# --- D-ID Functions ---
D_ID_URL = "https://api.d-id.com/talks"
AVATAR_URL = "https://cdn.d-id.com/images/predefined_laura.jpg" # Using a stable, predefined avatar

def create_talk(script_text):
    """Sends a script to the D-ID API to start a video generation job."""
    if not D_ID_API_KEY:
        st.error("D-ID API Key not found. Please ensure it is set in your Streamlit secrets.")
        return None
    headers = {"Authorization": f"Basic {D_ID_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "script": {
            "type": "text", "input": script_text,
            "provider": {"type": "microsoft", "voice_id": "en-US-JennyNeural"}
        },
        "source_url": AVATAR_URL,
        "config": {"result_format": "mp4"}
    }
    try:
        response = requests.post(D_ID_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating D-ID talk: {e}\nResponse: {response.text if 'response' in locals() else 'N/A'}")
        return None

def get_talk_result(talk_id):
    """Periodically checks the D-ID job status and returns the video URL upon completion."""
    if not D_ID_API_KEY: return None
    headers = {"Authorization": f"Basic {D_ID_API_KEY}"}
    status = ""
    while status not in ["done", "error"]:
        try:
            response = requests.get(f"{D_ID_URL}/{talk_id}", headers=headers)
            response.raise_for_status()
            result = response.json()
            status = result.get("status")
            st.toast(f"D-ID video generation status: {status}...")
            time.sleep(10)
        except requests.exceptions.RequestException as e:
            st.error(f"Error getting D-ID result: {e}")
            return None
    if status == "error":
        st.error(f"D-ID job failed: {result.get('result')}")
        return None
    return result.get("result_url")

# --- Replicate & MoviePy Functions ---
def transcribe_audio_with_timestamps(audio_file_path):
    """Transcribes audio using Whisper on Replicate to get word-level timestamps."""
    if not REPLICATE_API_TOKEN:
        st.error("Replicate API token not found. Cannot generate captions.")
        return None
    try:
        with open(audio_file_path, "rb") as audio_file:
            model_endpoint = "openai/whisper:4d50797290df275329f202e48c76360b3f22b08d28c196cbc54600319435f815"
            input_data = {"audio": audio_file, "word_timestamps": True}
            output = replicate.run(model_endpoint, input=input_data)
            return output.get("segments", [])
    except Exception as e:
        st.error(f"An error occurred during transcription: {e}")
        return None

def create_video_with_captions(original_video_path, segments):
    """Uses moviepy to burn word-by-word captions onto the original video."""
    try:
        video_clip = VideoFileClip(original_video_path)
        text_clips = []
        for segment in segments:
            for word_info in segment.get('words', []):
                word, start, end = word_info['word'], word_info['start'], word_info['end']
                txt_clip = TextClip(word.upper(), fontsize=70, color='white', font='Impact', stroke_color='black', stroke_width=2)
                txt_clip = txt_clip.set_pos('center').set_duration(end - start).set_start(start)
                text_clips.append(txt_clip)
        
        final_video = CompositeVideoClip([video_clip] + text_clips)
        final_video_path = "temp_captioned_video.mp4"
        final_video.write_videofile(final_video_path, codec='libx264', audio_codec='aac', threads=4)
        return final_video_path
    except Exception as e:
        st.error(f"Error creating captioned video: {e}")
        if "ImageMagick" in str(e):
            st.error("MoviePy Error: ImageMagick is not installed or not found. This is usually pre-installed on Streamlit Cloud but required for local execution.")
        return None


# ==============================================================================
# 3. STREAMLIT UI
# ==============================================================================

st.title("Synthesis Studio 🤖🎬")
st.write("An all-in-one AI toolkit for creating engaging short-form videos.")

# --- Feature 1: AI Presenter Generation ---
with st.container(border=True):
    st.header("Feature 1: Generate a Video from a Script")
    st.write("Type a script, and our AI presenter will create a video for you.")
    
    script = st.text_area("Enter your script here:", height=150,
                          placeholder="e.g., Welcome back! Today, we're discussing three powerful tips...")

    if st.button("Generate AI Presenter Video", type="primary"):
        if not script:
            st.warning("Please enter a script first.")
        elif not D_ID_API_KEY:
            st.error("D-ID API Key is missing. Cannot generate video.")
        else:
            with st.spinner("Sending script to our AI presenter..."):
                talk_data = create_talk(script)
            if talk_data and talk_data.get("id"):
                talk_id = talk_data["id"]
                st.info(f"Video generation job started! Please wait, this can take a few minutes.")
                with st.spinner("AI is rendering your video..."):
                    video_url = get_talk_result(talk_id)
                if video_url:
                    st.success("Your AI Presenter video is ready!")
                    st.video(video_url)
                else: st.error("Failed to retrieve the generated video.")
            else: st.error("Failed to start the video generation job.")

# --- Feature 2: AI Viral Captions ---
with st.container(border=True):
    st.header("Feature 2: Generate Viral Captions for a Video")
    st.write("Upload a video with speech, and we'll add dynamic, word-by-word captions.")
    
    caption_video_file = st.file_uploader("Upload a video file", type=['mp4', 'mov'], key="caption_video")

    if caption_video_file:
        st.video(caption_video_file)
        if st.button("Generate Captions"):
            if not REPLICATE_API_TOKEN:
                st.error("Replicate API Token is missing. Cannot generate captions.")
            else:
                # Save uploaded file temporarily to process it
                with open("temp_video.mp4", "wb") as f:
                    f.write(caption_video_file.getbuffer())
                
                # Extract audio from the video
                with st.spinner("Step 1/3: Extracting audio..."):
                    video_clip = VideoFileClip("temp_video.mp4")
                    audio_path = "temp_audio.mp3"
                    video_clip.audio.write_audiofile(audio_path)
                
                # Transcribe the audio
                with st.spinner("Step 2/3: Transcribing audio with Whisper AI..."):
                    segments = transcribe_audio_with_timestamps(audio_path)
                
                # Burn captions onto the video
                if segments:
                    with st.spinner("Step 3/3: Burning captions onto your video... This is intensive!"):
                        final_video_path = create_video_with_captions("temp_video.mp4", segments)
                    
                    if final_video_path:
                        st.success("Captioned video generated!")
                        # It's better to read the file bytes into the video element
                        with open(final_video_path, 'rb') as f_video:
                            video_bytes = f_video.read()
                        st.video(video_bytes)
                        # Re-open for the download button
                        with open(final_video_path, 'rb') as f_download:
                            st.download_button("Download Captioned Video", f_download, file_name="captioned_video.mp4")
                    else: st.error("Could not create the final video.")
                else: st.error("Could not transcribe the audio.")
