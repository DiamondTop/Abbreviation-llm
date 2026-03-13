import streamlit as st
import re
import time as _time
import requests
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
.stTextArea textarea::placeholder { color: var(--placeholder) !important; opacity: 1 !important; }

.stTextInput > div > div > input {
    background: var(--bg2) !important;
    border: 1px solid rgba(201,168,76,0.18) !important;
    border-radius: 4px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 0.92rem !important;
    line-height: 1.75 !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
    outline: none !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px rgba(201,168,76,0.12) !important;
}
.stTextInput > div > div > input::placeholder { color: var(--placeholder) !important; opacity: 1 !important; }

.stTextArea label, .stTextInput label, [data-testid="stWidgetLabel"] p {
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
[data-testid="stFileUploaderDropzoneInstructions"] { background: transparent !important; }
[data-testid="stFileUploaderDropzoneInstructions"] > div > span { color: var(--muted) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] > div > small { color: var(--placeholder) !important; }
[data-testid="stFileUploader"] svg { color: var(--gold) !important; fill: var(--gold) !important; opacity: 0.7; }
[data-testid="stFileUploader"] button {
    background: transparent !important; color: var(--gold) !important;
    border: 1px solid var(--border) !important; border-radius: 3px !important;
    font-family: var(--mono) !important; font-size: 0.72rem !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important; transition: all 0.2s !important;
}
[data-testid="stFileUploader"] button:hover { border-color: var(--gold) !important; background: var(--gold-dim) !important; }
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {
    background: var(--bg3) !important; border: 1px solid var(--border) !important; border-radius: 3px !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] span,
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] p { color: var(--text) !important; }
[data-testid="stFileUploader"] label {
    font-family: var(--mono) !important; font-size: 0.65rem !important;
    letter-spacing: 0.18em !important; text-transform: uppercase !important; color: var(--gold) !important;
}

