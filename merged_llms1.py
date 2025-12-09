import os
import requests
import streamlit as st

from openai import OpenAI
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



# ---------- CONFIG ----------
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


# ---------- LLM CALL FUNCTIONS ----------
from pypdf import PdfReader

def extract_pdf_text(file):
    reader = PdfReader(file)
    return "\n".join(page.extract_text() for page in reader.pages)




# ---------- STREAMLIT UI ----------

st.title("LLM Chat – Toggle Between Local (Ollama) and Gemini")


from pypdf import PdfReader

def extract_pdf_text(file):
    reader = PdfReader(file)
    return "\n".join(page.extract_text() for page in reader.pages)


uploaded_pdf = st.file_uploader("Upload an academic PDF", type=["pdf"])
user_input = st.chat_input("Ask a question")

if uploaded_pdf:
    text = extract_pdf_text(uploaded_pdf)
    result = call_openai(text)

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
