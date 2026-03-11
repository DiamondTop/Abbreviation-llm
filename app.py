import streamlit as st
import re
import time as _time
import requests
from datetime import datetime, timezone
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

header[data-testid="stHeader"] {
    background: var(--bg) !important;
    border-bottom: 1px solid var(--border) !important;
}
[data-testid="stToolbar"]               { display: none !important; }
[data-testid="collapsedControl"]        { display: none !important; }
button[kind="header"]                   { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
.stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-weight: 300;
}
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; font-family: var(--sans) !important; }
[data-testid="stMainBlockContainer"] { padding-top: 0.5rem !important; padding-bottom: 4rem !important; }
h1, h2, h3, h4 { font-family: var(--serif) !important; font-weight: 300 !important; }

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
.stTextArea label, [data-testid="stWidgetLabel"] p {
    font-family: var(--mono) !important; font-size: 0.65rem !important;
    letter-spacing: 0.18em !important; text-transform: uppercase !important;
    color: var(--gold) !important; margin-bottom: 0.4rem !important; font-weight: 400 !important;
}

.stSelectbox > div > div {
    background: var(--bg2) !important; border: 1px solid rgba(201,168,76,0.18) !important;
    border-radius: 4px !important; color: var(--text) !important;
}
.stSelectbox > div > div:hover,
.stSelectbox > div > div:focus-within { border-color: var(--gold) !important; }
[data-testid="stSelectbox"] svg { color: var(--gold) !important; }
div[data-baseweb="popover"] { background: var(--bg2) !important; border: 1px solid var(--border) !important; }
div[data-baseweb="option"]  { background: var(--bg2) !important; color: var(--text) !important; }
div[data-baseweb="option"]:hover { background: var(--bg3) !important; color: var(--gold) !important; }

[data-testid="stFileUploader"] {
    background: var(--bg2) !important;
    border: 1px dashed rgba(201,168,76,0.3) !important;
    border-radius: 4px !important;
    padding: 0.5rem !important;
}
/* Every inner container must be forced dark */
[data-testid="stFileUploader"] > div,
[data-testid="stFileUploader"] section,
[data-testid="stFileUploader"] section > div,
[data-testid="stFileUploader"] section > input,
[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploaderDropzone"] > div {
    background: var(--bg2) !important;
    background-color: var(--bg2) !important;
    border: none !important;
}
/* Hover state — slightly lighter dark */
[data-testid="stFileUploader"]:hover {
    border-color: rgba(201,168,76,0.55) !important;
    background: var(--bg3) !important;
}
[data-testid="stFileUploader"]:hover section,
[data-testid="stFileUploader"]:hover > div,
[data-testid="stFileUploader"]:hover [data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploader"]:hover [data-testid="stFileUploaderDropzone"] > div {
    background: var(--bg3) !important;
    background-color: var(--bg3) !important;
}
/* Instruction text */
[data-testid="stFileUploaderDropzoneInstructions"] {
    background: transparent !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div > span {
    color: var(--muted) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div > small {
    color: var(--placeholder) !important;
}
/* SVG upload icon */
[data-testid="stFileUploader"] svg {
    color: var(--gold) !important;
    fill: var(--gold) !important;
    opacity: 0.7;
}
/* Browse button */
[data-testid="stFileUploader"] button {
    background: transparent !important; color: var(--gold) !important;
    border: 1px solid var(--border) !important; border-radius: 3px !important;
    font-family: var(--mono) !important; font-size: 0.72rem !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
}
[data-testid="stFileUploader"] button:hover {
    border-color: var(--gold) !important;
    background: var(--gold-dim) !important;
}
/* Uploaded file pill */
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] span,
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] p {
    color: var(--text) !important;
}
/* Label above the uploader */
[data-testid="stFileUploader"] label {
    font-family: var(--mono) !important; font-size: 0.65rem !important;
    letter-spacing: 0.18em !important; text-transform: uppercase !important;
    color: var(--gold) !important;
}

