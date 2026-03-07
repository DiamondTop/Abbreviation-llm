import streamlit as st
import time
import re
from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup
from openai import OpenAI
import google.generativeai as genai

# ==============================
# PROVIDER SWITCH
# ==============================

st.set_page_config(page_title="AI Resume Architect", layout="wide")

# Function to determine color based on score
def get_score_color(score):
    if score < 50:
        return "#FF4B4B"  # Red
    elif score < 80:
        return "#FFA500"  # Orange
    else:
        return "#28A745"  # Green

with st.sidebar:
    st.header("Settings")
    PROVIDER = st.selectbox(
        "🤖 Choose LLM Engine:",
        ["Open-source (Meta-llama)", "Open-source (Gemma 2 27B)", "Closed-source (Gemini)"]
    )

# ==============================
# CLIENT SETUP
# ==============================

if PROVIDER == "Open-source (Meta-llama)":
    client = OpenAI(api_key=st.secrets["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1")
    MODEL_NAME = "meta-llama/llama-3-8b-instruct"
elif PROVIDER == "Open-source (Gemma 2 27B)":
    client = OpenAI(api_key=st.secrets["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1")
    MODEL_NAME = "google/gemma-2-27b-it:free"
else:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# ==============================
# HELPERS
# ==============================

def extract_text(file):
    ext = file.name.split(".")[-1].lower()
    if ext == "pdf":
        return "\n".join(page.extract_text() for page in PdfReader(file).pages)
    elif ext == "docx":
        return "\n".join(p.text for p in Document(file).paragraphs)
    return file.read().decode("utf-8")




def call_llm(system_prompt, user_content):
    scoring_instruction = "\n\nCRITICAL: You must begin your response with 'MATCH_SCORE: [number]' (0-100) based on how well the resume fits the job description, followed by your analysis."
    try:
        if "Open-source" in PROVIDER:
            r = client.chat.completions.create(
                model=MODEL_NAME, 
                temperature=0.4,
                messages=[
                    {"role": "system", "content": system_task + scoring_instruction}, 
                    {"role": "user", "content": user_content}
                ]
            )
            return r.choices[0].message.content.strip()
        else:
            # This handles your Gemini logic
            r = gemini_model.generate_content(f"{system_task}{scoring_instruction}\n\n{user_content}")
            return r.text.strip()
    except Exception as e:
        st.error(f"Error: {e}")
        return ""
