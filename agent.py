"""
Indic Voice Computer Agent
--------------------------
Speak in any Indian language → computer understands → takes action.

Layer 1 : mic → Saarika STT → Sarvam-105B intent parser → executor
Layer 2 : result → Bulbul TTS → spoken response  (enabled by default)

Usage:
    python agent.py
"""

import os
import io
import json
import base64
import tempfile
import re

import wave
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from sarvamai import SarvamAI

from executor import execute

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
SAMPLE_RATE   = 16000   # Hz — Saarika works best at 16kHz
RECORD_SECS   = 5       # seconds to record per command
SPEAK_BACK    = True    # Layer 2: spoken response via Bulbul
REPLY_LANG    = "hi-IN" # language for spoken reply (change to "ta-IN", "en-IN", etc.)

# ── Sarvam client ────────────────────────────────────────────────────────────
api_key = os.environ.get("SARVAM_API_KEY")
if not api_key:
    raise ValueError("SARVAM_API_KEY not set. Add it to your .env file.")
client = SarvamAI(api_subscription_key=api_key)

# ── System prompt for intent parsing ─────────────────────────────────────────
SYSTEM_PROMPT = """
You are the brain of an Indic voice computer agent running on macOS.
The user will give you a transcribed voice command in any Indian language (Hindi, Tamil, Telugu, Kannada, Bengali, Marathi, English, or code-mixed).

Your job: understand the intent and return ONLY a single JSON object (no markdown, no explanation).

Supported action types:
- {"action": "shell", "command": "<safe shell command>"}
- {"action": "browser_open", "url": "<full URL>"}
- {"action": "browser_search", "query": "<search query in English>"}
- {"action": "browser_download", "url": "<direct download URL>", "save_as": "<filename>"}
- {"action": "open_app", "app": "<app name>"}
- {"action": "open_folder", "path": "<path, use ~ for home>"}
- {"action": "answer", "text": "<short factual answer if no OS action needed>"}

Rules:
- Never use rm -rf, shutdown, reboot, or any destructive commands.
- For RAM/CPU/disk queries use: vm_stat, top -l 1, df -h
- For folder queries use open_folder with paths like ~/Desktop, ~/Downloads, ~/Documents
- If the command is to open YouTube, Google, a website — use browser_open or browser_search
- Always return valid JSON. No extra text.

Examples:
User: "मेरी Downloads folder खोलो"
→ {"action": "open_folder", "path": "~/Downloads"}

User: "YouTube पर AR Rahman songs खोलो"
→ {"action": "browser_search", "query": "AR Rahman songs"}

User: "RAM कितनी बची है"
→ {"action": "shell", "command": "vm_stat | head -5"}

User: "Google Chrome खोलो"
→ {"action": "open_app", "app": "Google Chrome"}

User: "Python tutorial search karo"
→ {"action": "browser_search", "query": "Python tutorial"}
"""

# ── Audio recording ──────────────────────────────────────────────────────────
def record_audio(seconds: int = RECORD_SECS) -> bytes:
    print(f"\n🎙️  Recording for {seconds}s... speak now!")
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                   channels=1, dtype="int16")
    sd.wait()
    print("✅  Done recording.")

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # int16 = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()


# ── Speech-to-text ───────────────────────────────────────────────────────────
def transcribe(audio_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        with open(tmp_path, "rb") as f:
            response = client.speech_to_text.transcribe(
                file=f,
                model="saaras:v4",
                mode="transcribe",
            )
        return response.transcript.strip()
    finally:
        os.unlink(tmp_path)


# ── Intent parsing ───────────────────────────────────────────────────────────
def parse_intent(text: str) -> dict:
    response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": text},
        ],
    )
    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"action": "answer", "text": raw}


# ── Layer 2: Speak the result ─────────────────────────────────────────────────
def speak(text: str):
    if not text or not SPEAK_BACK:
        return
    try:
        response = client.text_to_speech.convert(
            target_language_code=REPLY_LANG,
            text=text[:500],  # Bulbul limit per call
            speaker="meera",
            model="bulbul:v1",
        )
        audio_b64 = response.audios[0]
        audio_bytes = base64.b64decode(audio_b64)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        sd.play(audio_array, samplerate=22050)
        sd.wait()
    except Exception as e:
        print(f"  [TTS error: {e}]")


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  🤖  Indic Voice Computer Agent  (Sarvam AI)")
    print("=" * 55)
    print("  Speak in Hindi, Tamil, English, or any Indian language.")
    print("  Press  Ctrl+C  to quit.\n")

    while True:
        try:
            input("  ⏎  Press Enter to start speaking...")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break

        try:
            # Step 1: Record
            audio_bytes = record_audio()

            # Step 2: STT
            print("  🔤  Transcribing...")
            transcript = transcribe(audio_bytes)
            if not transcript:
                print("  ⚠️  Could not hear anything. Try again.\n")
                continue
            print(f"  📝  You said: \"{transcript}\"")

            # Step 3: Parse intent
            print("  🧠  Understanding intent...")
            action = parse_intent(transcript)
            print(f"  ⚡  Action: {json.dumps(action, ensure_ascii=False)}")

            # Step 4: Execute
            result = execute(action)
            print(f"  ✅  Result: {result}\n")

            # Step 5: Speak result (Layer 2)
            speak(result)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"  ❌  Error: {e}\n")


if __name__ == "__main__":
    main()
