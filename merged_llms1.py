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

st.set_page_config(page_title="AI Resume Intelligence", layout="wide")

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
    client = OpenAI(
        api_key=st.secrets["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1"
    )
    MODEL_NAME = "meta-llama/llama-3-8b-instruct"

elif PROVIDER == "Open-source (Gemma 2 27B)":
    client = OpenAI(
        api_key=st.secrets["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1"
    )
    MODEL_NAME = "google/gemma-2-27b-it:free"

else:
    # Use your existing Gemini config
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# ==============================
# DOCUMENT EXTRACTION
# ==============================

def extract_text(file):
    ext = file.name.split(".")[-1].lower()
    if ext == "pdf":
        reader = PdfReader(file)
        return "\n".join(page.extract_text() for page in reader.pages)
    elif ext == "docx":
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs)
    elif ext == "txt":
        return file.read().decode("utf-8")
    return ""

# ==============================
# LLM CALL
# ==============================

def call_llm(system_prompt, user_content):
    try:
        if "Open-source" in PROVIDER:
            r = client.chat.completions.create(
                model=MODEL_NAME,
                temperature=0.4,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            return r.choices[0].message.content.strip()
        else:
            r = gemini_model.generate_content(f"{system_prompt}\n\n{user_content}")
            return r.text.strip()
    except Exception as e:
        st.error(f"Error: {e}")
        return ""

# ==============================
# STREAMLIT UI
# ==============================

st.title("💼 AI Resume Architect & Job Matcher")
st.markdown("Tailor your resume, optimize for ATS, and improve your professional narrative.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Upload Resume")
    resume_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx", "txt"])
    
with col2:
    st.subheader("2. Target Job Description")
    job_desc = st.text_area("Paste the job posting here...", height=200)

st.divider()

st.subheader("3. Select Your Strategy")
prompt_options = {
    "ATS Keyword Optimization": "Analyze the Job Description for top keywords and modify my resume bullet points to include them naturally while maintaining truthfulness.",
    "STAR Method Bullet Point Rewrite": "Rewrite my work experience bullet points using the STAR method (Situation, Task, Action, Result). Focus on quantifiable achievements and metrics.",
    "Professional Summary Rewrite": "Draft a compelling 3-4 sentence professional summary that bridges my current experience with the requirements of this specific job.",
    "Skills Gap Analysis": "Compare my resume against the job description. Identify exactly what skills I am missing and suggest how I can reframe my existing experience to fill those gaps."
}

selected_strategy = st.selectbox("Choose a goal:", list(prompt_options.keys()))
custom_instructions = st.text_area("Additional custom instructions (optional):", 
                                  placeholder="e.g., 'Make it sound more executive' or 'Highlight my logistics background'")

# ==============================
# MAIN LOGIC
# ==============================

if st.button("🚀 Run Analysis", type="primary"):
    if not resume_file:
        st.warning("Please upload a resume first.")
    else:
        resume_text = extract_text(resume_file)
        
        # Build the final prompt context
        system_task = prompt_options[selected_strategy]
        if custom_instructions:
            system_task += f" Additional requirements: {custom_instructions}"
            
        full_user_input = f"""
        TARGET JOB DESCRIPTION:
        {job_desc if job_desc else 'No job description provided.'}
        
        MY CURRENT RESUME:
        {resume_text}
        """
        
        with st.spinner(f"Analyzing with {PROVIDER}..."):
            result = call_llm(system_task, full_user_input)
            
            if result:
                st.success("Analysis Complete!")
                st.markdown("### 📋 Recommendations & Edits")
                st.markdown(result)
                
                # Option to download the advice
                st.download_button("Download Advice as Text", result, file_name="resume_edits.txt")

# ==============================
# CHAT-ONLY (IF NO UPLOAD)
# ==============================
if not resume_file:
    st.info("💡 Pro-Tip: Once you upload a resume, I can provide specific rewrites. For now, you can ask general career questions in the sidebar settings.")
