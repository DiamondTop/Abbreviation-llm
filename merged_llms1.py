import streamlit as st
import time
from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup
from openai import OpenAI
import google.generativeai as genai

# ==============================
# PROVIDER SWITCH
# ==============================

PROVIDER = st.selectbox(
    "Choose LLM:",
    ["Open-source (Mistral)", "Closed-source (Gemini)"]
)

# ==============================
# CLIENT SETUP
# ==============================

if PROVIDER == "Open-source (Mistral)":
    client = OpenAI(
        api_key=st.secrets["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1"
    )
    MODEL_NAME = "mistralai/mistral-7b-instruct"
else:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# ==============================
# PROMPTS
# ==============================

CHAT_PROMPT = """
You are a helpful AI assistant.
Answer the user naturally and clearly.
"""

SUMMARY_PROMPT = """
You are summarizing an academic article.

Rules:
- Use ONLY information explicitly present in the text
- Do NOT add generic academic commentary
- Preserve technical terms and abbreviations
- If content is unclear, say so

Return a concise factual summary.
"""

QA_PROMP_
