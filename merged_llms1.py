import streamlit as st
import time
from openai import OpenAI
from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup

# ---------------- CONFIG ----------------

client = OpenAI(
    api_key=st.secrets["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1"
)

MODEL_NAME = "mistralai/mistral-7b-instruct"

FALLBACK_RESPONSE ="""I'm happy to play along.

since the context is empty, i'll answer the question directly:
I am an AI designed to simulate human-like conversations and provide information on a wide range of topics. I don't have personal experiences, emotions, or physical presence, but I'm here to help answer your questions and engage in discussions to the best of my abilities.
"""


ABBREVIATION_PROMPT = """
You extract abbreviation indexes from academic articles.

Return ONLY in this format:
• ABBR: full term

If no abbreviations are found, reply exactly:
NO_ABBREVIATIONS_FOUND
"""

QA_PROMPT = """
You are an AI assistant answering questions using ONLY the provided document context.
If the answer is not contained in the context, say:
"I don’t have enough information in the document to answer that."
"""

# ---------------- DOCUMENT EXTRACTION ----------------

def extract_text(file):
    ext = file.name.split(".")[-1].lower()

    if ext == "pdf":
        reader = PdfReader(file)
        return "\n".join(
            page.extract_text() or "" for page in reader.pages
        )

    elif ext == "txt":
        return file.read().decode("utf-8", errors="ignore")

    elif ext == "docx":
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    elif ext in ["html", "htm"]:
        soup = BeautifulSoup(file.read(), "html.parser")
        return soup.get_text(separator="\n")

    else:
        raise ValueError("Unsupported file format")

# ---------------- CHUNKING ----------------

def chunk_text(text, max_chars=1500):
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
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.warning(f"LLM call skipped: {e}")
        return "NO_ABBREVIATIONS_FOUND"

# ---------------- STREAMLIT UI ----------------

st.title("📘Input to AI - Abbreviation Index Generator")

mode = st.radio("Choose mode:", ["Enter your Question", "Extract abbreviations"])
uploaded_file = st.file_uploader(
    "Upload a document",
    type=["pdf", "txt", "docx", "html"]
)
user_question = st.chat_input("Ask something about the document")

if uploaded_file:
    text = extract_text(uploaded_file)
    chunks = chunk_text(text)

    if mode == "Extract abbreviations":
        prompt = ABBREVIATION_PROMPT
        outputs = []

        for chunk in chunks:
            r = call_llm(prompt, chunk)
            if r != "NO_ABBREVIATIONS_FOUND":
                outputs.append(r)
            time.sleep(0.3)

        final = "\n".join(sorted(set(outputs))) if outputs else FALLBACK_RESPONSE
        st.markdown(final)

    elif user_question:
        prompt = QA_PROMPT
        answers = []

        for chunk in chunks:
            ans = call_llm(prompt, f"Context:\n{chunk}\n\nQuestion:\n{user_question}")
            if "don’t have enough information" not in ans.lower():
                answers.append(ans)
            time.sleep(0.3)

        st.markdown(answers[0] if answers else FALLBACK_RESPONSE)
