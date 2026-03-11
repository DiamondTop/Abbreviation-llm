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
    color: var(--gold);
    margin-bottom: 0.4rem;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# HELPERS
# ==============================
def extract_text(file) -> tuple[str, str]:
    ext = file.name.split(".")[-1].lower()
    try:
        if ext == "pdf":
            reader = PdfReader(file)
            return "\n".join(p.extract_text() or "" for p in reader.pages), "PDF"
        elif ext == "docx":
            doc = Document(file)
            return "\n".join(p.text for p in doc.paragraphs), "DOCX"
        elif ext in ["xlsx", "xls"]:
            xls = pd.ExcelFile(file)
            sheets = []
            for name in xls.sheet_names:
                df = xls.parse(name).dropna(how="all").fillna("")
                sheets.append(f"[Sheet: {name}]\n{df.to_markdown(index=False)}")
            return "\n\n".join(sheets), "Excel"
        elif ext == "csv":
            return pd.read_csv(file).fillna("").to_markdown(index=False), "CSV"
        elif ext in ["png", "jpg", "jpeg"]:
            return pytesseract.image_to_string(Image.open(file)), "Image (OCR)"
        else:
            return file.read().decode("utf-8"), "Text"
    except Exception as e:
        return f"Error: {e}", "Unknown"

def get_llm_response(prompt, provider):
    try:
        if "Metal-llama" in provider:
            client = OpenAI(api_key=st.secrets["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1")
            response = client.chat.completions.create(model="meta-llama/llama-3.1-8b-instruct", messages=[{"role": "user", "content": prompt}])
            return response.choices[0].message.content
        elif "OpenAI" in provider:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(model="o1-mini", messages=[{"role": "user", "content": prompt}])
            return response.choices[0].message.content
        elif "Gemini" in provider:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel("gemini-2.0-flash")
            return model.generate_content(prompt).text
    except Exception as e:
        return f"Error: {str(e)}"

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("### ✦ Settings")
    PROVIDER = st.selectbox("Reasoning Engine", ["Metal-llama (Reasoning Expert)", "OpenAI o1-mini (Logic Focused)", "Gemini 2.0 Flash"])
    st.markdown("---")
    st.markdown("**Attach Context Files**")
    uploaded_files = st.file_uploader("Upload files", type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "xlsx", "xls", "csv"], accept_multiple_files=True, label_visibility="collapsed")
    
    if uploaded_files:
        for f in uploaded_files:
            st.markdown(f"<span class='file-badge'>📎 {f.name}</span>", unsafe_allow_html=True)

# ==============================
# MAIN INTERFACE
# ==============================
st.markdown("<h1 style='font-family:Cormorant Garamond; font-size:3.5rem; font-weight:300;'>Reasoning <em style='color:#a0732a; font-style:italic;'>Forge</em></h1>", unsafe_allow_html=True)

user_query = st.text_area("Define your problem:", height=200, placeholder="Ask a question about the uploaded files...")

if st.button("✦ Start Reasoning"):
    if not user_query:
        st.warning("Please enter a question.")
    else:
        combined_context = ""
        if uploaded_files:
            with st.spinner(f"Extracting data from {len(uploaded_files)} files..."):
                for f in uploaded_files:
                    f.seek(0)
                    text, ftype = extract_text(f)
                    combined_context += f"\n\n--- FILE: {f.name} ({ftype}) ---\n{text}\n"
        
        final_prompt = f"CONTEXT:\n{combined_context}\n\nUSER QUESTION:\n{user_query}" if combined_context else user_query

        with st.spinner(f"{PROVIDER} is thinking..."):
            answer = get_llm_response(final_prompt, PROVIDER)
            st.markdown("---")
            if "<think>" in answer:
                parts = answer.split("</think>")
                st.expander("View Reasoning Process", expanded=True).markdown(f"*{parts[0].replace('<think>', '').strip()}*")
                st.markdown(f"<div class='reasoning-box'>{parts[1].strip()}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='reasoning-box'>{answer}</div>", unsafe_allow_html=True)
