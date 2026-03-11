import streamlit as st
import re
from pypdf import PdfReader
from docx import Document
from openai import OpenAI
import google.generativeai as genai

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="ResumeForge — AI Resume Architect",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# GLOBAL STYLES
# ==============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg:         #0b0c0f;
    --bg2:        #111318;
    --bg3:        #1c1f28;
    --gold:       #c9a84c;
    --gold-light: #e8c87a;
    --gold-dim:   rgba(201,168,76,0.12);
    --border:     rgba(201,168,76,0.22);
    --text:       #f0ede6;
    --muted:      #9a958f;
    --placeholder:#7a7570;
    --serif:      'Cormorant Garamond', Georgia, serif;
    --sans:       'DM Sans', sans-serif;
    --mono:       'DM Mono', monospace;
}

/* ── KILL WHITE HEADER BAR ── */
header[data-testid="stHeader"] {
    background: var(--bg) !important;
    border-bottom: 1px solid var(--border) !important;
}
[data-testid="stToolbar"]               { display: none !important; }
[data-testid="collapsedControl"]        { display: none !important; }
button[kind="header"]                   { display: none !important; }
[data-testid="stSidebarCollapseButton"] svg { display: none !important; }
[data-testid="stSidebarCollapseButton"] {
    background: transparent !important;
    border: none !important;
}

/* ── GLOBAL BACKGROUND ── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
.stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-weight: 300;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text) !important;
    font-family: var(--sans) !important;
}

/* ── MAIN PADDING ── */
[data-testid="stMainBlockContainer"] {
    padding-top: 0.5rem !important;
    padding-bottom: 4rem !important;
}

/* ── HEADINGS ── */
h1, h2, h3, h4 {
    font-family: var(--serif) !important;
    font-weight: 300 !important;
}

/* ── TEXTAREA ── */
.stTextArea textarea {
    background: var(--bg2) !important;
    border: 1px solid rgba(201,168,76,0.18) !important;
    border-radius: 4px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 0.92rem !important;
    line-height: 1.75 !important;
    padding: 0.9rem 1rem !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
    outline: none !important;
    box-shadow: none !important;
}
.stTextArea textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px rgba(201,168,76,0.12) !important;
}
.stTextArea textarea::placeholder               { color: var(--placeholder) !important; opacity: 1 !important; }
.stTextArea textarea::-webkit-input-placeholder { color: var(--placeholder) !important; opacity: 1 !important; }
.stTextArea textarea::-moz-placeholder          { color: var(--placeholder) !important; opacity: 1 !important; }
.stTextArea textarea:-ms-input-placeholder      { color: var(--placeholder) !important; opacity: 1 !important; }

.stTextArea label,
[data-testid="stWidgetLabel"] p {
    font-family: var(--mono) !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: var(--gold) !important;
    margin-bottom: 0.4rem !important;
    font-weight: 400 !important;
}

/* ── SELECTBOX ── */
.stSelectbox > div > div {
    background: var(--bg2) !important;
    border: 1px solid rgba(201,168,76,0.18) !important;
    border-radius: 4px !important;
    color: var(--text) !important;
}
.stSelectbox > div > div:hover,
.stSelectbox > div > div:focus-within { border-color: var(--gold) !important; }
[data-testid="stSelectbox"] svg { color: var(--gold) !important; }
div[data-baseweb="popover"] { background: var(--bg2) !important; border: 1px solid var(--border) !important; }
div[data-baseweb="option"]  { background: var(--bg2) !important; color: var(--text) !important; }
div[data-baseweb="option"]:hover { background: var(--bg3) !important; color: var(--gold) !important; }

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background: var(--bg2) !important;
    border: 1px dashed rgba(201,168,76,0.25) !important;
    border-radius: 4px !important;
    padding: 0.5rem !important;
}
[data-testid="stFileUploader"]:hover { border-color: rgba(201,168,76,0.5) !important; }
[data-testid="stFileUploader"] section { background: transparent !important; border: none !important; }
[data-testid="stFileUploaderDropzoneInstructions"] > div > span  { color: var(--muted) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] > div > small { color: var(--placeholder) !important; }
[data-testid="stFileUploader"] button {
    background: transparent !important;
    color: var(--gold) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    font-family: var(--mono) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    transition: all 0.2s !important;
}
[data-testid="stFileUploader"] button:hover {
    border-color: var(--gold) !important;
    background: var(--gold-dim) !important;
}
[data-testid="stFileUploader"] label {
    font-family: var(--mono) !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: var(--gold) !important;
}

