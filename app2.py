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

# Clean light theme
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg:         #f7f5f0;
    --bg2:        #ffffff;
    --bg3:        #edeae3;
    --gold:       #a0732a;
    --gold-light: #c9a84c;
    --border:     rgba(160,115,42,0.25);
    --text:       #1a1612;
    --muted:      #6b6560;
    --serif:      'Cormorant Garamond', Georgia, serif;
    --sans:       'DM Sans', sans-serif;
    --mono:       'DM Mono', monospace;
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

/* Sidebar text */
[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

/* Text area */
.stTextArea textarea {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
}
.stTextArea textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px rgba(160,115,42,0.12) !important;
}

/* Selectbox & labels */
.stSelectbox label, .stTextArea label, .stFileUploader label {
    color: var(--muted) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

/* Button */
.stButton > button {
    background: var(--gold) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.03em !important;
    padding: 0.6rem 1.5rem !important;
    width: 100%;
    transition: background 0.2s ease !important;
}
.stButton > button:hover {
    background: var(--gold-light) !important;
}

/* Result box */
.reasoning-box {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 2rem;
    line-height: 1.85;
    white-space: pre-wrap;
    color: var(--text);
    font-size: 0.97rem;
    position: relative;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.reasoning-box::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    border-radius: 8px 8px 0 0;
    background: linear-gradient(90deg, var(--gold), var(--gold-light), transparent);
}

/* File badge */
.file-badge {
    display: inline-block;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
    color: var(--gold);
    margin-top: 0.5rem;
    font-weight: 500;
}

/* Divider */
hr {
    border-color: var(--border) !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# HELPERS
# ==============================
def extract_text(file) -> tuple[str, str]:
    """
    Returns (extracted_text, file_type_label).
    Supports: PDF, DOCX, TXT, PNG/JPG/JPEG (OCR), XLS, XLSX, CSV.
    """
    ext = file.name.split(".")[-1].lower()
    try:
        # ── PDF ──────────────────────────────────────────────
        if ext == "pdf":
            reader = PdfReader(file)
            pages_text = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages_text.append(f"[Page {i+1}]\n{page_text}")
            return "\n\n".join(pages_text), "PDF"

        # ── Word Document ─────────────────────────────────────
        elif ext == "docx":
            doc = Document(file)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

            # Also extract tables from the docx
            table_texts = []
            for i, table in enumerate(doc.tables):
                rows = []
                for row in table.rows:
                    rows.append(" | ".join(cell.text.strip() for cell in row.cells))
                table_texts.append(f"[Table {i+1}]\n" + "\n".join(rows))

            combined = "\n".join(paragraphs)
            if table_texts:
                combined += "\n\n" + "\n\n".join(table_texts)
            return combined, "DOCX"

        # ── Excel / CSV ───────────────────────────────────────
        elif ext in ["xlsx", "xls"]:
            xls = pd.ExcelFile(file)
            sheet_texts = []
            for sheet_name in xls.sheet_names:
                df = xls.parse(sheet_name)
                df = df.dropna(how="all").fillna("")      # clean empty rows/cells
                sheet_md = df.to_markdown(index=False)   # clean table-style text
                sheet_texts.append(f"[Sheet: {sheet_name}]\n{sheet_md}")
            return "\n\n".join(sheet_texts), "Excel"

        elif ext == "csv":
            df = pd.read_csv(file).fillna("")
            return df.to_markdown(index=False), "CSV"

        # ── Images (OCR) ──────────────────────────────────────
        elif ext in ["png", "jpg", "jpeg"]:
            img = Image.open(file)
            text = pytesseract.image_to_string(img)
            return text, "Image (OCR)"

        # ── Plain Text ────────────────────────────────────────
        else:
            return file.read().decode("utf-8"), "Text"

    except Exception as e:
        st.error(f"Extraction error: {e}")
        return "", "Unknown"


def get_llm_response(prompt, provider):
    try:
        # 1. DeepSeek R1
        if "DeepSeek" in provider:
            client = OpenAI(
                api_key=st.secrets["OPENROUTER_API_KEY"],
                base_url="https://openrouter.ai/api/v1"
            )
            response = client.chat.completions.create(
                model="deepseek/deepseek-r1",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

        # 2. OpenAI o1-mini
        elif "OpenAI" in provider:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="o1-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

        # 3. Gemini 2.0 Flash
        elif "Gemini" in provider:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text

    except Exception as e:
        return f"Error connecting to {provider}: {str(e)}"


# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("### ✦ Settings")
    PROVIDER = st.selectbox(
        "Reasoning Engine",
        ["DeepSeek R1 (Reasoning Expert)", "OpenAI o1-mini (Logic Focused)", "Gemini 2.0 Flash"]
    )

    st.markdown("---")
    st.markdown("**Attach Context File**")
    st.caption("Supported: PDF · DOCX · XLS · XLSX · CSV · PNG · JPG · TXT")
    uploaded_files = st.file_uploader(
    "Upload files",
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "xlsx", "xls", "csv"],
    accept_multiple_files=True,  # This is the key change
    label_visibility="collapsed"
)

    # Show a preview badge when file is loaded
    if uploaded_file:
        _, ftype = extract_text(uploaded_file)
        uploaded_file.seek(0)   # reset pointer after peek
        st.markdown(f"<span class='file-badge'>📎 {uploaded_file.name} · {ftype}</span>", unsafe_allow_html=True)

# ==============================
# MAIN INTERFACE
# ==============================
st.markdown("""
<h1 style="font-family:'Cormorant Garamond'; font-size:3.5rem; font-weight:300;">
    Reasoning <em style="color:#a0732a; font-style:italic;">Forge</em>
</h1>
""", unsafe_allow_html=True)

user_query = st.text_area(
    "Define your problem:",
    height=200,
    placeholder="Ask a complex question or explain what to do with the uploaded file..."
)

if st.button("✦ Start Reasoning"):
    if not user_query:
        st.warning("Please enter a question or instruction.")
    else:
        all_context = []
        
        if uploaded_files:
            with st.spinner(f"Processing {len(uploaded_files)} files..."):
                for file in uploaded_files:
                    file.seek(0)
                    context_text, ftype = extract_text(file)
                    if context_text.strip():
                        # Add a header for each file so the AI knows which is which
                        all_context.append(f"--- START OF FILE: {file.name} ({ftype}) ---\n{context_text}\n--- END OF FILE ---")
            
            if all_context:
                final_context = "\n\n".join(all_context)
                final_prompt = f"CONTEXT FROM MULTIPLE FILES:\n{final_context}\n\nUSER QUESTION:\n{user_query}"
                st.info(f"✔ Combined context from {len(uploaded_files)} files loaded.")
            else:
                final_prompt = user_query
        else:
            final_prompt = user_query

        with st.spinner(f"{PROVIDER} is analyzing..."):
            # The rest of your LLM call logic remains the same
            answer = get_llm_response(final_prompt, PROVIDER)
            # ... (your display logic)
