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
    return response.choices[0].message.content.strip
