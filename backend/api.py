"""
FastAPI Backend for ASL Sign Language App
WebSocket endpoints:
  - ws://.../ws/detect  : stream camera frames → get letter predictions
  - ws://.../ws/chat    : real-time Gemini chatbot
HTTP endpoints:
  - POST /text-to-sign  : text → sign images (base64)
  - GET  /health        : health check
  - GET  /              : info
"""

import sys
import os
import base64
import pickle
import json
import socket
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── path setup ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent   # repo root
sys.path.insert(0, str(BASE_DIR))

from gemini_chatbot import GeminiChatbot            # noqa: E402

# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(title="ASL Sign Language API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup banner ────────────────────────────────────────────────────────────
@app.on_event("startup")
async def print_network_info():
    try:
        # Get the local Wi-Fi / LAN IP (connects a UDP socket, never sends data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "unknown"

    sep = "=" * 54
    print(f"\n{sep}")
    print("  ASL Sign Language Backend  –  RUNNING")
    print(sep)
    print(f"  Local (this PC) : http://localhost:8000")
    print(f"  Network (phone) : http://{local_ip}:8000")
    print(f"  Health check    : http://{local_ip}:8000/health")
    print(f"  API docs        : http://{local_ip}:8000/docs")
    print(sep)
    print("  Flutter app URL to set in Settings:")
    print(f"    http://{local_ip}:8000")
    print(f"{sep}\n")

# ── Load ML model ────────────────────────────────────────────────────────────
MODEL_PATH = BASE_DIR / "model" / "model.p"
model_dict = pickle.load(open(MODEL_PATH, "rb"))
ml_model = model_dict["model"]

# ── MediaPipe ────────────────────────────────────────────────────────────────
try:
    mp_hands = mp.solutions.hands
except AttributeError:
    raise RuntimeError(
        "mediapipe.solutions not found. "
        "Install a compatible version: pip install 'mediapipe>=0.10.5,<0.10.20'"
    )

# ── Chatbot (lazy-loaded so missing API key doesn't crash startup) ────────────
_chatbot: GeminiChatbot | None = None

def get_chatbot() -> GeminiChatbot:
    global _chatbot
    if _chatbot is None:
        _chatbot = GeminiChatbot()
    return _chatbot

# ── Sign images directory ─────────────────────────────────────────────────────
IMAGES_DIR = BASE_DIR / "assets" / "images"

# ── Request / Response schemas ────────────────────────────────────────────────
class TextToSignRequest(BaseModel):
    text: str

class CorrectRequest(BaseModel):
    text: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def _image_to_b64(path: Path) -> str:
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def _build_signs(text: str) -> list:
    """Return ordered list of sign dicts for text."""
    words = text.lower().strip().split()
    result = []
    for word in words:
        word_path = IMAGES_DIR / f"{word}.jpg"
        if word_path.exists():
            result.append({"type": "word", "label": word, "image": _image_to_b64(word_path)})
        else:
            for ch in word:
                if ch.isalpha():
                    letter_path = IMAGES_DIR / f"{ch}.jpg"
                    if letter_path.exists():
                        result.append({"type": "letter", "label": ch.upper(), "image": _image_to_b64(letter_path)})
        result.append({"type": "space", "label": " ", "image": None})
    return result


def _predict_from_bytes(img_bytes: bytes) -> dict:
    """Run MediaPipe + ML model on raw image bytes. Returns dict."""
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"letter": None, "hand_detected": False}

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Use a fresh Hands instance per call (static_image_mode=True is thread-safe)
    with mp_hands.Hands(static_image_mode=True, max_num_hands=1,
                        min_detection_confidence=0.5) as hands:
        results = hands.process(frame_rgb)

    if not results.multi_hand_landmarks:
        return {"letter": None, "hand_detected": False}

    hand_lm = results.multi_hand_landmarks[0]
    data_aux, x_, y_ = [], [], []
    for lm in hand_lm.landmark:
        x_.append(lm.x)
        y_.append(lm.y)
    for lm in hand_lm.landmark:
        data_aux.append(lm.x - min(x_))
        data_aux.append(lm.y - min(y_))

    try:
        prediction = ml_model.predict([np.asarray(data_aux)])
        return {"letter": str(prediction[0]), "hand_detected": True}
    except Exception:
        return {"letter": None, "hand_detected": False}


# ── HTTP Endpoints ─────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"app": "ASL Sign Language API", "status": "running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/correct")
def correct_sentence(req: CorrectRequest):
    """Grammar-correct a sentence using Gemini. Returns {\"corrected\": \"...\"}."""
    if not req.text.strip():
        return {"corrected": req.text}
    try:
        bot = get_chatbot()
        prompt = (
            f"Fix the grammar and spelling of this sentence. "
            f"Return ONLY the corrected sentence, nothing else: {req.text}"
        )
        corrected = bot.send_message(prompt)
        return {"corrected": corrected.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/text-to-sign")
def text_to_sign(req: TextToSignRequest):
    """Convert text to a list of sign images (base64 encoded JPEG)."""
    if not req.text.strip():
        return {"signs": []}
    return {"signs": _build_signs(req.text)}


# ── WebSocket: ASL Detection ───────────────────────────────────────────────────
@app.websocket("/ws/detect")
async def ws_detect(websocket: WebSocket):
    """
    Real-time ASL letter detection over WebSocket.

    Client sends:  base64-encoded JPEG string (plain text)
    Server replies: JSON  {"letter": "A" | null, "hand_detected": true|false}
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                img_bytes = base64.b64decode(data)
                result = _predict_from_bytes(img_bytes)
            except Exception as e:
                result = {"letter": None, "hand_detected": False, "error": str(e)}
            await websocket.send_text(json.dumps(result))
    except WebSocketDisconnect:
        pass


# ── WebSocket: Chatbot ─────────────────────────────────────────────────────────
@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    """
    Gemini chatbot over WebSocket.

    Client sends:  plain text message  OR  "CLEAR" to reset history
    Server replies: JSON  {"response": "...", "error": null}
                      OR  {"response": null, "error": "..."}
    """
    await websocket.accept()
    try:
        bot = get_chatbot()
    except Exception as e:
        await websocket.send_text(json.dumps({"response": None, "error": str(e)}))
        await websocket.close()
        return

    try:
        while True:
            message = await websocket.receive_text()
            if message.strip().upper() == "CLEAR":
                bot.clear_history()
                await websocket.send_text(json.dumps({"response": "Chat cleared.", "error": None}))
                continue
            try:
                reply = bot.send_message(message)
                await websocket.send_text(json.dumps({"response": reply, "error": None}))
            except Exception as e:
                await websocket.send_text(json.dumps({"response": None, "error": str(e)}))
    except WebSocketDisconnect:
        pass


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
