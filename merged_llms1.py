import streamlit as st
import time
import re
from pypdf import PdfReader
from docx import Document
from openai import OpenAI
import google.generativeai as genai

# ==============================
# CONFIG & THEME
# ==============================
st.set_page_config(page_title="AI Resume Architect", layout="wide")

def get_score_color(score):
    if score < 50: return "#FF4B4B"  # Red
    elif score < 80: return "#FFA500" # Orange
    else: return "#28A745"           # Green

# ==============================
# SIDEBAR / PROVIDER
# ==============================
with st.sidebar:
    st.header("Settings")
    PROVIDER = st.selectbox(
        "🤖 Choose LLM Engine:",
        ["Step-3.5-Flash (StepFun - Recommended)", "Closed-source (Gemini)"]
    )

# ==============================
# CLIENT SETUP
# ==============================
if PROVIDER == "Step-3.5-Flash (StepFun - Recommended)":
    client = OpenAI(
        api_key=st.secrets["OPENROUTER_API_KEY"], 
        base_url="https://openrouter.ai/api/v1"
    )
    MODEL_NAME = "stepfun/step-3.5-flash:free"
else:
    # Your Gemini logic (gemini-3-flash)
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("gemini-3-flash")

# ==============================
# HELPERS
# ==============================
def extract_text(file):
    ext = file.name.split(".")[-1].lower()
    try:
        if ext == "pdf":
            return "\n".join(page.extract_text() for page in PdfReader(file).pages)
        elif ext == "docx":
            return "\n".join(p.text for p in Document(file).paragraphs)
        return file.read().decode("utf-8")
    except Exception as e:
        st.error(f"File reading error: {e}")
        return ""

def call_llm(system_task, user_content):
    scoring_instruction = "\n\nCRITICAL: You must begin your response with 'MATCH_SCORE: [number]' (0-100) based on how well the resume fits the job description, followed by your analysis."
    try:
        if "Step-3.5" in PROVIDER:
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
            r = gemini_model.generate_content(f"{system_task}{scoring_instruction}\n\