/* ── MAIN BUTTON ── */
.stButton > button {
    background: var(--gold) !important;
    color: #0b0c0f !important;
    border: 1px solid var(--gold) !important;
    border-radius: 3px !important;
    font-family: var(--sans) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 0.7rem 2.2rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: transparent !important;
    color: var(--gold) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 30px rgba(201,168,76,0.2) !important;
}

/* ── DOWNLOAD BUTTON ── */
.stDownloadButton > button {
    background: transparent !important;
    color: var(--gold) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
    border-color: var(--gold) !important;
    background: var(--gold-dim) !important;
}

/* ── DIVIDER ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 2rem 0 !important;
}

/* ── METRIC ── */
[data-testid="stMetric"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    padding: 1.2rem 1.5rem !important;
}
[data-testid="stMetricLabel"] p {
    font-family: var(--mono) !important;
    font-size: 0.62rem !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--serif) !important;
    font-size: 2.8rem !important;
    font-weight: 300 !important;
    color: var(--gold) !important;
    line-height: 1.1 !important;
}
[data-testid="stMetricDelta"] { color: #28A745 !important; font-size: 0.78rem !important; }

/* ── SPINNER ── */
.stSpinner > div { border-top-color: var(--gold) !important; }

/* ── ALERTS ── */
.stAlert {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    color: var(--text) !important;
}

/* ── MARKDOWN OUTPUT ── */
.stMarkdown p, .stMarkdown li {
    color: var(--text) !important;
    line-height: 1.85 !important;
    font-size: 0.95rem !important;
}
.stMarkdown h3 {
    font-family: var(--serif) !important;
    color: var(--gold) !important;
    font-size: 1.4rem !important;
    margin-top: 1.5rem !important;
    font-weight: 300 !important;
}
.stMarkdown strong { color: var(--gold-light) !important; font-weight: 500 !important; }
.stMarkdown code {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    color: var(--gold) !important;
    font-family: var(--mono) !important;
    font-size: 0.82rem !important;
    padding: 0.15rem 0.45rem !important;
}

/* ── COVER LETTER PANEL ── */
.cover-letter-box {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 2rem 2.2rem;
    line-height: 1.9;
    font-size: 0.95rem;
    color: var(--text);
    white-space: pre-wrap;
    font-family: var(--sans);
    position: relative;
}
.cover-letter-box::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--gold), transparent);
    border-radius: 6px 6px 0 0;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold); }
</style>
""", unsafe_allow_html=True)


# ==============================
# HERO HEADER
# ==============================
st.markdown("""
<div style="padding: 2.5rem 0 1.8rem; position: relative; overflow: hidden;">
    <div style="
        position: absolute; inset: 0;
        background-image:
            linear-gradient(rgba(201,168,76,0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(201,168,76,0.035) 1px, transparent 1px);
        background-size: 52px 52px; pointer-events: none;
    "></div>
    <div style="position:relative; z-index:1;">
        <div style="font-family:'DM Mono',monospace; font-size:0.65rem; letter-spacing:0.24em;
                    text-transform:uppercase; color:#c9a84c; margin-bottom:0.9rem;
                    display:flex; align-items:center; gap:0.7rem;">
            <span style="display:inline-block; width:26px; height:1px; background:#c9a84c;"></span>
            AI-Powered · Job-Specific · Interview-Ready
        </div>
        <h1 style="font-family:'Cormorant Garamond',Georgia,serif;
                   font-size:clamp(2.6rem,5.5vw,4.6rem); font-weight:300;
                   line-height:1.05; color:#f0ede6; margin-bottom:0.7rem; letter-spacing:-0.01em;">
            Resume<em style="color:#c9a84c; font-style:italic;">Forge</em>
        </h1>
        <p style="font-family:'DM Sans',sans-serif; font-size:0.98rem; color:#9a958f;
                  font-weight:300; max-width:500px; line-height:1.75; margin:0;">
            Paste a job description, upload your resume — and let AI sculpt
            a response precisely tuned to land you the interview.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)


# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("""
    <div style="padding:1.2rem 0 1rem;">
        <div style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.22em;
                    text-transform:uppercase; color:#c9a84c; margin-bottom:0.35rem;">✦ ResumeForge</div>
        <div style="font-family:'Cormorant Garamond',serif; font-size:1.35rem;
                    font-weight:300; color:#f0ede6; margin-bottom:0.25rem;">Settings</div>
        <div style="height:1px; background:rgba(201,168,76,0.2); margin-bottom:1.4rem;"></div>
    </div>
    """, unsafe_allow_html=True)

    PROVIDER = st.selectbox(
        "LLM Engine",
        [
            "Step-3.5-Flash (StepFun · Recommended)",
            "Meta Llama via Meta/Facebook",
            "Closed-source (Gemini) via Google"
        ]
    )

    st.markdown("""
    <div style="margin-top:1.8rem; padding:1.2rem; background:#0b0c0f;
                border:1px solid rgba(201,168,76,0.18); border-radius:4px;">
        <div style="font-family:'DM Mono',monospace; font-size:0.6rem; letter-spacing:0.18em;
                    text-transform:uppercase; color:#c9a84c; margin-bottom:0.8rem;">How it works</div>
        <div style="font-size:0.8rem; color:#9a958f; line-height:1.8;">
            <div style="margin-bottom:0.4rem;">① Upload your resume</div>
            <div style="margin-bottom:0.4rem;">② Paste the job description</div>
            <div style="margin-bottom:0.4rem;">③ Choose your goal</div>
            <div>④ Run analysis → download</div>
        </div>
    </div>
    <div style="margin-top:1.2rem; padding:1rem; background:rgba(201,168,76,0.06);
                border:1px solid rgba(201,168,76,0.15); border-radius:4px;">
        <div style="font-size:0.78rem; color:#9a958f; line-height:1.8;">
            <span style="color:#c9a84c;">✦</span> Your files are never stored.<br/>
            <span style="color:#c9a84c;">✦</span> Analysis runs in real-time.<br/>
            <span style="color:#c9a84c;">✦</span> Cover letter auto-generated on ATS runs.<br/>
            <span style="color:#c9a84c;">✦</span> Download your edits instantly.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==============================
# CLIENT SETUP
# ==============================
model_map = {
    "Step-3.5-Flash (StepFun · Recommended)": "stepfun/step-3.5-flash:free",
    "Meta Llama via Meta/Facebook":            "meta-llama/llama-3-8b-instruct",
}

