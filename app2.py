import streamlit as st
import requests
from openai import OpenAI
import google.generativeai as genai

# ==============================
# PAGE CONFIG & STYLES (Reusing your elegant gold/dark theme)
# ==============================
st.set_page_config(page_title="Reasoning Forge", page_icon="🧠", layout="wide")

# (Keep your existing CSS block here - it's excellent for the brand)

# ==============================
# SIDEBAR - LLM SELECTION
# ==============================
with st.sidebar:
    st.markdown("### ✦ Model Selection")
    
    # Dropdown for 3 different LLM providers
    PROVIDER = st.selectbox(
        "Choose Reasoning Engine",
        [
            "DeepSeek R1 (Reasoning Expert)",
            "OpenAI o1-mini (Logic Focused)",
            "Gemini 2.0 Flash (Speed & Context)"
        ]
    )
    
    st.info("Reasoning models take longer to respond as they 'think' through the problem step-by-step.")

# ==============================
# LLM CLIENT SETUP
# ==============================
def get_llm_response(prompt, provider):
    """Handles logic for the 3 different selected LLMs"""
    
    try:
        # 1. DeepSeek R1 via OpenRouter
        if "DeepSeek" in provider:
            client = OpenAI(
                api_key=st.secrets["OPENROUTER_API_KEY"],
                base_url="https://openrouter.ai/api/v1"
            )
            response = client.chat.completions.create(
                model="deepseek/deepseek-r1",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

        # 2. OpenAI o1-mini
        elif "OpenAI" in provider:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="o1-mini", # o1 models use 'developer' or 'user' roles specifically
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

        # 3. Gemini 2.0 Flash
        elif "Gemini" in provider:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text

    except Exception as e:
        return f"Error: {str(e)}"

# ==============================
# MAIN INTERFACE
# ==============================
st.markdown("""
<h1 style="font-family:'Cormorant Garamond'; font-size:3.5rem; font-weight:300;">
    Reasoning <em style="color:#c9a84c; font-style:italic;">Forge</em>
</h1>
""", unsafe_allow_html=True)

user_input = st.text_area(
    "Enter a complex problem, math equation, or logic puzzle:",
    height=250,
    placeholder="Ex: How many R's are in the word Strawberry? Explain your step-by-step logic."
)

if st.button("✦ Start Reasoning"):
    if user_input:
        with st.spinner(f"The {PROVIDER} is thinking..."):
            answer = get_llm_response(user_input, PROVIDER)
            
            # Formatting the output
            st.markdown("<hr/>", unsafe_allow_html=True)
            st.markdown("### ✦ Final Response")
            
            # Reasoning models often return <think> tags. 
            # This logic separates the 'thought' from the 'answer'.
            if "<think>" in answer:
                parts = answer.split("</think>")
                thought_process = parts[0].replace("<think>", "").strip()
                final_answer = parts[1].strip()
                
                with st.expander("View Internal Thought Process", expanded=True):
                    st.write(thought_process)
                st.markdown(f"<div class='cover-letter-box'>{final_answer}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='cover-letter-box'>{answer}</div>", unsafe_allow_html=True)
    else:
        st.warning("Please enter a prompt first.")
