# --- app.py (Initial Version for Deployment) ---
import streamlit as st
import requests
import time
import os

# --- Page Config & API Keys ---
st.set_page_config(page_title="Synthesis Studio", layout="wide")

# This securely reads the secrets you will provide on the Streamlit Cloud platform.
D_ID_API_KEY = st.secrets.get("D_ID_API_KEY")
REPLICATE_API_TOKEN = st.secrets.get("REPLICATE_API_TOKEN") # We will use this later

if REPLICATE_API_TOKEN:
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# --- D-ID API Functions ---
D_ID_URL = "https://api.d-id.com/talks"
# Use a direct URL to a high-quality, public-domain image for the avatar
AVATAR_URL = "https://i.imgur.com/E3OU9S8.png"

def create_talk(script_text):
    """Sends the script to D-ID to start the video generation job."""
    if not D_ID_API_KEY:
        st.error("D-ID API Key not found. Please ensure it is set in your Streamlit secrets.")
        return None

    headers = {
        "Authorization": f"Basic {D_ID_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "script": {"type": "text", "input": script_text},
        "source_url": AVATAR_URL,
        "config": {"result_format": "mp4"}
    }
    try:
        response = requests.post(D_ID_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating talk with D-ID: {e}")
        st.error(f"Response Body: {response.text if 'response' in locals() else 'No response'}")
        return None

def get_talk_result(talk_id):
    """Checks the status of the D-ID job and returns the video URL when ready."""
    if not D_ID_API_KEY:
        return None
    
    headers = {"Authorization": f"Basic {D_ID_API_KEY}"}
    status = ""
    while status != "done":
        try:
            response = requests.get(f"{D_ID_URL}/{talk_id}", headers=headers)
            response.raise_for_status()
            result = response.json()
            status = result.get("status")
            if status == "error":
                st.error(f"D-ID job failed: {result.get('result')}")
                return None
            st.toast(f"Video generation status: {status}...")
            time.sleep(10) # Using a longer sleep time for cloud deployment
        except requests.exceptions.RequestException as e:
            st.error(f"Error getting talk result: {e}")
            return None
    
    return result.get("result_url")

# --- Streamlit UI ---
st.title("Synthesis Studio 🤖🎬")
st.write("Generate a complete Reel from just a script, powered by AI.")
st.info("This is version 1.0: AI Presenter Generation. Captions and music coming soon!")

st.subheader("1. Write Your Script")
script = st.text_area("Enter the text you want the AI presenter to speak:", height=150,
                      placeholder="e.g., Welcome back to our channel! Today, we're discussing...")

if st.button("Generate My AI Presenter Video", type="primary"):
    if not script:
        st.warning("Please enter a script first.")
    elif not D_ID_API_KEY:
        st.error("D-ID API Key is missing. Cannot generate video.")
    else:
        with st.spinner("Sending script to our AI presenter..."):
            talk_data = create_talk(script)
        
        if talk_data and talk_data.get("id"):
            talk_id = talk_data["id"]
            st.info(f"Video generation started! Job ID: {talk_id}. Please wait, this can take a few minutes.")
            with st.spinner("AI is practicing its lines... Rendering video..."):
                video_url = get_talk_result(talk_id)
            
            if video_url:
                st.success("Your AI Presenter video is ready!")
                st.video(video_url)
            else:
                st.error("Failed to retrieve the generated video.")
        else:
            st.error("Failed to start the video generation job.")
