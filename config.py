import os
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
except (ImportError, FileNotFoundError, AttributeError):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. Add to .env file (local) or Streamlit secrets (cloud)"
    )

if not TAVILY_API_KEY:
    raise ValueError(
        "TAVILY_API_KEY not found. Add to .env file (local) or Streamlit secrets (cloud)"
    )
