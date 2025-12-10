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

PROVIDER = st.selectbox(
    "Choose LLM:",
    ["Open-source (Mistral)", "Closed-source (Gemini)"]
)

# ==============================
# CLIENT SETUP
# ==============================

if PROVIDER == "Open-source (Mistral)":
    client = OpenAI(
        api_key=st.secrets["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1"
    )
    MODEL_NAME = "mistralai/mistral-7b-instruct"
else:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# ==============================
# PROMPTS
# ==============================

ABBREVIATION_PROMPT = """
Extract ALL abbreviations and their definitions from the text below.

Rules:
- Only include abbreviations explicitly defined in the text
- Use exact wording from the document
- Format strictly as: ABBREVIATION = Full Term
- One entry per line
- Do NOT guess or hallucinate
"""

QA_PROMPT = """
Answer the question using ONLY the document content below.

If the answer is not clearly present, reply exactly:
"I don’t have enough information in the document to answer that."
"""

CHAT_PROMPT = """
You are a helpful AI assistant.
Answer the user naturally and clearly.
"""

FALLBACK_RESPONSE = "I don’t have enough information to answer that."

# ==============================
# DOCUMENT EXTRACTION (PAGE-BASED)
# ==============================

def extract_document_pages(file):
    ext = file.name.split(".")[-1].lower()

    if ext == "pdf":
        reader = PdfReader(file)
        pages = []
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if text and len(text.strip()) > 200:
                    pages.append((i + 1, text))
            except Exception:
                continue
        return pages

    elif ext == "txt":
        text = file.read().decode("utf-8", errors="ignore")
        return [(1, text)]

    elif ext == "docx":
        doc = Document(file)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [(1, text)]

    elif ext in ["html", "htm"]:
        soup = BeautifulSoup(file.read(), "html.parser")
        return [(1, soup.get_text(separator="\n"))]

    return []

# ==============================
# PAGE-BASED CHUNKING ✅
# ==============================

def chunk_pages(pages, pages_per_chunk=3):
    chunks = []
    for i in range(0, len(pages), pages_per_chunk):
        chunk = "\n".join(
            f"[Page {p[0]}]\n{p[1]}" for p in pages[i:i + pages_per_chunk]
        )
        chunks.append(chunk)
    return chunks

# ==============================
# LLM CALL
# ==============================

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

# ==============================
# MERGE + DEDUPLICATE ABBREVIATIONS
# ==============================

def merge_abbreviations(results):
    abbrev = {}
    for r in results:
        for line in r.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                abbrev[k.strip()] = v.strip()
    return dict(sorted(abbrev.items()))

# ==============================
# STREAMLIT UI
# ==============================

st.title("📘 Input to AI - Abbreviation Index Generator (Large PDF Safe)")

uploaded_file = st.file_uploader(
    "Upload a document",
    type=["pdf", "txt", "docx", "html"]
)

question = st.chat_input("Enter your question (optional)")

# ==============================
# MAIN LOGIC
# ==============================

abbrev_index = None
document_text_for_qa = ""

if uploaded_file:
    pages = extract_document_pages(uploaded_file)

    if len(pages) < 3:
        st.error("Unable to extract readable text. The document may be scanned.")
        st.stop()

    chunks = chunk_pages(pages, pages_per_chunk=3)

    results = []
    with st.spinner("Extracting abbreviations (page-based chunking)..."):
        for c in chunks:
            r = call_llm(ABBREVIATION_PROMPT, c)
            if r:
                results.append(r)
            time.sleep(0.3)

    abbrev_index = merge_abbreviations(results)

    st.subheader("📑 Abbreviation Index")
    for k, v in abbrev_index.items():
        st.markdown(f"**{k}** — {v}")

    document_text_for_qa = "\n".join(v for v in abbrev_index.values())

# ==============================
# QUESTION HANDLING
# ==============================

if question:
    st.chat_message("user").markdown(question)

    if uploaded_file:
        answer = call_llm(
            QA_PROMPT,
            f"Document content:\n{document_text_for_qa}\n\nQuestion:\n{question}"
        )
    else:
        answer = call_llm(CHAT_PROMPT, question)

    st.chat_message("assistant").markdown(
        answer if answer else FALLBACK_RESPONSE
    )
