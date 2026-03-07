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
    # ADDED Meta Llama TO THE LIST BELOW
    PROVIDER = st.selectbox(
        "🤖 Choose LLM Engine:",
        [
            "Step-3.5-Flash (StepFun - Recommended)", 
            "Meta Llama 3.3 70B (OpenRouter)", 
            "Closed-source (Gemini)"
        ]
    )

# ==============================
# CLIENT SETUP
# ==============================

# Create a mapping for OpenRouter models
model_map = {
    "Step-3.5-Flash (StepFun - Recommended)": "stepfun/step-3.5-flash:free",
    "Meta Llama 3.3 70B (OpenRouter)": "meta-llama/llama-3.3-70b-instruct:free"
}

if "Gemini" not in PROVIDER:
    client = OpenAI(
        api_key=st.secrets["OPENROUTER_API_KEY"], 
        base_url="https://openrouter.ai/api/v1"
    )
    # Set the MODEL_NAME based on the selection
    MODEL_NAME = model_map.get(PROVIDER)
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
        # UPDATED logic to handle all OpenRouter options
        if "Gemini" not in PROVIDER:
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
    job_desc = st.text_area("2. Target Job Description", height=200, placeholder="Paste requirements here...")

st.divider()

# PROMPT OPTIONS
prompt_options = {
    "ATS Keyword Optimization": "Analyze the Job Description for top keywords and modify my resume bullet points to include them naturally.",
    "STAR Method Bullet Point Rewrite": "Rewrite my work experience bullet points using the STAR method (Situation, Task, Action, Result). Focus on quantifiable achievements.",
    "Professional Summary Rewrite": "Draft a compelling 3-4 sentence professional summary that bridges my current experience with this specific job.",
    "Skills Gap Analysis": "Compare my resume against the job description. Identify exactly what hard and soft skills I am currently missing."
}

selected_strategy = st.selectbox("3. Choose a Goal:", list(prompt_options.keys()))
custom_instructions = st.text_area("Additional Instructions (Optional):", placeholder="e.g. 'Highlight my 10 years of experience in logistics'")

# ==============================
# EXECUTION
# ==============================
if st.button("🚀 Run Analysis", type="primary"):
    if not resume_file:
        st.warning("Please upload a resume first.")
    else:
        resume_text = extract_text(resume_file)
        system_task = prompt_options[selected_strategy]
        if custom_instructions:
            system_task += f" User note: {custom_instructions}"
            
        with st.spinner(f"Analyzing with {PROVIDER}..."):
            result = call_llm(system_task, f"JOB:\n{job_desc}\n\nRESUME:\n{resume_text}")
            
            if result:
                score_match = re.search(r"MATCH_SCORE:\s*(\d+)", result)
                if score_match:
                    score_val = int(score_match.group(1))
                    color = get_score_color(score_val)
                    
                    st.success("Analysis Complete!")
                    m_col1, m_col2 = st.columns([1, 4])
                    m_col1.metric("Match Score", f"{score_val}%")
                    
                    st.markdown(f"""<style>.stProgress > div > div > div > div {{ background-color: {color}; }}</style>""", unsafe_allow_html=True)
                    m_col2.write("###")
                    m_col2.progress(score_val / 100)
                    
                    display_text = result.replace(score_match.group(0), "").strip()
                else:
                    display_text = result
                
                st.divider()
                st.subheader("📋 Recommendations")
                st.markdown(display_text)
                st.download_button("💾 Download Edits", display_text, file_name="resume_analysis.txt")
