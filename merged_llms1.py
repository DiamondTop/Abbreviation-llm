import streamlit as st
from openai import OpenAI
import anthropic
import google.generativeai as genai

st.title("🤖 Multi-LLM Comparison Tool")

# ---------------- API CLIENTS ----------------

openai_client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)

anthropic_client = anthropic.Anthropic(
    api_key=st.secrets["ANTHROPIC_API_KEY"]
)

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

openrouter_client = OpenAI(
    api_key=st.secrets["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1"
)

# ---------------- QUESTION INPUT ----------------

question = st.text_input("Ask a question")

# ---------------- LLM CALL FUNCTIONS ----------------

def ask_chatgpt(q):

    r = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":q}],
        temperature=0
    )

    return r.choices[0].message.content


def ask_claude(q):

    r = anthropic_client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=800,
        messages=[{"role":"user","content":q}]
    )

    return r.content[0].text


def ask_gemini(q):

    r = gemini_model.generate_content(q)

    return r.text


def ask_mistral(q):

    r = openrouter_client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct:free",
        messages=[{"role":"user","content":q}],
        temperature=0
    )

    return r.choices[0].message.content


# ---------------- RUN MODELS ----------------

if question:

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        st.subheader("ChatGPT")
        st.write(ask_chatgpt(question))

    with col2:
        st.subheader("Claude")
        st.write(ask_claude(question))

    with col3:
        st.subheader("Gemini")
        st.write(ask_gemini(question))

    with col4:
        st.subheader("Open-source (Llama)")
        st.write(ask_mistral(question))
