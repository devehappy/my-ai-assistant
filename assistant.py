# assistant.py
"""
Core AI logic.
- Uses OpenAI if OPENAI_API_KEY is present.
- Falls back to llama-cpp-python local model if OPENAI_API_KEY is not provided and a local model path exists.
- Exposes chat_with_ai(prompt, history) which returns text.
"""

import os
import json
from typing import List, Tuple

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
LOCAL_LLAMA_PATH = os.getenv("LOCAL_LLAMA_MODEL_PATH", "models/ggml-model.bin")  # change if needed

# Try to import OpenAI if key exists
openai_available = False
if OPENAI_API_KEY:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        openai_available = True
    except Exception as e:
        print("OpenAI import failed:", e)
        openai_available = False

# Try to import llama-cpp-python
llama_available = False
try:
    from llama_cpp import Llama
    if os.path.exists(LOCAL_LLAMA_PATH):
        llm = Llama(model_path=LOCAL_LLAMA_PATH)
        llama_available = True
    else:
        llama_available = False
except Exception:
    llama_available = False

def chat_with_openai(prompt: str, history: List[Tuple[str, str]] = None) -> str:
    """
    Send a chat to OpenAI ChatCompletion (gpt-3.5-turbo / gpt-4 if available).
    history: list of (user, assistant) pairs to maintain context.
    """
    if not openai_available:
        raise RuntimeError("OpenAI not configured or unavailable.")

    messages = []
    # system prompt (you can modify)
    messages.append({"role": "system", "content": "You are a helpfu
