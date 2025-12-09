import os
import requests
import streamlit as st
from langchain_ollama import ChatOllama

# ---------- CONFIG ----------

# Closed-source Gemini API key
API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize local LLM (open-source via Ollama)
ollama_llm = ChatOllama(
    model="llama3.2:latest",
    temperature=0
)

# ---------- LLM CALL FUNCTIONS ----------

def call_gemini(prompt: str) -> str:
    """
    Call the Gemini API with a simple text prompt.
    Adjust URL/payload to match your actual Gemini endpoint.
    """

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "input": prompt,
        "output_format": "text",
    }

    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            headers=headers,
            json=data,
            timeout=60,
        )
    except Exception as e:
        return f"Error calling Gemini API: {e}"

    if response.status_code == 200:
        try:
            return response.json().get("response", "")
        except Exception as e:
            return f"Error parsing Gemini response: {e}"
    else:
        return f"Error from Gemini API ({response.status_code}): {response.text}"


def call_ollama(prompt: str) -> str:
    """
    Use the local Ollama LLM via LangChain.
    """
    try:
        response = ollama_llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error calling local Ollama model: {e}"


# ---------- STREAMLIT UI ----------

st.title("LLM Chat – Toggle Between Local (Ollama) and Gemini")

# Sidebar for model selection
model_choice = st.sidebar.selectbox(
    "Choose LLM backend",
    ["Local LLaMA (Ollama)", "Gemini (Closed-source API)"],
    index=0
)

st.sidebar.markdown(
    f"**Current model:** {model_choice}"
)

# Handle switching models (optional: reset chat on change)
if "current_model" not in st.session_state:
    st.session_state.current_model = model_choice

if model_choice != st.session_state.current_model:
    # Clear messages when switching models to avoid mixing contexts
    st.session_state.messages = []
    st.session_state.current_model = model_choice

# Initialize chat state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Type your message:")
if user_input:
    # Add user message to session
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Decide which model to call
    if model_choice == "Local LLaMA (Ollama)":
        ai_response = call_ollama(user_input)
    else:  # "Gemini (Closed-source API)"
        ai_response = call_gemini(user_input)

    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": ai_response})

    # Display assistant response immediately
    with st.chat_message("assistant"):
        st.markdown(ai_response)
