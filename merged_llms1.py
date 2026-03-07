import streamlit as st
import time
import re
from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup
from openai import OpenAI
import google.generativeai as genai

# ==============================
# CONFIG & THEME
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

# ==============================
# SIDEBAR / PROVIDER
# ==============================
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
    #MODEL_NAME = "google/gemma-2-27b-it:free"
    #MODEL_NAME = "qwen/qwen-2.5-72b-instruct:free"
    MODEL_NAME = "deepseek/deepseek-chat:free"
else:
    # Gemini logic (Untouched)
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

def call_llm(system_task, user_content):
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
            r = gemini_model.generate_content(f"{system_task}{scoring_instruction}\n\n{user_content}")
            return r.text.strip()
    except Exception as e:
        st.error(f"LLM Error: {e}")
        return ""

# ==============================
# UI MAIN DISPLAY
# ==============================
st.title("💼 AI Resume Architect & Job Matcher")

col1, col2 = st.columns(2)
with col1:
    resume_file = st.file_uploader("1. Upload Resume", type=["pdf", "docx", "txt"])
with col2:
    job_desc = st.text_area("2. Target Job Description", height=200, placeholder="Paste the job requirements here...")

st.divider()

prompt_options = {
    "Skills Gap Analysis": "Compare my resume against the job description. Identify exactly what skills I am missing.",
    "ATS Keyword Optimization": "Analyze the Job Description for keywords and modify resume bullet points.",
    "Professional Summary Rewrite": "Draft a summary bridging current experience with this job."
}
selected_strategy = st.selectbox("3. Choose a Goal:", list(prompt_options.keys()))
custom_instructions = st.text_area("Additional Instructions (Optional):", placeholder="e.g. 'Focus on my 10 years of logistics experience'")

# ==============================
# EXECUTION LOGIC
# ==============================
if st.button("🚀 Run Analysis", type="primary"):
    if not resume_file:
        st.warning("Please upload a resume first.")
    else:
        resume_text = extract_text(resume_file)
        system_task = prompt_options[selected_strategy]
        if custom_instructions:
            system_task += f" User note: {custom_instructions}"
            
        with st.spinner("Analyzing resume against job requirements..."):
            result = call_llm(system_task, f"JOB DESCRIPTION:\n{job_desc}\n\nRESUME CONTENT:\n{resume_text}")
            
            if result:
                score_match = re.search(r"MATCH_SCORE:\s*(\d+)", result)
                
                if score_match:
                    score_val = int(score_match.group(1))
                    color = get_score_color(score_val)
                    
                    # Score Visualization
                    st.success("Analysis Complete!")
                    m_col1, m_col2 = st.columns([1, 4])
                    
                    m_col1.metric("Match Score", f"{score_val}%")
                    
                    # Use a unique key for the progress bar to prevent rendering issues
                    st.markdown(f"""
                        <style>
                        .stProgress > div > div > div > div {{ background-color: {color}; }}
                        </style>""", unsafe_allow_html=True)
                    m_col2.write("###")
                    m_col2.progress(score_val / 100)
                    
                    # Clean the output text
                    display_text = result.replace(score_match.group(0), "").strip()
                else:
                    display_text = result
                    st.info("Analysis finished (Score not detected).")

                st.divider()
                st.subheader("📋 AI Recommendations")
                st.markdown(display_text)
                
                st.download_button("💾 Download Edits", display_text, file_name="resume_analysis.txt")


