"""
BhashaOS Local Web Server
Runs a lightweight server on http://localhost:8000 with a full browser-based voice UI.
"""
import os
import json
import base64
import tempfile
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
from dotenv import load_dotenv
from sarvamai import SarvamAI
from executor import execute

load_dotenv()

api_key = os.environ.get("SARVAM_API_KEY")
if not api_key:
    raise ValueError("SARVAM_API_KEY not set in .env")

client = SarvamAI(api_subscription_key=api_key)

SYSTEM_PROMPT = """
You are the brain of an Indic voice computer agent running on macOS.
The user will give you a transcribed voice command in an Indian language (Hindi, Tamil, Telugu, Kannada, Bengali, Marathi, English, or code-mixed).

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
- Never use rm -rf, shutdown, reboot, or destructive commands.
- For RAM/CPU/disk queries use: vm_stat | head -5, df -h
- For folder queries use open_folder with paths like ~/Desktop, ~/Downloads, ~/Documents
- If the command is to open YouTube, Google, a website — use browser_open or browser_search
"""

def parse_intent(text: str) -> dict:
    response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except Exception:
        return {"action": "answer", "text": raw}

def get_tts_audio(text: str, lang: str = "hi-IN") -> str:
    try:
        response = client.text_to_speech.convert(
            target_language_code=lang,
            text=text[:300],
            speaker="meera",
            model="bulbul:v1",
        )
        return response.audios[0]
    except Exception as e:
        print("TTS error:", e)
        return ""

class BhashaHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open("index.html", "rb") as f:
                self.wfile.write(f.read())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/command-audio":
            content_length = int(self.headers.get("Content-Length", 0))
            audio_data = self.rfile.read(content_length)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                tmp_path = f.name

            try:
                with open(tmp_path, "rb") as f:
                    stt_res = client.speech_to_text.transcribe(
                        file=f,
                        model="saaras:v4",
                        mode="transcribe"
                    )
                transcript = stt_res.transcript.strip()
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"STT failed: {e}"}).encode())
                return
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            self._process_text_and_reply(transcript)

        elif self.path == "/api/command-text":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            transcript = data.get("text", "")
            self._process_text_and_reply(transcript)
        else:
            self.send_response(404)
            self.end_headers()

    def _process_text_and_reply(self, transcript: str):
        action = parse_intent(transcript)
        result = execute(action)
        audio_b64 = get_tts_audio(result)

        resp = {
            "transcript": transcript,
            "action": action,
            "result": result,
            "audio_b64": audio_b64
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode())

if __name__ == "__main__":
    PORT = 8080
    server = HTTPServer(("0.0.0.0", PORT), BhashaHandler)
    print(f"🚀 BhashaOS Web Interface running at: http://localhost:{PORT}")
    server.serve_forever()
