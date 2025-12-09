import streamlit as st
import time
from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup
from openai import OpenAI
import google.generativeai as genai
#pip install pytesseract pillow pdf2image


# ---------------- PROVIDER SWITCH ----------------

PROVIDER = st.selectbox(
    "Choose LLM:",
    ["Open-source (Mistral)", "Closed-source (Gemini)"]
)

# ---------------- CLIENT SETUP ----------------

if PROVIDER == "Open-source (Mistral)":
    client = OpenAI(
        api_key=st.secrets["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1"
    )
    MODEL_NAME = "mistralai/mistral-7b-instruct"
else:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")


# ---------------- PROMPTS ----------------

SUMMARY_PROMPT = """
Summarize the following document text.
Preserve definitions, abbreviations, and key findings.
"""

QA_PROMPT = """
You are answering questions using the document content below.
Answer as accurately as possible.
If the document only partially answers the question, answer with uncertainty noted.
"""

FALLBACK_RESPONSE = """I couldn’t find enough information in the document to answer confidently."""

# ---------------- DOCUMENT EXTRACTION ----------------

def extract_text(file):
    # NOTE: This function currently only handles PDFs.
    # You will need to add logic for .txt, .docx, and .html
    # if you want to support those file types in the uploader.
    reader = PdfReader(file)
    pages = []

    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text()
            if text and len(text.strip()) > 100:
                pages.append(text)
        except Exception:
            continue

    return "\n".join(pages)

# The problematic code snippet has been removed from here
# and moved into the `if uploaded_file:` block below.


# ---------------- CHUNKING ----------------

def chunk_text(text, max_chars=1800):
    chunks, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) <= max_chars:
            current += line + "\n"
        else:
            chunks.append(current)
            current = line + "\n"
    if current.strip():
        chunks.append(current)
    return chunks

# ---------------- LLM CALL ----------------

def call_llm(prompt, text):
    try:
        if PROVIDER == "Open-source (Mistral)":
            r = client.chat.completions.create(
                model=MODEL_NAME,
                temperature=0,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ]
            )
            return r.choices[0].message.content.strip()

        else:
            r = gemini_model.generate_content(
                f"{prompt}\n\n{text}",
                generation_config={"temperature": 0}
            )
            return r.text.strip()

    except Exception as e:
        st.warning(f"LLM error: {e}")
        return ""

# ---------------- UI ----------------

st.title("📄 Document Q&A (Open-source ↔ Gemini)")

uploaded_file = st.file_uploader(
    "Upload document",
    type=["pdf", "txt", "docx", "html"]
)

question = st.chat_input("Ask a question about the document")

if uploaded_file:
    text = extract_text(uploaded_file)

    # MOVED: The validation check is now safely inside this block
    if not text or len(text.strip()) < 500:
        st.error("Unable to extract readable text from this PDF. The document may be scanned or image-based.")
        st.stop()
        
    chunks = chunk_text(text)

    # Step 1: 
    SUMMARY_PROMPT = """
You are summarizing an academic article.

Rules:
- Use ONLY information explicitly present in the text
- Do NOT add generic academic commentary
- If the content is unclear or incomplete, say so
- Preserve technical terms and abbreviations

Return a concise factual summary.
"""

    summaries = []
    with st.spinner("Understanding document..."):
        for c in chunks:
            s = call_llm(SUMMARY_PROMPT, c)
            if s:
                summaries.append(s)
            time.sleep(0.2)

    doc_summary = "\n".join(summaries)

    if question:
        answer = call_llm(
            QA_PROMPT,
            f"Document summary:\n{doc_summary}\n\nQuestion:\n{question}"
        )

        st.chat_message("assistant").markdown(
            answer if answer else FALLBACK_RESPONSE
        )
