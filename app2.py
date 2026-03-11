import streamlit as st
import re
import requests
from PIL import Image
import pytesseract
from pypdf import PdfReader
from docx import Document
import pandas as pd
from openai import OpenAI
import google.generativeai as genai

# ==============================
# PAGE CONFIG & STYLES
# ==============================
st.set_page_config(
    page_title="Reasoning Forge",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean light theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg:          #f7f5f0;
    --bg2:         #ffffff;
    --bg3:         #edeae3;
    --gold:        #a0732a;
    --gold-light:  #c9a84c;
    --border:      rgba(160,115,42,0.25);
    --text:        #1a1612;
    --muted:       #6b6560;
    --serif:       'Cormorant Garamond', Georgia, serif;
    --sans:        'DM Sans', sans-serif;
    --mono:        'DM Mono', monospace;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}

[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

.stTextArea textarea {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
}

.stButton > button {
    background: var(--gold) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    width: 100%;
}

.reasoning-box {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 2rem;
    line-height: 1.85;
    white-space: pre-wrap;
    color: var(--text);
    position: relative;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

.reasoning-box::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, var(--gold), var(--gold-light), transparent);
}

.file-badge {
    display: block;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
    color