.stButton > button {
    background: var(--gold) !important; color: #0b0c0f !important;
    border: 1px solid var(--gold) !important; border-radius: 3px !important;
    font-family: var(--sans) !important; font-size: 0.8rem !important;
    font-weight: 600 !important; letter-spacing: 0.12em !important;
    text-transform: uppercase !important; padding: 0.7rem 2.2rem !important;
}
.stButton > button:hover {
    background: transparent !important; color: var(--gold) !important;
}
.stDownloadButton > button {
    background: transparent !important; color: var(--gold) !important;
    border: 1px solid var(--border) !important; border-radius: 3px !important;
    font-size: 0.78rem !important; letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
.stDownloadButton > button:hover { border-color: var(--gold) !important; background: var(--gold-dim) !important; }

hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 2rem 0 !important; }

[data-testid="stMetric"] {
    background: var(--bg2) !important; border: 1px solid var(--border) !important;
    border-radius: 4px !important; padding: 1.2rem 1.5rem !important;
}
[data-testid="stMetricLabel"] p {
    font-family: var(--mono) !important; font-size: 0.62rem !important;
    letter-spacing: 0.16em !important; text-transform: uppercase !important; color: var(--muted) !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--serif) !important; font-size: 2.8rem !important;
    font-weight: 300 !important; color: var(--gold) !important; line-height: 1.1 !important;
}
[data-testid="stMetricDelta"] { color: #28A745 !important; font-size: 0.78rem !important; }
.stAlert { background: var(--bg2) !important; border: 1px solid var(--border) !important; border-radius: 3px !important; }

.stMarkdown p, .stMarkdown li { color: var(--text) !important; line-height: 1.85 !important; font-size: 0.95rem !important; }
.stMarkdown h3 { font-family: var(--serif) !important; color: var(--gold) !important; font-size: 1.4rem !important; margin-top: 1.5rem !important; }
.stMarkdown strong { color: var(--gold-light) !important; font-weight: 500 !important; }
.stMarkdown code { background: var(--bg3) !important; border: 1px solid var(--border) !important; border-radius: 3px !important; color: var(--gold) !important; font-family: var(--mono) !important; font-size: 0.82rem !important; padding: 0.15rem 0.45rem !important; }

.cover-letter-box {
    background: var(--bg2); border: 1px solid var(--border); border-radius: 6px;
    padding: 2rem 2.2rem; line-height: 1.9; font-size: 0.95rem; color: var(--text);
    white-space: pre-wrap; font-family: var(--sans); position: relative;
}
.cover-letter-box::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--gold), transparent); border-radius: 6px 6px 0 0;
}

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold); }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# ANALYTICS — Supabase helpers
# ══════════════════════════════════════════════════════
SUPABASE_URL = st.secrets.get("supabase", {}).get("url", "")
SUPABASE_KEY = st.secrets.get("supabase", {}).get("key", "")
ANALYTICS_ON = bool(SUPABASE_URL and SUPABASE_KEY)

EV_VISIT = "visit"
EV_RUN   = "run"
EV_ATS   = "goal_ats"
EV_STAR  = "goal_star"
EV_SUMM  = "goal_summary"
EV_GAP   = "goal_gap"
EV_COVER = "cover_letter_generated"

GOAL_EVENTS = {
    "✦  ATS Keyword Optimization":          EV_ATS,
    "✦  Rewrite Bullets with Impact":       EV_STAR,
    "✦  Professional Summary Rewrite":      EV_SUMM,
    "✦  Skills Gap Analysis":               EV_GAP,
}


def _sb_headers():
    return {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal",
    }


def track(event: str):
    if not ANALYTICS_ON:
        return
    try:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/analytics",
            json={"event": event},
            headers=_sb_headers(),
            timeout=3
        )
    except Exception:
        pass


def get_counts() -> dict:
    if not ANALYTICS_ON:
        return {}
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/analytics?select=event",
            headers={**_sb_headers(), "Prefer": ""},
            timeout=4
        )
        rows = resp.json()
        counts = {}
        for row in rows:
            e = row.get("event", "")
            counts[e] = counts.get(e, 0) + 1
        return counts
    except Exception:
        return {}


