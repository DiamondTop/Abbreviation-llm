import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
import time

# ---------------- CONFIG ----------------

client = OpenAI(
    api_key=st.secrets["OPENROUTER_API_KEY"], 
    base_url="openrouter.ai" 
)

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

def extract_pdf_text(file):
    reader = PdfReader(file)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text and len(text.strip()) > 50:  # skip junk pages
            pages.append(text)
    return "\n".join(pages)


def call_llm(text: str) -> str:
    try:
        # We will use a free/cheap model offered via OpenRouter, e.g., 'mistralai/mistral-7b-instruct'
        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct", # A commonly free/cheap model on OpenRouter
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        st.error(f"An OpenRouter/LLM error occurred: {e}") 
        st.warning("Skipped a chunk due to LLM error.")
        return "NO_ABBREVIATIONS_FOUND"

def chunk_text(text, max_chars=1500):
    chunks = []
    current = ""

    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if len(current) + len(paragraph) <= max_chars:
            current += paragraph + "\n"
        else:
            chunks.append(current)
            current = paragraph + "\n"

    if current.strip():
        chunks.append(current)

    return chunks


# ---------------- STREAMLIT UI ----------------

st.title("📘Input to AI - Abbreviation Index Generator")

uploaded_pdf = st.file_uploader("Enter your Question", type=["pdf"])
user_input = st.chat_input("Ask a question")

# -------- PDF MODE --------
if uploaded_pdf:
    with st.spinner("Processing PDF..."):
        try:
            text = extract_pdf_text(uploaded_pdf) # <--- The line 50 equivalent
        except Exception as e:
            st.error(f"Failed to process PDF. Specific error: {e}")
            st.exception(e) # This will show the full traceback in the UI
            st.stop() # Stop execution here
            
        chunks = chunk_text(text)

        results = []

        for chunk in chunks:
            r = call_llm(chunk)
            if r != "NO_ABBREVIATIONS_FOUND":
                results.append(r)
            time.sleep(0.3)  # rate-limit safety

        if results:
            result = "\n".join(sorted(set(results)))
        else:
            result = FALLBACK_RESPONSE

    st.chat_message("assistant").markdown(result)

# -------- CHAT MODE --------
elif user_input:
    st.chat_message("user").markdown(user_input)

    if len(user_input.split()) < 8:
        response = FALLBACK_RESPONSE
    else:
        response = call_llm(user_input)
        if response == "NO_ABBREVIATIONS_FOUND":
            response = FALLBACK_RESPONSE

    st.chat_message("assistant").markdown(response)
