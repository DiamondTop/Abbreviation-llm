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

gemini_model = genai.GenerativeModel("gemini-2.0-flash")

openrouter_client = OpenAI(
    api_key=st.secrets["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1"
)

# ---------------- QUESTION INPUT ----------------

question = st.text_input("Ask a question")

# ---------------- MODEL FUNCTIONS ----------------

def ask_chatgpt(q):
    try:
        r = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": q}],
            temperature=0
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"⚠ ChatGPT error: {e}"


def ask_claude(q):
    try:
        r = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=800,
            messages=[{"role": "user", "content": q}]
        )
        return r.content[0].text
    except Exception as e:
        return f"⚠ Claude error: {e}"


def ask_gemini(q):
    try:
        r = gemini_model.generate_content(q)
        return r.text
    except Exception as e:
        if "quota" in str(e).lower() or "429" in str(e):
            return "⚠ Gemini quota exceeded."
        return f"⚠ Gemini error: {e}"


def ask_open_source(q):
    try:
        r = openrouter_client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {"role": "user", "content": q}
            ],
            temperature=0
        )

        return r.choices[0].message.content

    except Exception as e:
        return f"⚠ OpenRouter error: {e}"


# ---------------- RUN MODELS ----------------

if question:

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        st.subheader("ChatGPT (OpenAI)")
        st.write(ask_chatgpt(question))

    with col2:
        st.subheader("Claude (Anthropic)")
        st.write(ask_claude(question))

    with col3:
        st.subheader("Gemini (Google)")
        st.write(ask_gemini(question))

    with col4:
        st.subheader("Open-source (OpenRouter)")
        st.write(ask_open_source(question))