if "visited" not in st.session_state:
    st.session_state.visited = True
    track(EV_VISIT)


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
            "Nemo via Nvidia",
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

    if ANALYTICS_ON:
        counts       = get_counts()
        total_visits = counts.get(EV_VISIT, 0)
        total_runs   = counts.get(EV_RUN,   0)
        ats_count    = counts.get(EV_ATS,   0)
        star_count   = counts.get(EV_STAR,  0)
        summ_count   = counts.get(EV_SUMM,  0)
        gap_count    = counts.get(EV_GAP,   0)
        cover_count  = counts.get(EV_COVER, 0)
        total_goals  = ats_count + star_count + summ_count + gap_count or 1

        def pct(n): return round(n / total_goals * 100)

        st.markdown(
            "<div style='margin-top:1.6rem; border-radius:6px 6px 0 0; overflow:hidden;"
            "border:1px solid rgba(201,168,76,0.25); border-bottom:none;"
            "background:linear-gradient(135deg,#1a160a 0%,#0f1118 100%);"
            "padding:0.8rem 1.1rem; display:flex; align-items:center; gap:0.55rem;'>"
            "<div style='width:7px; height:7px; border-radius:50%; background:#c9a84c;"
            "box-shadow:0 0 8px rgba(201,168,76,0.9);'></div>"
            "<span style='font-family:DM Mono,monospace; font-size:0.62rem;"
            "letter-spacing:0.2em; text-transform:uppercase; color:#c9a84c;"
            "font-weight:500;'>Live Analytics</span></div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<div style='border-left:1px solid rgba(201,168,76,0.25);"
            "border-right:1px solid rgba(201,168,76,0.25);"
            "background:#0d0e12; padding:0.9rem 1rem 0.6rem;'>"
            "<div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.45rem;'>"
            f"<div style='background:rgba(99,179,237,0.08); border:1px solid rgba(99,179,237,0.25);"
            f"border-radius:5px; padding:0.6rem 0.3rem; text-align:center;'>"
            f"<div style='font-family:DM Mono,monospace; font-size:1.2rem; font-weight:500; color:#63b3ed;'>{total_visits:,}</div>"
            f"<div style='font-size:0.54rem; letter-spacing:0.08em; text-transform:uppercase; color:#6a6560;'>Visitors</div></div>"
            f"<div style='background:rgba(104,211,145,0.07); border:1px solid rgba(104,211,145,0.22);"
            f"border-radius:5px; padding:0.6rem 0.3rem; text-align:center;'>"
            f"<div style='font-family:DM Mono,monospace; font-size:1.2rem; font-weight:500; color:#68d391;'>{total_runs:,}</div>"
            f"<div style='font-size:0.54rem; letter-spacing:0.08em; text-transform:uppercase; color:#6a6560;'>Analyses</div></div>"
            f"<div style='background:rgba(201,168,76,0.08); border:1px solid rgba(201,168,76,0.22);"
            f"border-radius:5px; padding:0.6rem 0.3rem; text-align:center;'>"
            f"<div style='font-family:DM Mono,monospace; font-size:1.2rem; font-weight:500; color:#c9a84c;'>{cover_count:,}</div>"
            f"<div style='font-size:0.54rem; letter-spacing:0.08em; text-transform:uppercase; color:#6a6560;'>Cover Letters</div></div>"
            "</div></div>",
            unsafe_allow_html=True
        )

        goal_items = [
            ("ATS Keywords",          ats_count,  "#c9a84c", "rgba(201,168,76,0.2)"),
            ("Impact Bullet Rewrite", star_count, "#63b3ed", "rgba(99,179,237,0.2)"),
            ("Summary Rewrite",       summ_count, "#68d391", "rgba(104,211,145,0.2)"),
            ("Skills Gap",            gap_count,  "#fc8181", "rgba(252,129,129,0.2)"),
        ]
        for i, (name, count, color, grad) in enumerate(goal_items):
            w = pct(count)
            is_last = (i == len(goal_items) - 1)
            bottom_radius = "0 0 6px 6px" if is_last else "0"
            bottom_border = "border-bottom:1px solid rgba(201,168,76,0.25);" if is_last else ""
            st.markdown(
                f"<div style='border-left:1px solid rgba(201,168,76,0.25);"
                f"border-right:1px solid rgba(201,168,76,0.25); {bottom_border}"
                f"border-radius:{bottom_radius}; background:#0d0e12; padding:0.3rem 1rem 0.55rem;'>"
                f"<div style='display:flex; justify-content:space-between; align-items:baseline; margin-bottom:0.28rem;'>"
                f"<span style='font-size:0.73rem; color:#b0aa9f;'>{name}</span>"
                f"<span style='font-family:DM Mono,monospace; font-size:0.7rem; color:{color};'>"
                f"{count} <span style='color:#4a4845; font-size:0.58rem;'>· {w}%</span></span></div>"
                f"<div style='height:5px; border-radius:3px; background:rgba(255,255,255,0.05); overflow:hidden;'>"
                f"<div style='height:5px; width:{w}%; border-radius:3px;"
                f"background:linear-gradient(90deg,{color},{grad});'></div></div></div>",
                unsafe_allow_html=True
            )


