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
# GLOBAL STYLES — Dark Gold Editorial Theme
# ==============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ── ROOT VARIABLES ── */
:root {
    --bg:        #0b0c0f;
    --bg2:       #111318;
    --bg3:       #181a21;
    --gold:      #c9a84c;
    --gold-light:#e8c87a;
    --gold-dim:  rgba(201,168,76,0.12);
    --border:    rgba(201,168,76,0.18);
    --text:      #f0ede6;
    --muted:     #8a8680;
    --serif:     'Cormorant Garamond', Georgia, serif;
    --sans:      'DM Sans', sans-serif;
    --mono:      'DM Mono', monospace;
}

/* ── GLOBAL RESET ── */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-weight: 300;
}

/* noise texture overlay */
.stApp::before {
    content: '';
    position: fixed; inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
    opacity: 0.4;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; font-family: var(--sans) !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] h2 {
    font-family: var(--mono) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: var(--gold) !important;
}

/* ── MAIN CONTENT AREA ── */
[data-testid="stMainBlockContainer"] {
    padding-top: 1rem !important;
    padding-bottom: 4rem !important;
}

/* ── HEADINGS ── */
h1, h2, h3, h4 {
    font-family: var(--serif) !important;
    font-weight: 300 !important;
    letter-spacing: -0.01em !important;
}

/* ── SELECTBOX ── */
.stSelectbox > div > div {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    color: var(--text) !important;
}
.stSelectbox > div > div:hover { border-color: var(--gold) !important; }
[data-testid="stSelectbox"] svg { color: var(--gold) !important; }
div[data-baseweb="popover"] { background: var(--bg2) !important; border: 1px solid var(--border) !important; }
div[data-baseweb="option"] { background: var(--bg2) !important; color: var(--text) !important; }
div[data-baseweb="option"]:hover { background: var(--bg3) !important; color: var(--gold) !important; }

/* ── TEXTAREA ── */
.stTextArea textarea {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 0.9rem !important;
    line-height: 1.7 !important;
    padding: 1rem !important;
    transition: border-color 0.2s !important;
}
.stTextArea textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px rgba(201,168,76,0.1) !important;
    outline: none !important;
}
.stTextArea label {
    font-family: var(--mono) !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: var(--gold) !important;
    margin-bottom: 0.4rem !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background: var(--bg2) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 3px !important;
    padding: 1rem !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--gold) !important; }
[data-testid="stFileUploader"] label {
    font-family: var(--mono) !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: var(--gold) !important;
}
[data-testid="stFileUploader"] section {
    background: transparent !important;
    border: none !important;
}
[data-testid="stFileUploader"] p { color: var(--muted) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] { color: var(--muted) !important; }

/* ── PRIMARY BUTTON ── */
.stButton > button[kind="primary"],
.stButton > button {
    background: var(--gold) !important;
    color: #0b0c0f !important;
    border: 1px solid var(--gold) !important;
    border-radius: 2px !important;
    font-family: var(--sans) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 0.65rem 2rem !important;
    transition: all 0.2s ease !important;
    width: auto !important;
}
.stButton > button:hover {
    background: transparent !important;
    color: var(--gold) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 30px rgba(201,168,76,0.18) !important;
}