if "Gemini" not in PROVIDER:
    client = OpenAI(
        api_key=st.secrets["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1"
    )
    MODEL_NAME = model_map.get(PROVIDER)
else:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")


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


def call_llm(system_task, user_content, add_score=True):
    """Call the configured LLM. Set add_score=False for cover letter generation."""
    scoring_instruction = (
        "\n\nCRITICAL: Begin your response with 'MATCH_SCORE: [number]' (0–100) "
        "based on how well the resume fits the job description, followed by your analysis."
    ) if add_score else ""

    try:
        if "Gemini" not in PROVIDER:
            r = client.chat.completions.create(
                model=MODEL_NAME,
                temperature=0.4,
                messages=[
                    {"role": "system", "content": system_task + scoring_instruction},
                    {"role": "user",   "content": user_content}
                ]
            )
            return r.choices[0].message.content.strip()
        else:
            r = gemini_model.generate_content(
                f"{system_task}{scoring_instruction}\n\n{user_content}"
            )
            return r.text.strip()
    except Exception as e:
        st.error(f"LLM Error: {e}")
        return ""


def generate_cover_letter(job_desc, resume_text):
    """Dedicated cover letter prompt — no score prefix needed."""
    system_task = """You are an expert career coach and professional writer.
Write a compelling, personalized cover letter based on the candidate's resume and the job description provided.

The cover letter must:
- Be 3–4 paragraphs, professional but warm in tone
- Open with a strong hook that references the specific role and company
- Highlight 2–3 of the candidate's most relevant experiences from their resume that directly match the job requirements
- Include at least one quantified achievement from the resume
- Close with a confident call to action
- NOT use generic filler phrases like "I am writing to express my interest..." or "I am a hard worker"
- Sound like a real human wrote it, not a template

Output ONLY the cover letter text — no subject lines, no labels, no preamble. Start directly with "Dear Hiring Manager," or a named salutation if the name is available."""

    return call_llm(system_task, f"JOB DESCRIPTION:\n{job_desc}\n\nRESUME:\n{resume_text}", add_score=False)


def get_score_color(score):
    if score < 50:  return "#FF4B4B"
    elif score < 80: return "#FFA500"
    else:            return "#28A745"


# ==============================
# STEP INDICATOR
# ==============================
st.markdown("""
<div style="display:flex; gap:1.2rem; align-items:center; margin-bottom:1.6rem; flex-wrap:wrap;">
    <span style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.16em; text-transform:uppercase; color:#c9a84c;">① Upload Resume</span>
    <span style="color:rgba(201,168,76,0.2);">────</span>
    <span style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.16em; text-transform:uppercase; color:#c9a84c;">② Job Description</span>
    <span style="color:rgba(201,168,76,0.2);">────</span>
    <span style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.16em; text-transform:uppercase; color:#c9a84c;">③ Choose Goal</span>
    <span style="color:rgba(201,168,76,0.2);">────</span>
    <span style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.16em; text-transform:uppercase; color:#c9a84c;">④ Run</span>
</div>
""", unsafe_allow_html=True)


# ==============================
# INPUTS
# ==============================
col1, col2 = st.columns(2, gap="large")
with col1:
    resume_file = st.file_uploader(
        "Upload Resume",
        type=["pdf", "docx", "txt"],
        help="Your file is processed in memory and never stored."
    )
with col2:
    job_desc = st.text_area(
        "Target Job Description",
        height=200,
        placeholder="Paste the full job posting here — requirements, responsibilities, everything..."
    )

st.markdown("<hr/>", unsafe_allow_html=True)

# ==============================
# GOAL + INSTRUCTIONS
# ==============================
prompt_options = {
    "✦  ATS Keyword Optimization":     "Analyze the Job Description for top keywords and modify my resume bullet points to include them naturally.",
    "✦  STAR Method Bullet Rewrite":   "Rewrite my work experience bullet points using the STAR method (Situation, Task, Action, Result). Focus on quantifiable achievements.",
    "✦  Professional Summary Rewrite": "Draft a compelling 3–4 sentence professional summary that bridges my current experience with this specific job.",
    "✦  Skills Gap Analysis":          "Compare my resume against the job description. Identify exactly what hard and soft skills I am currently missing.",
}

col3, col4 = st.columns([1.2, 1], gap="large")
with col3:
    selected_strategy = st.selectbox("Choose Your Goal", list(prompt_options.keys()))
with col4:
    custom_instructions = st.text_area(
        "Additional Instructions (Optional)",
        height=110,
        placeholder="e.g. 'Highlight my 10 years of experience in logistics'"
    )

st.markdown("<br/>", unsafe_allow_html=True)

# ── ATS badge hint
is_ats = "ATS" in selected_strategy
if is_ats:
    st.markdown("""
    <div style="display:inline-flex; align-items:center; gap:0.6rem;
                background:rgba(201,168,76,0.07); border:1px solid rgba(201,168,76,0.2);
                border-radius:20px; padding:0.35rem 0.9rem; margin-bottom:1rem;">
        <span style="color:#c9a84c; font-size:0.75rem;">✦</span>
        <span style="font-family:'DM Mono',monospace; font-size:0.65rem; letter-spacing:0.12em;
                     text-transform:uppercase; color:#9a958f;">
            A tailored cover letter will be generated automatically after this analysis
        </span>
    </div>
    """, unsafe_allow_html=True)

col_btn, _ = st.columns([1, 5])
with col_btn:
    run = st.button("✦  Run Analysis", type="primary")

st.markdown("<hr/>", unsafe_allow_html=True)


# ==============================
# RESULTS
# ==============================
if run:
    if not resume_file:
        st.warning("⚠  Please upload a resume to get started.")
    elif not job_desc.strip():
        st.warning("⚠  Please paste a job description to match against.")
    else:
        resume_text = extract_text(resume_file)
        system_task = prompt_options[selected_strategy]
        if custom_instructions:
            system_task += f"  Additional user context: {custom_instructions}"

        # ── Run main analysis
        with st.spinner("Analyzing your resume against the role..."):
            result = call_llm(
                system_task,
                f"JOB DESCRIPTION:\n{job_desc}\n\nRESUME:\n{resume_text}"
            )

        # ── Run cover letter if ATS selected
        cover_letter_text = ""
        if is_ats and result:
            with st.spinner("Generating your tailored cover letter..."):
                cover_letter_text = generate_cover_letter(job_desc, resume_text)

        if result:
            score_match = re.search(r"MATCH_SCORE:\s*(\d+)", result)

            if score_match:
                score_val    = int(score_match.group(1))
                color        = get_score_color(score_val)
                display_text = result.replace(score_match.group(0), "").strip()
                score_label  = (
                    "Strong Match" if score_val >= 80
                    else "Partial Match" if score_val >= 50
                    else "Needs Work"
                )

                # Success banner
                st.markdown(f"""
                <div style="padding:0.85rem 1.3rem; background:rgba(40,167,69,0.07);
                            border:1px solid rgba(40,167,69,0.28); border-radius:3px;
                            margin-bottom:1.4rem; font-family:'DM Mono',monospace;
                            font-size:0.68rem; letter-spacing:0.14em; text-transform:uppercase;
                            color:#28A745;">
                    ✓ &nbsp; Analysis complete · {PROVIDER.split('(')[0].strip()}
                </div>
                """, unsafe_allow_html=True)

                # Score row
                m1, m2 = st.columns([1, 3], gap="large")
                with m1:
                    st.metric("Match Score", f"{score_val}%", delta=score_label)
                with m2:
                    st.markdown(f"""
                    <div style="margin-top:1.1rem;">
                        <div style="font-family:'DM Mono',monospace; font-size:0.6rem;
                                    letter-spacing:0.16em; text-transform:uppercase;
                                    color:#9a958f; margin-bottom:0.55rem;">
                            Resume – Job Alignment
                        </div>
                        <div style="height:7px; background:#1c1f28; border-radius:3px; overflow:hidden;">
                            <div style="height:100%; width:{score_val}%; background:{color}; border-radius:3px;"></div>
                        </div>
                        <div style="display:flex; justify-content:space-between;
                                    font-size:0.6rem; color:#4a4845;
                                    font-family:'DM Mono',monospace; margin-top:0.35rem;">
                            <span>0%</span><span>50%</span><span>100%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                display_text = result

            st.markdown("<hr/>", unsafe_allow_html=True)

            # ── Analysis results header
            st.markdown(f"""
            <div style="margin-bottom:1.1rem;">
                <div style="font-family:'DM Mono',monospace; font-size:0.62rem;
                            letter-spacing:0.2em; text-transform:uppercase; color:#c9a84c;
                            margin-bottom:0.35rem; display:flex; align-items:center; gap:0.6rem;">
                    <span style="display:inline-block;width:18px;height:1px;background:#c9a84c;"></span>
                    Results
                </div>
                <div style="font-family:'Cormorant Garamond',serif; font-size:1.75rem;
                            font-weight:300; color:#f0ede6;">
                    {selected_strategy.replace("✦  ", "")}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(display_text)
            st.markdown("<br/>", unsafe_allow_html=True)

            # ── Download analysis
            dcol1, _ = st.columns([1, 4])
            with dcol1:
                st.download_button(
                    "↓  Download Analysis",
                    data=display_text,
                    file_name="resume_analysis.txt",
                    mime="text/plain"
                )

            # ══════════════════════════════════════════
            # COVER LETTER SECTION (ATS only)
            # ══════════════════════════════════════════
            if is_ats and cover_letter_text:
                st.markdown("<hr/>", unsafe_allow_html=True)

                # Section header
                st.markdown("""
                <div style="margin-bottom:1.4rem;">
                    <div style="font-family:'DM Mono',monospace; font-size:0.62rem;
                                letter-spacing:0.2em; text-transform:uppercase; color:#c9a84c;
                                margin-bottom:0.35rem; display:flex; align-items:center; gap:0.6rem;">
                        <span style="display:inline-block;width:18px;height:1px;background:#c9a84c;"></span>
                        Bonus
                    </div>
                    <div style="font-family:'Cormorant Garamond',serif; font-size:1.75rem;
                                font-weight:300; color:#f0ede6; margin-bottom:0.4rem;">
                        Your Tailored Cover Letter
                    </div>
                    <p style="font-family:'DM Sans',sans-serif; font-size:0.85rem;
                              color:#9a958f; font-weight:300; max-width:560px; line-height:1.7; margin:0;">
                        Written specifically for this role using your resume and the job description.
                        Edit freely before sending — this is your starting point, not your final draft.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # Cover letter display box
                st.markdown(f"""
                <div class="cover-letter-box">{cover_letter_text}</div>
                """, unsafe_allow_html=True)

                st.markdown("<br/>", unsafe_allow_html=True)

                # Download buttons — side by side
                cl_col1, cl_col2, _ = st.columns([1, 1, 3])
                with cl_col1:
                    st.download_button(
                        "↓  Download Cover Letter (.txt)",
                        data=cover_letter_text,
                        file_name="cover_letter.txt",
                        mime="text/plain",
                        key="dl_cover_txt"
                    )
                with cl_col2:
                    # Also offer as .docx-friendly plain text with proper line breaks
                    formatted = cover_letter_text.replace("\n", "\r\n")
                    st.download_button(
                        "↓  Download as .doc",
                        data=formatted,
                        file_name="cover_letter.doc",
                        mime="application/msword",
                        key="dl_cover_doc"
                    )

                # Tip callout
                st.markdown("""
                <div style="margin-top:1rem; padding:0.9rem 1.2rem;
                            background:rgba(201,168,76,0.05);
                            border-left:2px solid rgba(201,168,76,0.4);
                            border-radius:0 4px 4px 0;">
                    <span style="font-family:'DM Mono',monospace; font-size:0.62rem;
                                 letter-spacing:0.14em; text-transform:uppercase; color:#c9a84c;">
                        ✦ Tip
                    </span>
                    <p style="font-family:'DM Sans',sans-serif; font-size:0.82rem;
                              color:#9a958f; margin:0.3rem 0 0; line-height:1.7;">
                        Personalise the opening line with the hiring manager's name if you can find it on LinkedIn.
                        A named salutation increases open rates by up to 20%.
                    </p>
                </div>
                """, unsafe_allow_html=True)
