# app.py
"""
Flask backend exposing:
 - POST /ask  -> JSON { "session_id": "...", "prompt": "..." } returns { "reply": "...", "ok": True }
 - GET  /privacy -> serves privacy_policy.md content (HTML)
This is minimal and stores session histories in memory (per-process). For production, persist sessions.
"""

import os
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
import threading
import json

load_dotenv()

from assistant import chat_with_ai

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # You may restrict origins in production

# In-memory session store: { session_id -> [ (user, assistant), ... ] }
# Warning: ephemeral. If the server restarts, histories are lost. Persist for production.
sessions = {}
lock = threading.Lock()

DATA_DIR = Path(os.getenv("DATA_DIR", "local_data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRIVACY_PATH = Path("privacy_policy.md")

@app.route("/ask", methods=["POST"])
def ask():
    body = request.get_json(force=True, silent=True)
    if not body or "prompt" not in body:
        return jsonify({"ok": False, "error": "Missing 'prompt' in JSON body."}), 400

    prompt = body["prompt"]
    session_id = body.get("session_id", "default")

    # retrieve history
    with lock:
        history = sessions.get(session_id, []).copy()

    # call model
    reply = chat_with_ai(prompt, history)

    # update history
    with lock:
        sessions.setdefault(session_id, []).append((prompt, reply))
        # optional: cap history length
        max_turns = int(os.getenv("MAX_HISTORY_TURNS", "20"))
        if len(sessions[session_id]) > max_turns:
            sessions[session_id] = sessions[session_id][-max_turns:]

    return jsonify({"ok": True, "reply": reply})

@app.route("/privacy", methods=["GET"])
def privacy():
    if PRIVACY_PATH.exists():
        # serve as HTML string conversion or raw markdown
        md = PRIVACY_PATH.read_text(encoding="utf-8")
        # simple HTML conversion: replace newlines -> <br> (you can use markdown lib for nicer view)
        html = "<html><body><pre style='white-space:pre-wrap; font-family:monospace;'>" + md + "</pre></body></html>"
        return Response(html, mimetype="text/html")
    else:
        return "Privacy policy not found.", 404

@app.route("/reset_session", methods=["POST"])
def reset_session():
    body = request.get_json(force=True, silent=True) or {}
    session_id = body.get("session_id", "default")
    with lock:
        sessions.pop(session_id, None)
    return jsonify({"ok": True, "session_id": session_id})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