.stButton > button {
    background: var(--gold) !important; color: #0b0c0f !important;
    border: 1px solid var(--gold) !important; border-radius: 3px !important;
    font-family: var(--sans) !important; font-size: 0.8rem !important;
    font-weight: 600 !important; letter-spacing: 0.12em !important;
    text-transform: uppercase !important; padding: 0.7rem 2.2rem !important; transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: transparent !important; color: var(--gold) !important;
    transform: translateY(-1px) !important; box-shadow: 0 8px 30px rgba(201,168,76,0.2) !important;
}
.stDownloadButton > button {
    background: transparent !important; color: var(--gold) !important;
    border: 1px solid var(--border) !important; border-radius: 3px !important;
    font-size: 0.78rem !important; letter-spacing: 0.1em !important;
    text-transform: uppercase !important; transition: all 0.2s !important;
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
.stAlert { background: var(--bg2) !important; border: 1px solid var(--border) !important; border-radius: 3px !important; color: var(--text) !important; }

.stMarkdown p, .stMarkdown li { color: var(--text) !important; line-height: 1.85 !important; font-size: 0.95rem !important; }
.stMarkdown h3 { font-family: var(--serif) !important; color: var(--gold) !important; font-size: 1.4rem !important; margin-top: 1.5rem !important; font-weight: 300 !important; }
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

/* ── HIDE STREAMLIT BRANDING ── */
footer                         { display: none !important; }
#MainMenu                      { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stDecoration"]   { display: none !important; }
.viewerBadge_container__r5tak  { display: none !important; }
.viewerBadge_link__qRIco       { display: none !important; }
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
    "✦  ATS Keyword Optimization":     EV_ATS,
    "✦  Rewrite Bullets with Impact":  EV_STAR,
    "✦  Professional Summary Rewrite": EV_SUMM,
    "✦  Skills Gap Analysis":          EV_GAP,
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
            <div style="margin-bottom:0.4rem;">&#9312; Upload your resume</div>
            <div style="margin-bottom:0.4rem;">&#9313; Paste the job description</div>
            <div style="margin-bottom:0.4rem;">&#9314; Choose your goal</div>
            <div style="margin-bottom:0.4rem;">&#9315; Add target job title <em style="color:#c9a84c;">(sharpens AI output)</em></div>
            <div>&#9316; Run analysis &#8594; download</div>
        </div>
    </div>
    <div style="margin-top:1.2rem; padding:1rem; background:rgba(201,168,76,0.06);
                border:1px solid rgba(201,168,76,0.15); border-radius:4px;">
        <div style="font-size:0.78rem; color:#9a958f; line-height:1.8;">
            <span style="color:#c9a84c;">&#10022;</span> Your files are never stored on this website.<br/>
            <span style="color:#c9a84c;">&#10022;</span> Analysis runs in real-time.<br/>
            <span style="color:#c9a84c;">&#10022;</span> Cover letter auto-generated on ATS runs.<br/>
            <span style="color:#c9a84c;">&#10022;</span> Download your edits instantly.
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
            "<div style='margin-top:1.6rem; border-radius:6px 6px 0 0;"
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
            f"<div style='font-family:DM Mono,monospace; font-size:1.2rem; font-weight:500;"
            f"color:#63b3ed; line-height:1.1;'>{total_visits:,}</div>"
            f"<div style='font-size:0.54rem; letter-spacing:0.08em; text-transform:uppercase;"
            f"color:#6a6560; margin-top:0.15rem;'>Visitors</div></div>"
            f"<div style='background:rgba(104,211,145,0.07); border:1px solid rgba(104,211,145,0.22);"
            f"border-radius:5px; padding:0.6rem 0.3rem; text-align:center;'>"
            f"<div style='font-family:DM Mono,monospace; font-size:1.2rem; font-weight:500;"
            f"color:#68d391; line-height:1.1;'>{total_runs:,}</div>"
            f"<div style='font-size:0.54rem; letter-spacing:0.08em; text-transform:uppercase;"
            f"color:#6a6560; margin-top:0.15rem;'>Analyses</div></div>"
            f"<div style='background:rgba(201,168,76,0.08); border:1px solid rgba(201,168,76,0.22);"
            f"border-radius:5px; padding:0.6rem 0.3rem; text-align:center;'>"
            f"<div style='font-family:DM Mono,monospace; font-size:1.2rem; font-weight:500;"
            f"color:#c9a84c; line-height:1.1;'>{cover_count:,}</div>"
            f"<div style='font-size:0.54rem; letter-spacing:0.08em; text-transform:uppercase;"
            f"color:#6a6560; margin-top:0.15rem;'>Letters</div></div>"
            "</div></div>",
            unsafe_allow_html=True
        )

        st.markdown(
            "<div style='border-left:1px solid rgba(201,168,76,0.25);"
            "border-right:1px solid rgba(201,168,76,0.25);"
            "background:#0d0e12; padding:0.6rem 1rem 0.5rem;'>"
            "<div style='font-family:DM Mono,monospace; font-size:0.57rem; letter-spacing:0.16em;"
            "text-transform:uppercase; color:#4a4845;"
            "border-top:1px solid rgba(255,255,255,0.05); padding-top:0.6rem;'>"
            "Goal Breakdown</div></div>",
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
                f"border-radius:{bottom_radius}; background:#0d0e12;"
                f"padding:0.3rem 1rem 0.55rem;'>"
                f"<div style='display:flex; justify-content:space-between; align-items:baseline; margin-bottom:0.28rem;'>"
                f"<span style='font-size:0.73rem; color:#b0aa9f;'>{name}</span>"
                f"<span style='font-family:DM Mono,monospace; font-size:0.7rem; font-weight:500; color:{color};'>"
                f"{count} <span style='color:#4a4845; font-size:0.58rem;'>· {w}%</span></span></div>"
                f"<div style='height:5px; border-radius:3px; background:rgba(255,255,255,0.05); overflow:hidden;'>"
                f"<div style='height:5px; width:{w}%; border-radius:3px;"
                f"background:linear-gradient(90deg,{color},{grad});'></div></div></div>",
                unsafe_allow_html=True
            )
    else:
        st.markdown("""
        <div style="margin-top:1.4rem; padding:0.9rem 1rem; background:#0b0c0f;
                    border:1px dashed rgba(201,168,76,0.15); border-radius:4px;">
            <div style="font-family:'DM Mono',monospace; font-size:0.6rem; letter-spacing:0.14em;
                        text-transform:uppercase; color:#4a4845; margin-bottom:0.3rem;">Analytics</div>
            <div style="font-size:0.75rem; color:#4a4845; line-height:1.6;">
                Add Supabase credentials to secrets.toml to enable live analytics.
            </div>
        </div>
        """, unsafe_allow_html=True)


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