/* ── DOWNLOAD BUTTON ── */
.stDownloadButton > button {
    background: transparent !important;
    color: var(--gold) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    font-family: var(--sans) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
    border-color: var(--gold) !important;
    box-shadow: 0 4px 20px rgba(201,168,76,0.12) !important;
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
[data-testid="stMetricLabel"] {
    font-family: var(--mono) !important;
    font-size: 0.65rem !important;
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

/* ── PROGRESS BAR ── */
.stProgress > div > div { background: var(--bg3) !important; border-radius: 2px !important; }
.stProgress > div > div > div { border-radius: 2px !important; transition: width 0.8s ease !important; }

/* ── ALERTS / WARNINGS ── */
.stAlert {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    color: var(--text) !important;
}

/* ── SPINNER ── */
.stSpinner > div { border-top-color: var(--gold) !important; }

/* ── COLUMNS ── */
[data-testid="stHorizontalBlock"] { gap: 1.5rem !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold); }

/* ── MARKDOWN OUTPUT ── */
.stMarkdown p, .stMarkdown li {
    color: var(--text) !important;
    line-height: 1.8 !important;
    font-size: 0.95rem !important;
}
.stMarkdown h3 {
    font-family: var(--serif) !important;
    color: var(--gold) !important;
    font-size: 1.4rem !important;
    margin-top: 1.5rem !important;
}
.stMarkdown strong { color: var(--gold-light) !important; font-weight: 500 !important; }
.stMarkdown code {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    color: var(--gold) !important;
    font-family: var(--mono) !important;
    font-size: 0.82rem !important;
    padding: 0.1rem 0.4rem !important;
}

/* ── SUCCESS BOX ── */
.stSuccess {
    background: rgba(40,167,69,0.08) !important;
    border: 1px solid rgba(40,167,69,0.3) !important;
    border-radius: 3px !important;
}
</style>
""", unsafe_allow_html=True)


# ==============================
# HERO HEADER
# ==============================
st.markdown("""
<div style="padding: 3rem 0 2rem; position: relative; overflow: hidden;">
    <!-- Subtle grid background -->
    <div style="
        position: absolute; inset: 0;
        background-image: linear-gradient(rgba(201,168,76,0.04) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(201,168,76,0.04) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
    "></div>
    <!-- Tag line -->
    <div style="
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: #c9a84c;
        margin-bottom: 1rem;
        display: flex; align-items: center; gap: 0.7rem;
    ">
        <span style="display:inline-block; width:28px; height:1px; background:#c9a84c;"></span>
        AI-Powered · Job-Specific · Interview-Ready
    </div>
    <!-- Main title -->
    <h1 style="
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        font-size: clamp(2.8rem, 6vw, 5rem) !important;
        font-weight: 300 !important;
        line-height: 1.05 !important;
        color: #f0ede6 !important;
        margin-bottom: 0.6rem !important;
    ">
        Resume<em style="color:#c9a84c; font-style:italic;">Forge</em>
    </h1>
    <!-- Subtitle -->
    <p style="
        font-family: 'DM Sans', sans-serif;
        font-size: 1rem;
        color: #8a8680;
        font-weight: 300;
        max-width: 520px;
        line-height: 1.7;
        margin: 0;
    ">
        Paste a job description, upload your resume — and let AI sculpt a response
        precisely tuned to land you the interview.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)


# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("""
    <div style="padding: 1.5rem 0 1rem;">
        <div style="font-family:'DM Mono',monospace; font-size:0.65rem; letter-spacing:0.2em;
                    text-transform:uppercase; color:#c9a84c; margin-bottom:0.4rem;">
            ✦ ResumeForge
        </div>
        <div style="font-family:'Cormorant Garamond',serif; font-size:1.4rem;
                    font-weight:300; color:#f0ede6; margin-bottom:0.3rem;">
            Settings
        </div>
        <div style="height:1px; background:rgba(201,168,76,0.18); margin-bottom:1.5rem;"></div>
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
    <div style="margin-top:2rem; padding:1.2rem; background:#111318;
                border:1px solid rgba(201,168,76,0.18); border-radius:4px;">
        <div style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.16em;
                    text-transform:uppercase; color:#c9a84c; margin-bottom:0.8rem;">
            How it works
        </div>
        <div style="font-size:0.8rem; color:#8a8680; line-height:1.7;">
            <div style="margin-bottom:0.5rem;">① Upload your resume</div>
            <div style="margin-bottom:0.5rem;">② Paste the job description</div>
            <div style="margin-bottom:0.5rem;">③ Choose your goal</div>
            <div>④ Run analysis → download</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:1.5rem; padding:1rem; background:rgba(201,168,76,0.06);
                border:1px solid rgba(201,168,76,0.15); border-radius:4px;">
        <div style="font-size:0.75rem; color:#8a8680; line-height:1.6;">
            <span style="color:#c9a84c;">✦</span> Your files are never stored.<br/>
            <span style="color:#c9a84c;">✦</span> Analysis runs in real-time.<br/>
            <span style="color:#c9a84c;">✦</span> Download your edits instantly.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==============================
# CLIENT SETUP
# ==============================
model_map = {
    "Step-3.5-Flash (StepFun · Recommended)": "stepfun/step-3.5-flash:free",
    "Meta Llama via Meta/Facebook": "meta-llama/llama-3-8b-instruct",
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

def call_llm(system_task, user_content):
    scoring_instruction = (
        "\n\nCRITICAL: Begin your response with 'MATCH_SCORE: [number]' (0–100) "
        "based on how well the resume fits the job description, followed by your analysis."
    )
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

def get_score_color(score):
    if score < 50: return "#FF4B4B"
    elif score < 80: return "#FFA500"
    else: return "#28A745"


# ==============================
# STEP LABELS
# ==============================
st.markdown("""
<div style="display:flex; gap:1.5rem; margin-bottom:2rem; flex-wrap:wrap;">
    <div style="font-family:'DM Mono',monospace; font-size:0.65rem; letter-spacing:0.18em;
                text-transform:uppercase; color:#c9a84c;">
        ① Upload Resume
    </div>
    <div style="color:rgba(201,168,76,0.3);">·</div>
    <div style="font-family:'DM Mono',monospace; font-size:0.65rem; letter-spacing:0.18em;
                text-transform:uppercase; color:#c9a84c;">
        ② Job Description
    </div>
    <div style="color:rgba(201,168,76,0.3);">·</div>
    <div style="font-family:'DM Mono',monospace; font-size:0.65rem; letter-spacing:0.18em;
                text-transform:uppercase; color:#c9a84c;">
        ③ Choose Goal
    </div>
    <div style="color:rgba(201,168,76,0.3);">·</div>
    <div style="font-family:'DM Mono',monospace; font-size:0.65rem; letter-spacing:0.18em;
                text-transform:uppercase; color:#c9a84c;">
        ④ Run
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================
# INPUT COLUMNS
# ==============================
col1, col2 = st.columns(2, gap="large")

with col1:
    resume_file = st.file_uploader(
        "Upload Resume",
        type=["pdf", "docx", "txt"],
        help="PDF, DOCX, or TXT — your file is never stored."
    )

with col2:
    job_desc = st.text_area(
        "Target Job Description",
        height=200,
        placeholder="Paste the full job posting here — requirements, responsibilities, everything..."
    )

st.markdown("<hr/>", unsafe_allow_html=True)

# ==============================
# GOAL SELECTION
# ==============================
prompt_options = {
    "✦ ATS Keyword Optimization": "Analyze the Job Description for top keywords and modify my resume bullet points to include them naturally.",
    "✦ STAR Method Bullet Rewrite": "Rewrite my work experience bullet points using the STAR method (Situation, Task, Action, Result). Focus on quantifiable achievements.",
    "✦ Professional Summary Rewrite": "Draft a compelling 3-4 sentence professional summary that bridges my current experience with this specific job.",
    "✦ Skills Gap Analysis": "Compare my resume against the job description. Identify exactly what hard and soft skills I am currently missing.",
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

# ==============================
# RUN BUTTON
# ==============================
col_btn, col_space = st.columns([1, 4])
with col_btn:
    run = st.button("✦ Run Analysis", type="primary", use_container_width=False)

st.markdown("<hr/>", unsafe_allow_html=True)

# ==============================
# EXECUTION & RESULTS
# ==============================
if run:
    if not resume_file:
        st.warning("⚠ Please upload a resume to get started.")
    elif not job_desc.strip():
        st.warning("⚠ Please paste a job description to match against.")
    else:
        resume_text = extract_text(resume_file)
        system_task = prompt_options[selected_strategy]
        if custom_instructions:
            system_task += f" Additional user context: {custom_instructions}"

        with st.spinner("Analyzing your resume against the role..."):
            result = call_llm(
                system_task,
                f"JOB DESCRIPTION:\n{job_desc}\n\nRESUME:\n{resume_text}"
            )

        if result:
            score_match = re.search(r"MATCH_SCORE:\s*(\d+)", result)

            if score_match:
                score_val = int(score_match.group(1))
                color = get_score_color(score_val)
                display_text = result.replace(score_match.group(0), "").strip()

                # Score label
                if score_val >= 80:
                    score_label = "Strong Match"
                elif score_val >= 50:
                    score_label = "Partial Match"
                else:
                    score_label = "Needs Work"

                # Success banner
                st.markdown(f"""
                <div style="
                    padding: 1rem 1.5rem;
                    background: rgba(40,167,69,0.06);
                    border: 1px solid rgba(40,167,69,0.25);
                    border-radius: 3px;
                    margin-bottom: 1.5rem;
                    font-family: 'DM Mono', monospace;
                    font-size: 0.72rem;
                    letter-spacing: 0.14em;
                    text-transform: uppercase;
                    color: #28A745;
                ">
                    ✓ &nbsp; Analysis complete · {PROVIDER.split('(')[0].strip()}
                </div>
                """, unsafe_allow_html=True)

                # Score + progress
                m1, m2 = st.columns([1, 3], gap="large")
                with m1:
                    st.metric("Match Score", f"{score_val}%", delta=score_label)

                with m2:
                    st.markdown(f"""
                    <div style="margin-top:1.2rem;">
                        <div style="
                            font-family:'DM Mono',monospace;
                            font-size:0.62rem; letter-spacing:0.16em;
                            text-transform:uppercase; color:#8a8680;
                            margin-bottom:0.6rem;
                        ">Resume–Job Alignment</div>
                        <div style="height:6px; background:#181a21; border-radius:2px; overflow:hidden;">
                            <div style="
                                height:100%;
                                width:{score_val}%;
                                background:{color};
                                border-radius:2px;
                                transition: width 1s ease;
                            "></div>
                        </div>
                        <div style="
                            display:flex; justify-content:space-between;
                            font-size:0.65rem; color:#4a4845;
                            font-family:'DM Mono',monospace;
                            margin-top:0.4rem;
                        ">
                            <span>0%</span><span>50%</span><span>100%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            else:
                display_text = result

            st.markdown("<hr/>", unsafe_allow_html=True)

            # Results header
            st.markdown(f"""
            <div style="margin-bottom:1.2rem;">
                <div style="
                    font-family:'DM Mono',monospace; font-size:0.65rem;
                    letter-spacing:0.2em; text-transform:uppercase;
                    color:#c9a84c; margin-bottom:0.4rem;
                ">
                    <span style="display:inline-block;width:20px;height:1px;background:#c9a84c;
                                 vertical-align:middle;margin-right:0.6rem;"></span>
                    Results
                </div>
                <div style="
                    font-family:'Cormorant Garamond',serif;
                    font-size:1.8rem; font-weight:300; color:#f0ede6;
                ">
                    {selected_strategy.replace("✦ ", "")}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(display_text)

            st.markdown("<br/>", unsafe_allow_html=True)

            # Download
            dcol1, dcol2 = st.columns([1, 4])
            with dcol1:
                st.download_button(
                    "↓ Download Analysis",
                    data=display_text,
                    file_name="resume_analysis.txt",
                    mime="text/plain"
                )
