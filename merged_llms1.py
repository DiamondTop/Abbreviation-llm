import streamlit as st
from openai import OpenAI
from pypdf import PdfReader

# ---------------- CONFIG ----------------

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

FALLBACK_RESPONSE = """I'm happy to play along.

since the context is empty, i'll answer the question directly:
I am an AI designed to simulate human-like conversations and provide information on a wide range of topics. I don't have personal experiences, emotions, or physical presence, but I'm here to help answer your questions and engage in discussions to the best of my abilities.
"""

SYSTEM_PROMPT = """
You extract abbreviation indexes from academic articles.

Return ONLY in this format:
• ABBR: full term

If no abbreviations are found, reply exactly:
NO_ABBREVIATIONS_FOUND
"""

# ---------------- FUNCTIONS ----------------

def call_openai(text: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content.strip()


def extract_pdf_text(file):
    reader = PdfReader(file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def chunk_text(text, max_chars=3000):
    chunks = []
    current = ""

    for paragraph in text.split("\n"):
        if len(current) + len(paragraph) < max_chars:
            current += paragraph + "\n"
        else:
            chunks.append(current)
            current = paragraph + "\n"

    if current.strip():
        chunks.append(current)

    return chunks


# ---------------- STREAMLIT UI ----------------

st.title("📘 Abbreviation Index Generator")

uploaded_pdf = st.file_uploader("Upload an academic PDF", type=["pdf"])
user_input = st.chat_input("Ask a question")

if uploaded_pdf:
    text = extract_pdf_text(uploaded_pdf)
    chunks = chunk_text(text)
    results = []
	
    for chunk in chunks:
    	r = call_openai(chunk)
    	if r != "NO_ABBREVIATIONS_FOUND":
        	results.append(r)

result = "\n".join(sorted(set(results))) if results else FALLBACK_RESPONSE

    if result == "NO_ABBREVIATIONS_FOUND":
        result = FALLBACK_RESPONSE

    st.chat_message("assistant").markdown(result)

elif user_input:
    st.chat_message("user").markdown(user_input)

    if len(user_input.split()) < 8:
        response = FALLBACK_RESPONSE
    else:
        response = call_openai(user_input)
        if response == "NO_ABBREVIATIONS_FOUND":
            response = FALLBACK_RESPONSE

    st.chat_message("assistant").markdown(response)