def inject_job_title(base_task: str, job_title: str) -> str:
    if not job_title.strip():
        return base_task
    return base_task + f"""

TARGET JOB TITLE: "{job_title.strip()}"

Use this target job title to sharpen every part of your response:
- Mirror the exact terminology, seniority level, and industry language a \
hiring manager recruiting for this specific role would expect to see
- Prioritise the skills, action verbs, and quantified achievements that carry \
the most weight for a "{job_title.strip()}"
- Rewrite any vague language so it reads as if crafted by — and for — a strong \
candidate actively pursuing this exact title
- Calibrate tone to seniority: junior/associate titles should project energy and \
growth potential; senior/lead/director titles should project authority, scope, and \
measurable business impact
"""


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


def generate_cover_letter(job_desc, resume_text, job_title: str):
    title_clause  = f" for the **{job_title.strip()}** position" if job_title.strip() else ""
    title_persona = (
        f"\n- Write from the perspective of a strong {job_title.strip()} candidate"
        if job_title.strip() else ""
    )
    system_task = f"""You are an expert career coach and professional writer.
Write a compelling, personalized cover letter{title_clause} based on the candidate's \
resume and the job description provided.

The cover letter must:
- Be 3-4 paragraphs, professional but warm in tone
- Open with a strong hook that references the specific role and company
- Highlight 2-3 of the candidate's most relevant experiences from their resume \
that directly match the job requirements
- Include at least one quantified achievement from the resume
- Close with a confident call to action
- NOT use generic filler phrases like "I am writing to express my interest..." \
or "I am a hard worker"
- Sound like a real human wrote it, not a template{title_persona}

Output ONLY the cover letter text. Start directly with "Dear Hiring Manager," \
or a named salutation if available."""

    return call_llm(system_task, f"JOB DESCRIPTION:\n{job_desc}\n\nRESUME:\n{resume_text}", add_score=False)


def get_score_color(score):
    if score < 50:   return "#FF4B4B"
    elif score < 80: return "#FFA500"
    else:            return "#28A745"


# ==============================
# PROGRESS BAR HELPER
# ==============================
def make_progress_ui(steps: list):
    container = st.empty()

    def render(current_i):
        if current_i is None:
            container.empty()
            return

        total   = len(steps) - 1
        bar_pct = int(current_i / total * 100)
        icon, label = steps[current_i]

        dots_html = ""
        for si, (sicon, slabel) in enumerate(steps):
            if si < current_i:
                dot_bg, dot_color, text_color, content = "#28A745", "#0b0c0f", "#28A745", "&#10003;"
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
            f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;'>"
            f"<div style='display:flex; align-items:center; gap:0.6rem;'>"
            f"<div style='width:8px; height:8px; border-radius:50%; background:#c9a84c;"
            f"box-shadow:0 0 10px rgba(201,168,76,0.9);'></div>"
            f"<span style='font-family:DM Mono,monospace; font-size:0.68rem; letter-spacing:0.14em;"
            f"text-transform:uppercase; color:#c9a84c;'>{icon} &nbsp;{label}</span>"
            f"</div>"
            f"<span style='font-family:DM Mono,monospace; font-size:0.78rem;"
            f"font-weight:600; color:#c9a84c;'>{bar_pct}%</span>"
            f"</div>"
            f"<div style='height:6px; background:rgba(201,168,76,0.1); border-radius:3px;"
            f"overflow:hidden; margin-bottom:1.4rem;'>"
            f"<div style='height:6px; width:{bar_pct}%; border-radius:3px;"
            f"background:linear-gradient(90deg,#7a5520,#c9a84c,#e8c87a);'></div></div>"
            f"<div style='display:flex; align-items:flex-start; justify-content:center;'>"
            f"{dots_html}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    return render


def parse_bullet_pairs(text: str) -> list[dict]:
    """Parse ---BULLET--- blocks into list of {original, rewritten} dicts."""
    pairs = []
    blocks = re.findall(r"---BULLET---\s*(.*?)\s*---END---", text, re.DOTALL)
    for block in blocks:
        orig_match = re.search(r"ORIGINAL:\s*(.+?)(?=\nREWRITTEN:)", block, re.DOTALL)
        new_match  = re.search(r"REWRITTEN:\s*(.+?)$",                block, re.DOTALL)
        if orig_match and new_match:
            pairs.append({
                "original":  orig_match.group(1).strip(),
                "rewritten": new_match.group(1).strip(),
            })
    return pairs


