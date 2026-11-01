# BhashaOS 🇮🇳 — Indic Voice Computer Agent

> Control your computer with your voice in Indian languages. A voice-first ambient computer agent built on Sarvam AI's speech, language, and voice models.

[![Sarvam AI](https://img.shields.io/badge/Powered%20By-Sarvam%20AI-orange.svg)](https://www.sarvam.ai/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌟 The Problem

Over 500 million people across India think and speak in Indian languages (Hindi, Tamil, Telugu, Kannada, Bengali, etc.) and code-mixed formats like Hinglish. Yet, computer interfaces, operating systems, and terminal shells remain exclusively English-first. 

**BhashaOS** closes this gap by transforming spoken Indic voice instructions directly into native computer actions: opening applications, browsing websites, managing files, executing safe shell utilities, and answering questions — speaking the results back in the user's native tongue.

---

## 🏗️ Architecture

```
🎙️ Microphone (16kHz)
        │
        ▼
🔤 Sarvam Saarika (STT) ────────► Accurately transcribes accents & code-mixed Indic speech
        │
        ▼
🧠 Sarvam-105B (Chat LLM) ──────► Parses user intent into a clean action schema
        │
        ▼
⚡ Action Router (executor.py) ──► Shell commands, Finder / Explorer, Default Browser
        │
        ▼
🔊 Sarvam Bulbul (TTS) ─────────► Speaks confirmation and results back in Hindi/Tamil
```

---

## 🚀 Key Features

- **Indic Code-Mixed STT:** Understands seamless mixtures like *"Mera Downloads folder open karo"* or *"Python tutorial search karo"*.
- **Autonomous Browser Navigation:** Opens URLs, performs Google searches, and downloads remote files.
- **Native OS & App Control:** Directly interacts with macOS/Linux/Windows apps (e.g., Calculator, Chrome, Notes) and directory hierarchies.
- **System Information & Shell:** Runs safe diagnostic queries (`vm_stat`, `df -h`) while actively blocking destructive commands (`rm -rf`, format, etc.).
- **Spoken Confirmations (Layer 2):** Uses Sarvam Bulbul to read responses back out loud to the user.
- **Zero Overhead:** No heavy headless browser downloads — uses native system bindings for instant execution.

---

## 🛠️ Quickstart

### 1. Clone the repository
```bash
git clone https://github.com/your-username/bhasha-os.git
cd bhasha-os
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure your API Key
Create a `.env` file in the root directory:
```env
SARVAM_API_KEY=your_sarvam_api_key_here
```

### 4. Run the Agent
```bash
python3 agent.py
```
Press **Enter**, speak your command in any Indian language, and watch your computer execute it!

---

## 🌐 Showcase Landing Page

A complete interactive showcase landing page is included in `index.html`. Open it directly in any browser:
```bash
open index.html
```

---

## 🏆 Built For
Sarvam AI Hackathon 2026. Empowering the next billion users through voice and native Indian AI.
