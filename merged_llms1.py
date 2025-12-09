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

CHAT_PROMPT = """
You are a helpful AI assistant.
Answer the user naturally and clearly.
"""

SUMMARY_PROMPT = """
You are summarizing an academic article.

Rules:
- Use ONLY information explicitly present in the text
- Do NOT add generic academic commentary
- Preserve technical terms and abbreviations
- If content is unclear, say so

Return a concise factual summary.
"""

QA_PROMPT = """
Answer the question using ONLY the document content below.

If the answer is not clearly present, reply exactly:
"I don’t have enough information in the document to answer that."
"""

FALLBACK_RESPONSE = """I'm happy to play along.

since the context is empty, i'll answer the question directly:
I am an AI designed to simulate human-like conversations and provide information on a wide range of topics. I don't have personal experiences, emotions, or physical presence, but I'm here to help answer your questions and engage in discussions to the best of my abilities.
"""

# ==============================
# DOCUMENT EXTRACTION
# ==============================

def extract_text(file):
    ext = file.name.split(".")[-1].lower()

    if ext == "pdf":
        reader = PdfReader(file)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text and len(text.strip()) > 100:
                pages.append(text)
        return "\n".join(pages)

    elif ext == "txt":
        return file.read().decode("utf-8", errors="ignore")

    elif ext == "docx":
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    elif ext in ["html", "htm"]:
        soup = BeautifulSoup(file.read(), "html.parser")
        return soup.get_text(separator="\n")

    else:
        return ""

# ==============================
# CHUNKING
# ==============================

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
# STREAMLIT UI
# ==============================

st.title("📄 Input to AI – Document Q&A (Open-source ↔ Gemini)")

uploaded_file = st.file_uploader(
    "Upload a document (optional)",
    type=["pdf", "txt", "docx", "html"]
)

question = st.chat_input("Ask a question")

# ==============================
# LOGIC FLOW
# ==============================

doc_summary = None

# ---- If document uploaded ----
if uploaded_file:
    text = extract_text(uploaded_file)

    if not text or len(text.strip()) < 500:
        st.error("Unable to extract readable text from this document.")
    else:
        chunks = chunk_text(text)

        summaries = []
        with st.spinner("Understanding document..."):
            for c in chunks:
                s = call_llm(SUMMARY_PROMPT, c)
                if s:
                    summaries.append(s)
                time.sleep(0.2)

        doc_summary = "\n".join(summaries)

# ---- Handle user question (WITH or WITHOUT document) ----
if question:
    st.chat_message("user").markdown(question)

    if doc_summary:
        answer = call_llm(
            QA_PROMPT,
            f"Document content:\n{doc_summary}\n\nQuestion:\n{question}"
        )
        st.chat_message("assistant").markdown(
            answer if answer else FALLBACK_RESPONSE
        )

    else:
        # ✅ CHAT MODE (no document uploaded)
        answer = call_llm(CHAT_PROMPT, question)
        st.chat_message("assistant").markdown(
            answer if answer else FALLBACK_RESPONSE
        )