def build_updated_resume(original_text: str, pairs: list[dict]) -> str:
    """Replace original bullets in resume text with rewritten versions."""
    updated = original_text
    for p in pairs:
        if p["original"] in updated:
            updated = updated.replace(p["original"], p["rewritten"], 1)
    return updated


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
            AI-Powered &middot; Job-Specific &middot; Interview-Ready
        </div>
        <h1 style="font-family:'Cormorant Garamond',Georgia,serif;
                   font-size:clamp(2.6rem,5.5vw,4.6rem); font-weight:300;
                   line-height:1.05; color:#f0ede6; margin-bottom:0.7rem; letter-spacing:-0.01em;">
            Resume<em style="color:#c9a84c; font-style:italic;">Forge</em>
        </h1>
        <p style="font-family:'DM Sans',sans-serif; font-size:0.98rem; color:#9a958f;
                  font-weight:300; max-width:500px; line-height:1.75; margin:0;">
            Paste a job description, upload your resume &mdash; and let AI sculpt
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
    <span style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.16em; text-transform:uppercase; color:#c9a84c;">&#9312; Upload Resume</span>
    <span style="color:rgba(201,168,76,0.2);">&#9472;&#9472;&#9472;&#9472;</span>
    <span style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.16em; text-transform:uppercase; color:#c9a84c;">&#9313; Job Description</span>
    <span style="color:rgba(201,168,76,0.2);">&#9472;&#9472;&#9472;&#9472;</span>
    <span style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.16em; text-transform:uppercase; color:#c9a84c;">&#9314; Choose Goal</span>
    <span style="color:rgba(201,168,76,0.2);">&#9472;&#9472;&#9472;&#9472;</span>
    <span style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.16em; text-transform:uppercase; color:#c9a84c;">&#9315; Run</span>
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
# GOAL + JOB TITLE
# ==============================
BULLET_PROMPT = """Extract every work-experience bullet point from the resume and rewrite each one to highlight measurable achievements and strong action verbs.

CRITICAL — output ONLY in this exact format, one block per bullet, no extra text before or after:

---BULLET---
ORIGINAL: [paste the exact original bullet point here]
REWRITTEN: [your improved version here]
---END---

Rules:
- Include every bullet point from every job, not just a few
- Keep ORIGINAL as the exact text from the resume (do not paraphrase it)
- REWRITTEN should use strong action verbs, quantified outcomes, and results-driven language
- Do not add any intro text, section headers, commentary, or explanation — only the ---BULLET--- blocks"""

prompt_options = {
    "✦  ATS Keyword Optimization":     "Analyze the Job Description for top keywords and modify my resume bullet points to include them naturally.",
    "✦  Rewrite Bullets with Impact":  BULLET_PROMPT,
    "✦  Professional Summary Rewrite": "Draft a compelling 3-4 sentence professional summary that bridges my current experience with this specific job.",
    "✦  Skills Gap Analysis":          "Compare my resume against the job description. Identify exactly what hard and soft skills I am currently missing.",
}

col3, col4 = st.columns([1.2, 1], gap="large")
with col3:
    selected_strategy = st.selectbox("Choose Your Goal", list(prompt_options.keys()))
with col4:
    job_title = st.text_input(
        "Target Job Title (Optional)",
        placeholder="e.g. Senior Data Engineer, Product Manager, UX Designer...",
        help="Providing a job title anchors the AI's vocabulary, seniority tone, and keyword priority to that specific role."
    )

st.markdown("<br/>", unsafe_allow_html=True)

