import streamlit as st
import re
import time
import datetime
import html
from PIL import Image
import pytesseract
from pypdf import PdfReader
from docx import Document
import pandas as pd
from openai import OpenAI

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

/* ── Chat bubbles ── */
.bubble-user {
    background: var(--gold);
    color: #ffffff;
    border-radius: 16px 16px 4px 16px;
    padding: 0.85rem 1.2rem;
    margin: 0.5rem 0 0.5rem 15%;
    line-height: 1.65;
    font-size: 0.95rem;
    word-wrap: break-word;
}

.bubble-ai {
    background: var(--bg2);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 16px 16px 16px 4px;
    padding: 0.85rem 1.2rem;
    margin: 0.5rem 15% 0.1rem 0;
    line-height: 1.75;
    font-size: 0.95rem;
    word-wrap: break-word;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    position: relative;
}
.bubble-ai::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    border-radius: 16px 16px 0 0;
    background: linear-gradient(90deg, var(--gold), var(--gold-light), transparent);
}
.bubble-ai p { margin: 0 0 0.6em 0; }
.bubble-ai p:last-child { margin-bottom: 0; }

.bubble-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--muted);
    margin-bottom: 0.2rem;
}
.label-user { text-align: right; margin-right: 0.2rem; }
.label-ai   { text-align: left;  margin-left:  0.2rem; }

/* ── Timing badge ── */
.timing-badge {
    font-size: 0.72rem;
    color: var(--muted);
    margin: 0.2rem 0 0.9rem 0.3rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.timing-bar {
    display: inline-block;
    height: 3px;
    border-radius: 2px;
    background: linear-gradient(90deg, var(--gold), var(--gold-light));
    vertical-align: middle;
}

/* ── Input area ── */
.stTextArea textarea {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--gold) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    width: 100%;
    transition: background 0.2s ease !important;
}
.stButton > button:hover { background: var(--gold-light) !important; }

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

/* ── File badge ── */
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