# ==============================
# CLIENT SETUP
# ==============================
model_map = {
    "Step-3.5-Flash (StepFun · Recommended)": "stepfun/step-3.5-flash:free",
    "Nemo via Nvidia":                         "nvidia/nemotron-3-super-120b-a12b:free",
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
    scoring_instruction = (
        "\n\nCRITICAL: Begin your response with 'MATCH_SCORE: [number]' (0–100) "
        "based on how well the resume fits the job description, followed by your analysis."
    ) if add_score else ""
    try:
        if "Gemini" not in PROVIDER:
            r = client.chat.completions.create(
                model=MODEL_NAME, temperature=0.4,
                messages=[
                    {"role": "system", "content": system_task + scoring_instruction},
                    {"role": "user",   "content": user_content}
                ]
            )
            return r.choices[0].message.content.strip()
        else:
            r = gemini_model.generate_content(f"{system_task}{scoring_instruction}\n\n{user_content}")
            return r.text.strip()
    except Exception as e:
        st.error(f"LLM Error: {e}")
        return ""


def generate_cover_letter(job_desc, resume_text):
    system_task = """You are an expert career coach and professional writer.
Write a compelling, personalized cover letter based on the candidate's resume and the job description provided.
The cover letter must:
- Be 3–4 paragraphs, professional but warm in tone
- Open with a strong hook that references the specific role and company
- Highlight 2–3 of the candidate's most relevant experiences from their resume that directly match the job requirements
- Include at least one quantified achievement from the resume
- Close with a confident call to action
- NOT use generic filler phrases like "I am writing to express my interest..."
- Sound like a real human wrote it, not a template
Output ONLY the cover letter text. Start directly with "Dear Hiring Manager," or a named salutation if available."""
    return call_llm(system_task, f"JOB DESCRIPTION:\n{job_desc}\n\nRESUME:\n{resume_text}", add_score=False)


def get_score_color(score):
    if score < 50:   return "#FF4B4B"
    elif score < 80: return "#FFA500"
    else:            return "#28A745"


# ==============================
# PROGRESS BAR HELPER
# ==============================
def make_progress_ui(steps: list):
    """
    Returns (container, advance_fn).
    Call advance_fn(i, label) to move to step i.
    Call advance_fn(None) to clear the whole bar.
    """
    container = st.empty()

    def render(current_i):
        if current_i is None:
            container.empty()
            return

        total   = len(steps) - 1
        bar_pct = int(current_i / total * 100)
        icon, label = steps[current_i]

        # Build step dots HTML
        dots_html = ""
        for si, (sicon, slabel) in enumerate(steps):
            if si < current_i:
                dot_bg, dot_color, text_color, content = "#28A745", "#0b0c0f", "#28A745", "✓"
            elif si == current_i:
                dot_bg, dot_color, text_color, content = "#c9a84c", "#0b0c0f", "#f0ede6", sicon
            else:
                dot_bg, dot_color, text_color, content = "#1c1f28", "#4a4845", "#4a4845", str(si + 1)

            connector = (
                f"<div style='flex:1; height:2px; margin:0 4px; align-self:center; border-radius:1px;"
                f"background:{'#28A745' if si < current_i else 'rgba(201,168,76,0.12)'};"
                f"'></div>"
            ) if si < len(steps) - 1 else ""

            dots_html += (
                f"<div style='display:flex; flex-direction:column; align-items:center; gap:6px;'>"
                f"<div style='width:34px; height:34px; border-radius:50%;"
                f"background:{dot_bg}; color:{dot_color};"
                f"border:1.5px solid {'#c9a84c' if si == current_i else dot_bg};"
                f"display:flex; align-items:center; justify-content:center;"
                f"font-size:0.85rem; font-weight:600;'>{content}</div>"
                f"<div style='font-family:DM Mono,monospace; font-size:0.5rem; letter-spacing:0.07em;"
                f"text-transform:uppercase; color:{text_color}; text-align:center; max-width:66px;"
                f"line-height:1.35;'>{slabel}</div>"
                f"</div>" + connector
            )

        container.markdown(
            f"<div style='background:#111318; border:1px solid rgba(201,168,76,0.28);"
            f"border-radius:10px; padding:1.5rem 1.8rem; margin-bottom:1.4rem;'>"

            # Header row
            f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;'>"
            f"<div style='display:flex; align-items:center; gap:0.6rem;'>"
            f"<div style='width:8px; height:8px; border-radius:50%; background:#c9a84c;"
            f"box-shadow:0 0 10px rgba(201,168,76,0.9); animation:pulse 1.5s infinite;'></div>"
            f"<span style='font-family:DM Mono,monospace; font-size:0.68rem; letter-spacing:0.14em;"
            f"text-transform:uppercase; color:#c9a84c;'>{icon} &nbsp;{label}</span>"
            f"</div>"
            f"<span style='font-family:DM Mono,monospace; font-size:0.78rem;"
            f"font-weight:600; color:#c9a84c;'>{bar_pct}%</span>"
            f"</div>"

            # Progress track
            f"<div style='height:6px; background:rgba(201,168,76,0.1); border-radius:3px;"
            f"overflow:hidden; margin-bottom:1.4rem;'>"
            f"<div style='height:6px; width:{bar_pct}%; border-radius:3px;"
            f"background:linear-gradient(90deg,#7a5520,#c9a84c,#e8c87a);'></div></div>"

            # Step dots
            f"<div style='display:flex; align-items:flex-start; justify-content:center;'>"
            f"{dots_html}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    return render


# ==============================
# HERO HEADER
# ==============================
st.markdown("""
<div style="padding:2.5rem 0 1.8rem; position:relative; overflow:hidden;">
    <div style="position:absolute; inset:0;
        background-image: linear-gradient(rgba(201,168,76,0.035) 1px,transparent 1px),
                          linear-gradient(90deg,rgba(201,168,76,0.035) 1px,transparent 1px);
        background-size:52px 52px; pointer-events:none;"></div>
    <div style="position:relative; z-index:1;">
        <div style="font-family:'DM Mono',monospace; font-size:0.65rem; letter-spacing:0.24em;
                    text-transform:uppercase; color:#c9a84c; margin-bottom:0.9rem;
                    display:flex; align-items:center; gap:0.7rem;">
            <span style="display:inline-block; width:26px; height:1px; background:#c9a84c;"></span>
            AI-Powered · Job-Specific · Interview-Ready
        </div>
        <h1 style="font-family:'Cormorant Garamond',Georgia,serif;
                   font-size:clamp(2.6rem,5.5vw,4.6rem); font-weight:300;
                   line-height:1.05; color:#f0ede6; margin-bottom:0.7rem;">
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
        "Upload Resume", type=["pdf", "docx", "txt"],
        help="Your file is processed in memory and never stored."
    )
with col2:
    job_desc = st.text_area(
        "Target Job Description", height=200,
        placeholder="Paste the full job posting here — requirements, responsibilities, everything..."
    )

st.markdown("<hr/>", unsafe_allow_html=True)

# ==============================
# GOAL + INSTRUCTIONS
# ==============================
prompt_options = {
    "✦  ATS Keyword Optimization":          "Analyze the Job Description for top keywords and modify my resume bullet points to include them naturally.",
    "✦  Rewrite Bullets with Impact":       "Rewrite my work experience bullet points to highlight measurable achievements and strong action verbs. Turn vague responsibilities into powerful results-driven statements — e.g. 'Managed a team' becomes 'Led a 6-person team that delivered a 30% efficiency gain in Q3'. Focus on outcomes, numbers, and impact.",
    "✦  Professional Summary Rewrite":      "Draft a compelling 3–4 sentence professional summary that bridges my current experience with this specific job.",
    "✦  Skills Gap Analysis":               "Compare my resume against the job description. Identify exactly what hard and soft skills I am currently missing.",
}

col3, col4 = st.columns([1.2, 1], gap="large")
with col3:
    selected_strategy = st.selectbox("Choose Your Goal", list(prompt_options.keys()))
with col4:
    custom_instructions = st.text_area(
        "Additional Instructions (Optional)", height=110,
        placeholder="e.g. 'Highlight my 10 years of experience in logistics'"
    )

st.markdown("<br/>", unsafe_allow_html=True)

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
        system_task = prompt_options[selected_strategy]
        if custom_instructions:
            system_task += f"  Additional user context: {custom_instructions}"

        track(EV_RUN)
        track(GOAL_EVENTS.get(selected_strategy, "goal_other"))

        # ── Step definitions ──────────────────────────────────
        steps_base = [
            ("📄", "Reading resume"),
            ("🔍", "Parsing job description"),
            ("🤖", "Running AI analysis"),
            ("✅", "Complete"),
        ]
        steps_cover = [
            ("📄", "Reading resume"),
            ("🔍", "Parsing job description"),
            ("🤖", "Running AI analysis"),
            ("✉️",  "Generating cover letter"),
            ("✅", "Complete"),
        ]
        steps = steps_cover if is_ats else steps_base
        total = len(steps) - 1

        # ── Render progress UI ────────────────────────────────
        render_progress = make_progress_ui(steps)

        render_progress(0)
        resume_text = extract_text(resume_file)

        render_progress(1)
        _time.sleep(0.35)   # let user see the step

        render_progress(2)
        result = call_llm(system_task, f"JOB DESCRIPTION:\n{job_desc}\n\nRESUME:\n{resume_text}")

        cover_letter_text = ""
        if is_ats and result:
            render_progress(3)
            cover_letter_text = generate_cover_letter(job_desc, resume_text)
            if cover_letter_text:
                track(EV_COVER)

        # Complete → brief pause → clear bar
        render_progress(total)
        _time.sleep(0.6)
        render_progress(None)   # clear

        # ── Display results ───────────────────────────────────
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

                st.markdown(f"""
                <div style="padding:0.85rem 1.3rem; background:rgba(40,167,69,0.07);
                            border:1px solid rgba(40,167,69,0.28); border-radius:3px;
                            margin-bottom:1.4rem; font-family:'DM Mono',monospace;
                            font-size:0.68rem; letter-spacing:0.14em; text-transform:uppercase; color:#28A745;">
                    ✓ &nbsp; Analysis complete · {PROVIDER.split('(')[0].strip()}
                </div>
                """, unsafe_allow_html=True)

                m1, m2 = st.columns([1, 3], gap="large")
                with m1:
                    st.metric("Match Score", f"{score_val}%", delta=score_label)
                with m2:
                    st.markdown(f"""
                    <div style="margin-top:1.1rem;">
                        <div style="font-family:'DM Mono',monospace; font-size:0.6rem; letter-spacing:0.16em;
                                    text-transform:uppercase; color:#9a958f; margin-bottom:0.55rem;">
                            Resume – Job Alignment
                        </div>
                        <div style="height:7px; background:#1c1f28; border-radius:3px; overflow:hidden;">
                            <div style="height:100%; width:{score_val}%; background:{color}; border-radius:3px;"></div>
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:0.6rem;
                                    color:#4a4845; font-family:'DM Mono',monospace; margin-top:0.35rem;">
                            <span>0%</span><span>50%</span><span>100%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                display_text = result

            st.markdown("<hr/>", unsafe_allow_html=True)

            st.markdown(f"""
            <div style="margin-bottom:1.1rem;">
                <div style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.2em;
                            text-transform:uppercase; color:#c9a84c; margin-bottom:0.35rem;
                            display:flex; align-items:center; gap:0.6rem;">
                    <span style="display:inline-block;width:18px;height:1px;background:#c9a84c;"></span>Results
                </div>
                <div style="font-family:'Cormorant Garamond',serif; font-size:1.75rem;
                            font-weight:300; color:#f0ede6;">
                    {selected_strategy.replace("✦  ", "")}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(display_text)
            st.markdown("<br/>", unsafe_allow_html=True)

            dcol1, _ = st.columns([1, 4])
            with dcol1:
                st.download_button(
                    "↓  Download Analysis", data=display_text,
                    file_name="resume_analysis.txt", mime="text/plain"
                )

            # ── Cover Letter Section ──────────────────────────
            if is_ats and cover_letter_text:
                st.markdown("<hr/>", unsafe_allow_html=True)

                st.markdown("""
                <div style="margin-bottom:1.4rem;">
                    <div style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.2em;
                                text-transform:uppercase; color:#c9a84c; margin-bottom:0.35rem;
                                display:flex; align-items:center; gap:0.6rem;">
                        <span style="display:inline-block;width:18px;height:1px;background:#c9a84c;"></span>Bonus
                    </div>
                    <div style="font-family:'Cormorant Garamond',serif; font-size:1.75rem;
                                font-weight:300; color:#f0ede6; margin-bottom:0.4rem;">
                        Your Tailored Cover Letter
                    </div>
                    <p style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#9a958f;
                              font-weight:300; max-width:560px; line-height:1.7; margin:0;">
                        Written specifically for this role using your resume and the job description.
                        Edit freely before sending.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f'<div class="cover-letter-box">{cover_letter_text}</div>', unsafe_allow_html=True)
                st.markdown("<br/>", unsafe_allow_html=True)

                cl1, cl2, _ = st.columns([1, 1, 3])
                with cl1:
                    st.download_button(
                        "↓  Download .txt", data=cover_letter_text,
                        file_name="cover_letter.txt", mime="text/plain", key="dl_cover_txt"
                    )
                with cl2:
                    st.download_button(
                        "↓  Download .doc", data=cover_letter_text.replace("\n", "\r\n"),
                        file_name="cover_letter.doc", mime="application/msword", key="dl_cover_doc"
                    )

                st.markdown("""
                <div style="margin-top:1rem; padding:0.9rem 1.2rem; background:rgba(201,168,76,0.05);
                            border-left:2px solid rgba(201,168,76,0.4); border-radius:0 4px 4px 0;">
                    <span style="font-family:'DM Mono',monospace; font-size:0.62rem;
                                 letter-spacing:0.14em; text-transform:uppercase; color:#c9a84c;">✦ Tip</span>
                    <p style="font-family:'DM Sans',sans-serif; font-size:0.82rem; color:#9a958f;
                              margin:0.3rem 0 0; line-height:1.7;">
                        Personalise the opening line with the hiring manager's name if you can find it on LinkedIn.
                        A named salutation can increase response rates by up to 20%.
                    </p>
                </div>
                """, unsafe_allow_html=True)
