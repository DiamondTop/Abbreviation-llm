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
import datetime
import html

# ==============================
# PAGE CONFIG & STYLES
# ==============================
st.set_page_config(
    page_title="Reasoning Forge",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    transition: background 0.2s ease !important;
}
.stButton > button:hover {
    background: var(--gold-light) !important;
}

/* Download button — outlined to distinguish from primary */
.stDownloadButton > button {
    background: transparent !important;
    color: var(--gold) !important;
    border: 1.5px solid var(--gold) !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    width: 100%;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    background: var(--gold) !important;
    color: #ffffff !important;
}

/* FIX: white-space:normal removes giant blank gaps from LLM newlines */
.reasoning-box {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 2rem;
    white-space: normal;
    word-wrap: break-word;
    line-height: 1.85;
    color: var(--text);
    position: relative;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.reasoning-box::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    border-radius: 8px 8px 0 0;
    background: linear-gradient(90deg, var(--gold), var(--gold-light), transparent);
}
.reasoning-box p {
    margin: 0 0 0.75em 0;
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

.result-meta {
    font-size: 0.78rem;
    color: var(--muted);
    margin-bottom: 0.75rem;
    font-style: italic;
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


def format_for_display(text: str) -> str:
    """Convert LLM plain-text into clean HTML paragraphs — no giant blank gaps."""
    escaped = html.escape(text)
    # Split on 2+ newlines = paragraph break
    paragraphs = re.split(r'\n{2,}', escaped.strip())
    parts = []
    for para in paragraphs:
        # Single newlines within a paragraph → <br>
        para = para.replace('\n', '<br>')
        parts.append(f"<p>{para}</p>")
    return "".join(parts)


def build_download_text(question: str, answer: str, provider: str, files: list) -> str:
    """Plain-text export of the full session."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_names = ", ".join(f.name for f in files) if files else "None"
    div = "=" * 60
    return (
        f"REASONING FORGE — EXPORT\n{div}\n"
        f"Date      : {timestamp}\n"
        f"Engine    : {provider}\n"
        f"Files     : {file_names}\n"
        f"{div}\n\n"
        f"QUESTION\n{question}\n\n"
        f"{div}\n\n"
        f"ANSWER\n{answer}\n"
    )


def get_llm_response(prompt, provider):
    try:
        client = OpenAI(
            api_key=st.secrets["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1"
        )

        if "Metal-llama" in provider:
            model_id = "meta-llama/llama-3.1-8b-instruct:free"
        elif "nemotron-3 by Nvidia" in provider:
            model_id = "nvidia/nemotron-3-super-120b-a12b:free"
        elif "Stepfun" in provider:
            model_id = "stepfun/step-3.5-flash:free"
        else:
            model_id = "meta-llama/llama-3.1-8b-instruct:free"

        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            extra_headers={
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "Reasoning Forge"
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("### ✦ Settings")
    PROVIDER = st.selectbox(
        "Reasoning Engine",
        ["Metal-llama (Reasoning Expert)", "nemotron-3 by Nvidia (Logic Focused)", "Stepfun"]
    )
    st.markdown("---")
    st.markdown("**Attach Context Files**")
    uploaded_files = st.file_uploader(
        "Upload files",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "xlsx", "xls", "csv"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    if uploaded_files:
        for f in uploaded_files:
            st.markdown(f"<span class='file-badge'>📎 {f.name}</span>", unsafe_allow_html=True)

# ==============================
# MAIN INTERFACE
# ==============================
st.markdown(
    "<h1 style='font-family:Cormorant Garamond; font-size:3.5rem; font-weight:300; margin-bottom:0;'>"
    "Reasoning <em style='color:#a0732a; font-style:italic;'>Forge</em></h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='color:#6b6560; margin-top:0.25rem; margin-bottom:1.5rem;'>"
    "Powered by AI · Seek reasoning · Upload any files</p>",
    unsafe_allow_html=True
)

user_query = st.text_area(
    "Define your problem:",
    height=180,
    placeholder="Ask a question about the uploaded files, or pose any complex problem..."
)

if st.button("✦ Start Reasoning"):
    if not user_query:
        st.warning("Please enter a question.")
    else:
        # ── Extract file context ─────────────────────────────
        combined_context = ""
        if uploaded_files:
            with st.spinner(f"Extracting data from {len(uploaded_files)} file(s)..."):
                for f in uploaded_files:
                    f.seek(0)
                    text, ftype = extract_text(f)
                    combined_context += f"\n\n--- FILE: {f.name} ({ftype}) ---\n{text}\n"

        final_prompt = (
            f"CONTEXT:\n{combined_context}\n\nUSER QUESTION:\n{user_query}"
            if combined_context else user_query
        )

        # ── Call LLM ─────────────────────────────────────────
        with st.spinner(f"{PROVIDER} is thinking..."):
            answer = get_llm_response(final_prompt, PROVIDER)

        st.markdown("---")
        st.markdown("### ✦ Analysis Result")

        # Strip <think> block if present (DeepSeek-style models)
        clean_answer = answer
        if "<think>" in answer and "</think>" in answer:
            parts = answer.split("</think>")
            thought = parts[0].replace("<think>", "").strip()
            clean_answer = parts[1].strip()
            with st.expander("View Reasoning Process", expanded=False):
                st.markdown(f"*{thought}*")

        # Meta line
        ts = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
        st.markdown(f"<p class='result-meta'>Generated {ts} · {PROVIDER}</p>", unsafe_allow_html=True)

        # Result box — properly formatted, no blank-space gaps
        st.markdown(
            f"<div class='reasoning-box'>{format_for_display(clean_answer)}</div>",
            unsafe_allow_html=True
        )

        # ── Download button ──────────────────────────────────
        st.markdown("<div style='margin-top:1rem;'>", unsafe_allow_html=True)
        download_content = build_download_text(user_query, clean_answer, PROVIDER, uploaded_files or [])
        filename = f"reasoning_forge_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        st.download_button(
            label="⬇ Download Result",
            data=download_content,
            file_name=filename,
            mime="text/plain"
        )
        st.markdown("</div>", unsafe_allow_html=True)