/* ── Divider ── */
.turn-divider {
    border: none;
    border-top: 1px dashed var(--border);
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# SESSION STATE INIT
# ==============================
if "messages"      not in st.session_state: st.session_state.messages      = []
if "file_context"  not in st.session_state: st.session_state.file_context  = ""
if "file_names"    not in st.session_state: st.session_state.file_names    = []
# input_counter: incrementing this generates a brand-new widget key,
# which clears the box — without ever writing to a widget-bound state key.
if "input_counter" not in st.session_state: st.session_state.input_counter = 0
# saved_input: preserves typed text across non-send reruns (e.g. file upload)
if "saved_input"   not in st.session_state: st.session_state.saved_input   = ""

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
    escaped = html.escape(text)
    paragraphs = re.split(r'\n{2,}', escaped.strip())
    return "".join(
        f"<p>{para.replace(chr(10), '<br>')}</p>"
        for para in paragraphs
    )


def elapsed_label(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{int(seconds // 60)}m {seconds % 60:.0f}s"


def save_input():
    """on_change callback — keeps saved_input in sync as the user types."""
    current_key = f"input_{st.session_state.input_counter}"
    st.session_state.saved_input = st.session_state.get(current_key, "")


def build_messages_for_api(file_context: str, history: list) -> list:
    api_messages = []
    for i, msg in enumerate(history):
        content = msg["content"]
        if i == 0 and msg["role"] == "user" and file_context:
            content = f"CONTEXT FROM FILES:\n{file_context}\n\n---\n\nUSER: {content}"
        api_messages.append({"role": msg["role"], "content": content})
    return api_messages


def get_llm_response(history: list, file_context: str, provider: str) -> tuple[str, float]:
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

        api_messages = build_messages_for_api(file_context, history)

        t0 = time.time()
        response = client.chat.completions.create(
            model=model_id,
            messages=api_messages,
            extra_headers={
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "Reasoning Forge"
            }
        )
        elapsed = time.time() - t0
        return response.choices[0].message.content, elapsed

    except Exception as e:
        return f"Error: {str(e)}", 0.0


def build_download_text(history: list, provider: str, file_names: list) -> str:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    files_str = ", ".join(file_names) if file_names else "None"
    div = "=" * 60
    lines = [
        "REASONING FORGE — CONVERSATION EXPORT",
        div,
        f"Date    : {timestamp}",
        f"Engine  : {provider}",
        f"Files   : {files_str}",
        div, ""
    ]
    for i, msg in enumerate(history):
        role_label = "YOU" if msg["role"] == "user" else "AI"
        elapsed    = msg.get("elapsed")
        lines.append(f"[{role_label}]")
        if elapsed is not None:
            lines.append(f"  ⏱ Generated in {elapsed_label(elapsed)}")
        lines.append(msg["content"] + "\n")
        if i < len(history) - 1:
            lines.append("-" * 40)
    return "\n".join(lines)


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
    st.caption("Files are loaded into every conversation turn automatically.")
    uploaded_files = st.file_uploader(
        "Upload files",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "xlsx", "xls", "csv"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    current_names = [f.name for f in uploaded_files] if uploaded_files else []
    if current_names != st.session_state.file_names:
        if uploaded_files:
            combined = ""
            for f in uploaded_files:
                f.seek(0)
                text, ftype = extract_text(f)
                combined += f"\n\n--- FILE: {f.name} ({ftype}) ---\n{text}\n"
            st.session_state.file_context = combined
        else:
            st.session_state.file_context = ""
        st.session_state.file_names = current_names

    if uploaded_files:
        for f in uploaded_files:
            st.markdown(f"<span class='file-badge'>📎 {f.name}</span>", unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🗑 Clear Conversation"):
        st.session_state.messages     = []
        st.session_state.saved_input  = ""
        st.session_state.input_counter += 1   # reset the text box too
        st.rerun()

    if st.session_state.messages:
        download_content = build_download_text(
            st.session_state.messages, PROVIDER, st.session_state.file_names
        )
        filename = f"reasoning_forge_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        st.download_button(
            label="⬇ Download Conversation",
            data=download_content,
            file_name=filename,
            mime="text/plain"
        )

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
    "Powered by AI · Multi-turn conversation · Upload any files</p>",
    unsafe_allow_html=True
)

# ── Render conversation history ──────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown("<p class='bubble-label label-user'>You</p>", unsafe_allow_html=True)
        st.markdown(f"<div class='bubble-user'>{html.escape(msg['content'])}</div>", unsafe_allow_html=True)
    else:
        content = msg["content"]
        if "<think>" in content and "</think>" in content:
            content = content.split("</think>")[-1].strip()

        elapsed = msg.get("elapsed")

        st.markdown("<p class='bubble-label label-ai'>✦ Reasoning Forge</p>", unsafe_allow_html=True)
        st.markdown(f"<div class='bubble-ai'>{format_for_display(content)}</div>", unsafe_allow_html=True)

        if elapsed is not None:
            bar_px = min(int(elapsed * 8), 140)
            st.markdown(
                f"<div class='timing-badge'>"
                f"<span class='timing-bar' style='width:{bar_px}px'></span>"
                f"⏱ Generated in {elapsed_label(elapsed)}"
                f"</div>",
                unsafe_allow_html=True
            )

if st.session_state.messages:
    st.markdown("<hr class='turn-divider'>", unsafe_allow_html=True)

# ── Input box ────────────────────────────────────────────────
# Key changes on send (input_counter increments) → widget resets cleanly.
# Key stays the same on file-upload reruns → typed text is preserved.
# on_change keeps saved_input in sync so the value survives any rerun.
input_key = f"input_{st.session_state.input_counter}"

user_query = st.text_area(
    "Your message:" if st.session_state.messages else "Define your problem:",
    height=130,
    placeholder="Continue the conversation, or ask a follow-up question...",
    value=st.session_state.saved_input,
    key=input_key,
    on_change=save_input,
)

send = st.button("✦ Send" if st.session_state.messages else "✦ Start Reasoning")

# ── Handle send ──────────────────────────────────────────────
if send:
    query = st.session_state.get(input_key, "").strip()
    if not query:
        st.warning("Please enter a message.")
    else:
        st.session_state.messages.append({
            "role": "user", "content": query, "elapsed": None
        })

        with st.spinner(f"{PROVIDER} is thinking..."):
            reply, elapsed = get_llm_response(
                st.session_state.messages,
                st.session_state.file_context,
                PROVIDER
            )

        st.session_state.messages.append({
            "role": "assistant", "content": reply, "elapsed": elapsed
        })

        # Clear input: reset saved text and generate a new widget key
        st.session_state.saved_input   = ""
        st.session_state.input_counter += 1
        st.rerun()