is_ats     = "ATS"     in selected_strategy
is_bullets = "Bullets" in selected_strategy
if is_ats:
    st.markdown("""
    <div style="display:inline-flex; align-items:center; gap:0.6rem;
                background:rgba(201,168,76,0.07); border:1px solid rgba(201,168,76,0.2);
                border-radius:20px; padding:0.35rem 0.9rem; margin-bottom:1rem;">
        <span style="color:#c9a84c; font-size:0.75rem;">&#10022;</span>
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
        st.warning("Please upload a resume to get started.")
    elif not job_desc.strip():
        st.warning("Please paste a job description to match against.")
    else:
        system_task = inject_job_title(prompt_options[selected_strategy], job_title)

        track(EV_RUN)
        track(GOAL_EVENTS.get(selected_strategy, "goal_other"))

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
            ("✉️", "Generating cover letter"),
            ("✅", "Complete"),
        ]
        steps = steps_cover if is_ats else steps_base
        total = len(steps) - 1

        render_progress = make_progress_ui(steps)

        render_progress(0)
        resume_text = extract_text(resume_file)

        render_progress(1)
        _time.sleep(0.35)

        render_progress(2)
        result = call_llm(system_task, f"JOB DESCRIPTION:\n{job_desc}\n\nRESUME:\n{resume_text}")

        cover_letter_text = ""
        if is_ats and result:
            render_progress(3)
            cover_letter_text = generate_cover_letter(job_desc, resume_text, job_title)
            if cover_letter_text:
                track(EV_COVER)

        render_progress(total)
        _time.sleep(0.6)
        render_progress(None)

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

                title_badge = (
                    f"&nbsp;&middot;&nbsp;<span style='color:#c9a84c;'>{job_title.strip()}</span>"
                    if job_title.strip() else ""
                )
                st.markdown(f"""
                <div style="padding:0.85rem 1.3rem; background:rgba(40,167,69,0.07);
                            border:1px solid rgba(40,167,69,0.28); border-radius:3px;
                            margin-bottom:1.4rem; font-family:'DM Mono',monospace;
                            font-size:0.68rem; letter-spacing:0.14em; text-transform:uppercase; color:#28A745;">
                    &#10003; &nbsp; Analysis complete &middot; {PROVIDER.split('(')[0].strip()}{title_badge}
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
                            Resume &ndash; Job Alignment
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

            title_pill = (
                f"<span style='display:inline-block; background:rgba(201,168,76,0.1); "
                f"border:1px solid rgba(201,168,76,0.28); border-radius:20px; "
                f"padding:0.18rem 0.8rem; font-family:DM Mono,monospace; font-size:0.58rem; "
                f"letter-spacing:0.12em; text-transform:uppercase; color:#c9a84c; "
                f"vertical-align:middle; margin-left:0.8rem;'>{job_title.strip()}</span>"
                if job_title.strip() else ""
            )

            st.markdown(f"""
            <div style="margin-bottom:1.1rem;">
                <div style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.2em;
                            text-transform:uppercase; color:#c9a84c; margin-bottom:0.35rem;
                            display:flex; align-items:center; gap:0.6rem;">
                    <span style="display:inline-block;width:18px;height:1px;background:#c9a84c;"></span>Results
                </div>
                <div style="font-family:'Cormorant Garamond',serif; font-size:1.75rem;
                            font-weight:300; color:#f0ede6; display:flex; align-items:center; flex-wrap:wrap;">
                    {selected_strategy.replace("✦  ", "")}{title_pill}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── BULLET COMPARISON UI ──────────────────────────────────────
            if is_bullets:
                bullet_pairs = parse_bullet_pairs(display_text)

                if bullet_pairs:
                    st.markdown(f"""
                    <div style="margin-bottom:1.4rem;">
                        <div style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.2em;
                                    text-transform:uppercase; color:#c9a84c; margin-bottom:0.35rem;
                                    display:flex; align-items:center; gap:0.6rem;">
                            <span style="display:inline-block;width:18px;height:1px;background:#c9a84c;"></span>Results
                        </div>
                        <div style="font-family:'Cormorant Garamond',serif; font-size:1.75rem;
                                    font-weight:300; color:#f0ede6; margin-bottom:0.3rem;">
                            Impact Bullet Rewriting{title_pill}
                        </div>
                        <p style="font-size:0.85rem; color:#9a958f; font-weight:300; margin:0; line-height:1.7;">
                            {len(bullet_pairs)} bullet{"s" if len(bullet_pairs) != 1 else ""} rewritten.
                            Review each change, then apply and download your updated resume.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Column headers
                    h1, h2 = st.columns(2, gap="large")
                    with h1:
                        st.markdown("""
                        <div style="font-family:'DM Mono',monospace; font-size:0.6rem; letter-spacing:0.16em;
                                    text-transform:uppercase; color:#6a6560; padding:0.5rem 0.8rem;
                                    background:#0b0c0f; border:1px solid rgba(255,255,255,0.06);
                                    border-radius:4px 4px 0 0; text-align:center;">
                            ✗ &nbsp; Before
                        </div>
                        """, unsafe_allow_html=True)
                    with h2:
                        st.markdown("""
                        <div style="font-family:'DM Mono',monospace; font-size:0.6rem; letter-spacing:0.16em;
                                    text-transform:uppercase; color:#c9a84c; padding:0.5rem 0.8rem;
                                    background:#0b0c0f; border:1px solid rgba(201,168,76,0.25);
                                    border-radius:4px 4px 0 0; text-align:center;">
                            ✦ &nbsp; After
                        </div>
                        """, unsafe_allow_html=True)

                    # Bullet rows
                    for i, pair in enumerate(bullet_pairs):
                        c1, c2 = st.columns(2, gap="large")
                        bg_row = "#0d0e12" if i % 2 == 0 else "#111318"
                        with c1:
                            st.markdown(
                                f"<div style='background:{bg_row}; border:1px solid rgba(255,255,255,0.05);"
                                f"border-top:none; padding:0.85rem 1rem; font-size:0.88rem;"
                                f"color:#6a6560; line-height:1.7; min-height:60px;'>"
                                f"— &nbsp;{pair['original']}</div>",
                                unsafe_allow_html=True
                            )
                        with c2:
                            st.markdown(
                                f"<div style='background:{bg_row}; border:1px solid rgba(201,168,76,0.12);"
                                f"border-top:none; padding:0.85rem 1rem; font-size:0.88rem;"
                                f"color:#f0ede6; line-height:1.7; min-height:60px;'>"
                                f"<span style='color:#c9a84c; font-size:0.7rem;'>✦</span>"
                                f"&nbsp;{pair['rewritten']}</div>",
                                unsafe_allow_html=True
                            )

                    st.markdown("<br/>", unsafe_allow_html=True)

                    # Apply + download
                    st.markdown("""
                    <div style="padding:1.2rem 1.5rem; background:rgba(201,168,76,0.06);
                                border:1px solid rgba(201,168,76,0.2); border-radius:6px;
                                margin-bottom:1rem;">
                        <div style="font-family:'DM Mono',monospace; font-size:0.62rem;
                                    letter-spacing:0.14em; text-transform:uppercase;
                                    color:#c9a84c; margin-bottom:0.4rem;">&#10022; Apply Changes</div>
                        <p style="font-size:0.83rem; color:#9a958f; margin:0; line-height:1.7;">
                            Click <strong style='color:#f0ede6;'>Apply &amp; Download</strong> to
                            replace every original bullet in your resume with the rewritten version
                            and download the updated file.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Store updated resume in session state on Apply
                    if "updated_resume" not in st.session_state:
                        st.session_state.updated_resume = None

                    ac1, ac2, ac3, _ = st.columns([1.3, 1.2, 1.2, 3])
                    with ac1:
                        if st.button("✦  Apply Changes", type="primary", key="apply_bullets"):
                            st.session_state.updated_resume = build_updated_resume(resume_text, bullet_pairs)
                            st.success(f"✓  {len(bullet_pairs)} bullets applied to your resume.")

                    if st.session_state.updated_resume:
                        with ac2:
                            st.download_button(
                                "↓  Download .txt",
                                data=st.session_state.updated_resume,
                                file_name="resume_updated.txt",
                                mime="text/plain",
                                key="dl_updated_txt"
                            )
                        with ac3:
                            st.download_button(
                                "↓  Download .doc",
                                data=st.session_state.updated_resume.replace("\n", "\r\n"),
                                file_name="resume_updated.doc",
                                mime="application/msword",
                                key="dl_updated_doc"
                            )
                else:
                    # Fallback: model didn't use structured format
                    st.markdown(display_text)
                    st.markdown("<br/>", unsafe_allow_html=True)
                    dcol1, _ = st.columns([1, 4])
                    with dcol1:
                        st.download_button(
                            "↓  Download Analysis", data=display_text,
                            file_name="resume_analysis.txt", mime="text/plain"
                        )

            # ── ALL OTHER GOALS ──────────────────────────────────────────
            else:
                st.markdown(display_text)
                st.markdown("<br/>", unsafe_allow_html=True)

                dcol1, _ = st.columns([1, 4])
                with dcol1:
                    st.download_button(
                        "↓  Download Analysis", data=display_text,
                        file_name="resume_analysis.txt", mime="text/plain"
                    )

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
                                 letter-spacing:0.14em; text-transform:uppercase; color:#c9a84c;">&#10022; Tip</span>
                    <p style="font-family:'DM Sans',sans-serif; font-size:0.82rem; color:#9a958f;
                              margin:0.3rem 0 0; line-height:1.7;">
                        Personalise the opening line with the hiring manager's name if you can find it on LinkedIn.
                        A named salutation can increase response rates by up to 20%.
                    </p>
                </div>
                """, unsafe_allow_html=True)
