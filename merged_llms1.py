import streamlit as st
# Keep existing imports
from pypdf import PdfReader
import time
from openai import OpenAI # The library itself is used for OpenRouter too

# ---------------- CONFIG ----------------

# Configure the client to point to OpenRouter
client = OpenAI(
    api_key=st.secrets["OPENROUTER_API_KEY"], 
    base_url="openrouter.ai"
)

# ... (rest of your existing FALLBACK_RESPONSE and SYSTEM_PROMPT remain the same) ...

# ---------------- FUNCTIONS ----------------

# Rename function to be model-agnostic
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

# ... (extract_pdf_text and chunk_text remain the same) ...

# ---------------- STREAMLIT UI ----------------

st.title("📘 Abbreviation Index Generator")

uploaded_pdf = st.file_uploader("Upload an academic PDF", type=["pdf"])
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
            r = call_llm(chunk) # Use the new function name
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
        response = call_llm(user_input) # Use the new function name
        if response == "NO_ABBREVIATIONS_FOUND":
            response = FALLBACK_RESPONSE

    st.chat_message("assistant").markdown(response)
