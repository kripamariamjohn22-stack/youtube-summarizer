from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import os
import re

st.set_page_config(page_title="YT Summarizer", page_icon="🎬", layout="centered")

st.title("🎬 YouTube Summarizer")
st.caption("Paste any YouTube link → get a clean summary in seconds")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("Missing GROQ_API_KEY in your .env file.")
    st.stop()

def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_id):
    try:
        ytt = YouTubeTranscriptApi()
        fetched = ytt.fetch(video_id)
        full_text = " ".join([item.text for item in fetched])
        return full_text
    except Exception as e:
        st.error(f"Transcript error: {e}")
        return None

def summarize(transcript, style):
    from groq import Groq  # pyright: ignore[reportMissingImports]

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    style_prompts = {
        "Quick (3 bullets)": "Summarize this YouTube video transcript in exactly 3 bullet points. Be concise.",
        "Detailed": "Summarize this YouTube video transcript in detail. Include main points, key insights, and important details. Use bullet points.",
        "Study Notes": "Convert this transcript into clean study notes with headers and bullet points.",
    }

    prompt = f"{style_prompts[style]}\n\nTranscript:\n{transcript[:8000]}"

    response = client.chat.completions.create(
     model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# UI
url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

style = st.selectbox("Summary Style", [
    "Quick (3 bullets)",
    "Detailed",
    "Study Notes"
])

if st.button("✨ Summarize", type="primary"):
    if not url:
        st.warning("Please paste a YouTube URL first.")
    else:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("Couldn't read that URL. Try copying it directly from YouTube.")
        else:
            with st.spinner("Fetching transcript..."):
                transcript = get_transcript(video_id)

            if not transcript:
                st.error("No transcript found. This video might not have captions enabled.")
            else:
                with st.spinner("Summarizing with AI..."):
                    result = summarize(transcript, style)

                if not result:
                    st.stop()

                st.success("Done!")
                st.markdown("### 📋 Summary")
                st.markdown(result)
                st.code(result, language=None)
                word_count = len(result.split())
                st.caption(f"Summary: {word_count} words from a full video transcript")
