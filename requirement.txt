# ui.py
"""
Streamlit UI for the assistant.
Run with: streamlit run ui.py
It sends prompts to the Flask backend /ask endpoint.
"""

import streamlit as st
import requests
import os
from datetime import datetime
from uuid import uuid4

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")

st.set_page_config(page_title="My Personal AI Assistant", layout="centered")

st.title("My Personal AI Assistant 🤖")
st.caption("Local-first / self-hosted. See privacy policy link below.")

# simple persistent session_id per browser using streamlit session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []  # list of dicts {role, text, ts}

def send_prompt(prompt: str):
    payload = {"session_id": st.session_state.session_id, "prompt": prompt}
    try:
        resp = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=300)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                return data.get("reply","(no reply)")
            else:
                return f"Error: {data.get('error', 'unknown')}"
        else:
            return f"HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"Request error: {e}"

# UI layout
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", "")
    submitted = st.form_submit_button("Send")

if submitted and user_input.strip():
    st.session_state.messages.append({"role": "user", "text": user_input, "ts": datetime.utcnow().isoformat()})
    reply = send_prompt(user_input)
    st.session_state.messages.append({"role": "assistant", "text": reply, "ts": datetime.utcnow().isoformat()})

# display messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['text']}")
    else:
        st.markdown(f"**Assistant:** {msg['text']}")

st.markdown("---")
st.markdown(f"[View privacy policy]({BACKEND_URL}/privacy)")

# small controls
if st.button("Reset conversation"):
    requests.post(f"{BACKEND_URL}/reset_session", json={"session_id": st.session_state.session_id})
    st.session_state.messages = []
    st.success("Conversation reset.")
