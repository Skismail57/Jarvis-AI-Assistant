---

<p align="center">
  <img src="Screenshots/cover%20image.png" alt="JARVIS Cover" width="800" style="border-radius: 16px; box-shadow: 0 0 60px rgba(123, 47, 247, 0.5);" />
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=ffdd54" /></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" /></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black" /></a>
  <a href="https://vitejs.dev/"><img src="https://img.shields.io/badge/Vite-5.4-646CFF?style=for-the-badge&logo=vite&logoColor=white" /></a>
  <a href="https://tailwindcss.com/"><img src="https://img.shields.io/badge/TailwindCSS-3.4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" /></a>
  <a href="https://www.trychroma.com/"><img src="https://img.shields.io/badge/ChromaDB-Vector_Store-FF6B6B?style=for-the-badge" /></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" /></a>
  <img src="https://img.shields.io/badge/Version-2.0.0-7b2ff7?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-Educational%20Use-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge" />
</p>

<p align="center">
  <strong>JARVIS V2.0</strong> — A full-stack professional AI personal assistant with voice interaction, PC control, semantic memory, biometric auth, smart-home integration, and a luxury dark-themed web UI.
</p>

---

## 📑 Table of Contents

1. [✨ Project Overview](#-project-overview)
2. [🚀 Key Features](#-key-features)
3. [🛠️ Technology Stack](#️-technology-stack)
4. [📁 Project Structure](#-project-structure)
5. [⚙️ Prerequisites](#️-prerequisites)
6. [📦 Installation](#-installation)
7. [🔧 Configuration](#-configuration)
8. [▶️ Running the Project](#️-running-the-project)
9. [💡 How to Use](#-how-to-use)
10. [🧠 Architecture Deep-Dive](#-architecture-deep-dive)
11. [🔌 API Reference](#-api-reference)
12. [🧩 Plugin System](#-plugin-system)
13. [🧪 Testing](#-testing)
14. [🐳 Docker Deployment](#-docker-deployment)
15. [🛤️ Roadmap](#️-roadmap)
16. [🤝 Contributing](#-contributing)
17. [📄 License](#-license)
18. [🙏 Acknowledgements](#-acknowledgements)

---

## ✨ Project Overview

**JARVIS (Just A Rather Very Intelligent System) V2.0** is a production-grade, modular AI personal assistant inspired by Iron Man's iconic AI companion. It combines **speech recognition**, **text-to-speech**, **LLM-powered reasoning**, **vector-based long-term memory**, **PC automation**, **biometric authentication**, and **smart-home control** into a single cohesive system — all wrapped in a stunning neon purple/pink/cyan luxury-themed React dashboard.

Built with a **FastAPI + Python backend** and a **React + Vite + Tailwind frontend**, JARVIS communicates via **REST + WebSockets** for real-time chat streaming, live system metrics, and voice biometrics.

### 🎯 Design Philosophy

- **Modular & Extensible** — Pluggable architecture with a full plugin SDK, skill handlers, and vector memory
- **Privacy-First** — Runs locally; optional cloud LLM providers (OpenAI, Gemini, Anthropic, OpenRouter)
- **Cross-Platform** — Windows, macOS, Linux (PC-control mapping per OS)
- **Production-Ready** — Pydantic validation, structured logging (loguru), typed schemas, Docker configs, test suite
- **Luxury Aesthetic** — Custom Tailwind theme with animated orbs, neon glow effects, framer-motion transitions, live waveform visualization

---

## 🚀 Key Features

### 🗣️ Voice & Multilingual Interaction
- Wake-word detection ("Jarvis") with Porcupine or local hybrid engine
- Speech-to-Text via SpeechRecognition or **OpenAI Whisper** (GPU-accelerated)
- Text-to-Speech via pyttsx3 (offline), gTTS, or **edge-tts** (high-quality neural voices)
- Auto language detection (`langdetect`) & 40+ languages via multilingual module
- Speaker diarization, SSML processing, emotional TTS, voice cloning support

### 🧠 AI & Reasoning
- **Multi-LLM Provider Chain** — OpenAI GPT-4o, Google Gemini 1.5, Anthropic Claude, OpenRouter (auto-fallback)
- **Hybrid Memory Architecture**
  - **Short-term**: In-memory conversation history (200 turns, configurable)
  - **Long-term**: ChromaDB vector store w/ SentenceTransformer embeddings (`all-MiniLM-L6-v2`)
  - **Enhanced RAG** + Knowledge Graph + Document Processor (PDF/TXT/Word with OCR via pytesseract)
- **Intent Classifier** — Custom TF-IDF + SVM ML model, retrainable on demand
- **Self-thinking Agent** (`JarvisAgent`) with hierarchical planner & active learning loop
- **Advanced Web Search** — DuckDuckGo Go + Wikipedia + BeautifulSoup4 scraping

### 💻 PC Control & Automation
- **Open/Close 30+ Apps** — Chrome, Edge, VS Code, Word, Excel, Spotify, Discord, Terminal, Settings, etc.
- **System Actions** — Shutdown, Restart, Sleep, Hibernate, Lock, Logout
- **Media Control** — Volume (pycaw), Brightness, Play/Pause/Next Track, Mute
- **File Management** — Browse, Open Folders, Create/Delete files, Virtual File Manager UI
- **Input Automation** — PyAutoGUI keyboard/mouse, PyInput hotkeys, Clipboard stack
- **Window Management** — Min/Max/Close/Switch windows (pygetwindow)
- **Screen Capture** — Screenshot + OCR + Screen Understanding (Pillow + cv2)

### 🔐 Security & Identity
- **Biometric Authentication**
  - Face Recognition (face-recognition library, dlib-based)
  - Voice Biometrics (feature-template matching)
  - Multi-factor mode with lockout (5 failed attempts → 30 min lock)
- Token-based auth (SHA-256 hashed passwords + 7-day JWT-style tokens)
- Encryption Manager + Audit Logger + Data Retention policies
- User profiles with RBAC (`admin` / `user` / `guest`) + per-user permissions (shutdown PC, delete files)

### 📅 Productivity & Integrations
- **Natural-Language Reminders** — "Remind me at 5pm to call Mom" → APScheduler cron/jobs
- **Calendar Conflict Detection** + Meeting Prep Agent
- **Email Processor** (Gmail API via google-api-python-client)
- **Microsoft 365** + CRM + Todoist integrations
- **WhatsApp** message sending (pywhatkit)
- **Music Services** (Spotify API) + Cloud Services integrations
- **Workflow Automation** engine

### 🏠 Smart Home
- Home Assistant integration
- Matter/Thread protocol support
- Scene Automation + Energy Monitor
- Person Detection (OpenCV) + Video Streaming

### 🎛️ Developer Experience
- **Plugin SDK** with marketplace, dependency manager, GraphQL API
- Customizable Dashboard UI (drag-drop widgets)
- Collaborative Sessions + Accessibility features
- Usage Analytics + Monitoring + Caching + Query Optimizer
- Browser Extension skeleton + Desktop (Tkinter/PyQt) app skeleton + Mobile (React Native) skeleton

---

## 🛠️ Technology Stack

### 🐍 Backend — Python 3.11+

| Icon | Technology | Purpose |
|------|-----------|---------|
| <img src="https://skillicons.dev/icons?i=fastapi" width="32" height="32" /> | **FastAPI** | High-performance async web framework with auto-generated OpenAPI docs |
| <img src="https://skillicons.dev/icons?i=python" width="32" height="32" /> | **Python 3.11+** | Core runtime for AI, ML, and PC automation |
| <img src="https://trychroma.com/favicon.ico" width="32" height="32" /> | **ChromaDB** | Open-source vector database for semantic long-term memory |
| 🤗 | **HuggingFace Transformers** | Whisper STT, embeddings, LLM backbones |
| 🔥 | **PyTorch** | ML/DL engine for neural models (CUDA optional) |
| 🎙️ | **SpeechRecognition** | Microphone input + Google/Whisper STT engines |
| 🔊 | **edge-tts** | High-quality Microsoft neural voices (offline-capable cache) |
| 🦜 | **pyttsx3 / gTTS** | Offline & Google TTS fallbacks |
| ⏰ | **APScheduler** | Reminder scheduling (cron, interval, date triggers) |
| 📊 | **Pydantic v2** | Runtime type validation + `.env` settings management |
| 📝 | **Loguru** | Structured, colorful, rotating-file logging |
| 🔌 | **WebSockets** | Real-time chat streaming + live metrics push |
| 🪟 | **PyAutoGUI / PyInput** | Keyboard/mouse automation for PC control |
| 💿 | **psutil / pycaw** | System metrics + Windows Core Audio volume control |
| 👁️ | **face-recognition** | dlib-based face detection + encoding matching |
| 🔍 | **scikit-learn** | TF-IDF + SVM intent classifier (retrainable) |
| 📚 | **NLTK** | Tokenization, text preprocessing for NLP |
| 🔎 | **Sentence-Transformers** | `all-MiniLM-L6-v2` embedding model for vector search |
| 🦆 | **ddgs (DuckDuckGo)** | Privacy-first web search + news lookup |
| 📧 | **Google API Client** | Gmail + Calendar + M365 integrations |
| 🦓 | **Pytest** | Unit + integration test suite (14+ test modules) |

### ⚛️ Frontend — React 18 + Vite 5

| Icon | Technology | Purpose |
|------|-----------|---------|
| <img src="https://skillicons.dev/icons?i=react" width="32" height="32" /> | **React 18.3** | Component-based UI with concurrent rendering |
| <img src="https://skillicons.dev/icons?i=vite" width="32" height="32" /> | **Vite 5.4** | Lightning-fast dev server + optimized production builds |
| <img src="https://skillicons.dev/icons?i=tailwindcss" width="32" height="32" /> | **Tailwind CSS 3.4** | Utility-first CSS with custom JARVIS neon theme |
| 🐻 | **Zustand** | Minimal, fast state management (2 stores: auth + app) |
| 💫 | **Framer Motion** | Page transitions, orbs, pulse-glow animations, stagger effects |
| 🗺️ | **React Router v7** | Login/Signup/Biometric → Main app route protection |
| 📈 | **Recharts** | Real-time CPU/RAM/Network line charts (System Dashboard) |
| 🔗 | **Axios** | HTTP client w/ interceptors & unified error handling |
| 🧭 | **Lucide React** | Clean icon set for all UI components |
| ⏱️ | **date-fns** | Date/time formatting for reminders & timestamps |
| 🌐 | **Native WebSockets** | Custom `JarvisWS` class w/ auto-reconnect & exponential backoff |

### 🧰 DevOps & Tooling

| Icon | Technology | Purpose |
|------|-----------|---------|
| <img src="https://skillicons.dev/icons?i=docker" width="32" height="32" /> | **Docker** | Slim Python 3.11 image w/ health-check (config generator included) |
| <img src="https://skillicons.dev/icons?i=git" width="32" height="32" /> | **Git** | Version control |
| <img src="https://skillicons.dev/icons?i=vscode" width="32" height="32" /> | **VS Code** | Recommended IDE |
| 📱 | **React Native** | Mobile app skeleton (iOS/Android) |
| 🌐 | **Browser Extension** | Chrome/Firefox extension skeleton (manifest config ready) |
| 🖥️ | **Tkinter/PyQt** | Cross-platform desktop app skeleton |

---

## 📁 Project Structure

```
Ai Voice Assstant/
├── 🐍 main.py                              # CLI entrypoint (text/voice/wake/test/retrain)
├── 📋 requirements.txt                     # 63+ Python dependencies
├── ⚙️ .env.example                         # Environment template (create .env from this)
├── 📖 README.md                            # This file
├── 🧪 test_all_modules.py                  # Global test runner
├── 🧪 test_biometric.py                    # Biometric auth standalone tests
├── 🧪 _check_env.py                        # Dependency/env checker utility
├──
├── assistant/                               # ✅ Core backend package
│   ├── config.py                           # Pydantic-settings config (ROOT, DATA, ports, API keys)
│   │
│   ├── core/                               # ⚙️ Assistant brain
│   │   ├── assistant.py                    # AIAssistant orchestrator class (main entry)
│   │   ├── llm_core.py                     # Multi-provider LLM chain + offline fallback
│   │   ├── agent.py                        # JarvisAgent self-thinking/planning loop
│   │   ├── hierarchical_planner.py         # Task decomposition planner
│   │   ├── data_provider.py                # Weather, country, currency, time APIs
│   │   ├── pc_controller.py                # App/system/file/media/input control (cross-OS)
│   │   ├── auto_learner.py                 # Active learning from user feedback
│   │   ├── active_learning.py              # Uncertainty sampling + online fine-tune
│   │   ├── advanced_web_search.py          # DuckDuckGo + Wikipedia + scraping
│   │   └── offline_mode.py                 # Graceful offline fallback stack
│   │
│   ├── voice/                              # 🎙️ Speech pipeline
│   │   ├── stt.py                          # SpeechToText (sr / whisper engines)
│   │   ├── tts.py                          # TextToSpeech (pyttsx3 / gtts / edge-tts)
│   │   ├── wake_word.py                    # Basic wake-word detection
│   │   ├── advanced_wake_word.py           # Porcupine + hybrid wake engine
│   │   ├── wake_word_trainer.py            # Custom wake-word trainer
│   │   ├── streaming_transcription.py      # Real-time streaming STT
│   │   ├── multilingual.py                 # 40+ lang detect + edge-tts voice mapper
│   │   ├── emotional_tts.py                # Affective tone synthesis
│   │   ├── voice_cloning.py                # Voice cloning (Coqui/TTS wrapper)
│   │   ├── speaker_diarization.py          # Multi-speaker separation
│   │   ├── ssml_processor.py               # SSML markup parser
│   │   └── audio_enhancement.py            # Denoise + gain + VAD
│   │
│   ├── memory/                             # 🧠 Memory subsystems
│   │   ├── conversation_memory.py          # Short-term turns (list-based, LRU-cap)
│   │   ├── vector_memory.py                # Long-term ChromaDB semantic store
│   │   ├── enhanced_rag.py                 # RAG w/ query rewriting + re-ranking
│   │   └── knowledge_graph.py              # Entity-relation graph memory
│   │
│   ├── nlp/                                # 📚 NLP layer
│   │   ├── intent_classifier.py            # TF-IDF + SVM (retrainable, ~20 intents)
│   │   └── few_shot_intent_classifier.py   # Few-shot LLM-based intent fallback
│   │
│   ├── skills/                             # 🎯 Built-in skills
│   │   ├── skill_handler.py                # 20+ dispatch: time/date/weather/calc/joke/search/translate...
│   │   ├── reminder_scheduler.py           # NL parser → APScheduler jobs
│   │   ├── productivity_skills.py          # Email/meeting/task workflows
│   │   └── email_processor.py              # Gmail/M365 inbox processing
│   │
│   ├── plugins/                            # 🧩 Extensibility
│   │   ├── plugin_manager.py               # Auto-discover .py plugins, match patterns, dispatch
│   │   ├── plugin_marketplace.py           # Registry/install system
│   │   └── plugin_dependency_manager.py    # Plugin pip deps resolver
│   │
│   ├── identity/                           # 👤 Identity & profiles
│   │   └── user_profiles.py                # Multi-user CRUD, permissions, active-user switching
│   │
│   ├── security/                           # 🔐 Security suite
│   │   ├── biometric_auth.py               # Face + voice biometrics (enroll/authenticate/lockout)
│   │   ├── encryption_manager.py           # Field-level encryption utilities
│   │   ├── audit_logger.py                 # Tamper-evident audit trail
│   │   └── data_retention.py               # GDPR-style retention policies
│   │
│   ├── server/                             # 🌐 FastAPI server
│   │   ├── app.py                          # create_app() — routes, WS, CORS, singleton assistant
│   │   ├── schemas.py                      # All Pydantic v2 request/response models
│   │   └── auth.py                         # login/signup/logout/verify/biometric endpoints
│   │
│   ├── integrations/                       # 🔗 External services
│   │   ├── microsoft365.py
│   │   ├── crm_integration.py
│   │   ├── music_services.py
│   │   └── cloud_services.py
│   │
│   ├── smarthome/                          # 🏠 Home automation
│   │   ├── home_assistant.py
│   │   ├── matter_thread.py
│   │   ├── scene_automation.py
│   │   ├── energy_monitor.py
│   │   ├── person_detection.py
│   │   └── video_streaming.py
│   │
│   ├── productivity/                       # 📈 Productivity tools
│   │   ├── task_parser.py
│   │   ├── calendar_conflict.py
│   │   ├── meeting_prep.py
│   │   ├── project_integration.py
│   │   └── workflow_automation.py
│   │
│   ├── document_processor/                 # 📄 RAG document ingest
│   │   └── document_processor.py           # PDF/Word/TXT + OCR (pytesseract) → vectorize
│   │
│   ├── emotion/                            # 💬 Affective layer
│   │   ├── sentiment_analyzer.py
│   │   ├── adaptive_response.py
│   │   └── personality_system.py
│   │
│   ├── vision/                             # 👁️ Computer vision
│   │   └── screen_understanding.py         # Screenshot → OCR → scene graph
│   │
│   ├── developer/                          # 🛠️ SDK & APIs
│   │   ├── sdk.py
│   │   ├── graphql_api.py
│   │   └── plugin_dependency_manager.py
│   │
│   ├── ui/                                 # 🎨 UI helpers
│   │   ├── customizable_dashboard.py
│   │   ├── collaborative_sessions.py
│   │   └── accessibility.py
│   │
│   ├── performance/                        # ⚡ Perf optimizations
│   │   ├── caching.py
│   │   ├── monitoring.py
│   │   └── query_optimizer.py
│   │
│   ├── analytics/                          # 📊 Usage analytics
│   │   └── usage_analytics.py
│   │
│   └── utils/                              # 🧰 Shared utilities
│       ├── logger.py                       # Loguru wrapper with rotation/retention
│       └── json_encoder.py
│
├── frontend/                               # ⚛️ React + Vite Web UI
│   ├── index.html
│   ├── package.json                        # React 18 + Vite 5 + Zustand + Framer-Motion + Recharts
│   ├── vite.config.js                      # Port 3000, proxy /api → :8000, /ws → ws://:8000
│   ├── tailwind.config.js                  # Custom jarvis palette, 15+ keyframe animations
│   ├── postcss.config.js
│   │
│   └── src/
│       ├── main.jsx                        # ReactDOM root
│       ├── App.jsx                         # Router, boot sequence, WS init, orbs/logo
│       ├── index.css                       # @tailwind base/components/utilities + glass class
│       │
│       ├── api/client.js                   # Axios jarvisApi + JarvisWS auto-reconnect class
│       │
│       ├── store/
│       │   ├── authStore.js                # Zustand persist store: login/signup/logout/checkAuth
│       │   └── useJarvisStore.js           # App state: tabs, messages, streaming, metrics, memory...
│       │
│       └── components/
│           ├── Sidebar.jsx                 # Animated nav: Chat / Dashboard / Skills / Reminders / Profiles / Memory / Settings
│           ├── ChatPanel.jsx               # Streaming chat UI, mic button, waveform, token streaming
│           ├── SystemDashboard.jsx         # Recharts live CPU/RAM/NET + process stats
│           ├── WaveformAnimation.jsx       # Pure-CSS neon animated bars
│           ├── MemoryPanel.jsx             # Short/Long-term memory stats + clear actions
│           ├── RemindersPanel.jsx          # CRUD reminders with NL parsing
│           ├── ProfilesPanel.jsx           # Multi-user profile management, permissions
│           ├── SkillsPanel.jsx             # List of installed skills & plugins
│           ├── SettingsPanel.jsx           # Update TTS/STT/LLM/keys/flags via API
│           ├── Login.jsx + Login.css       # Login screen (creds + biometric button)
│           ├── Signup.jsx + Signup.css     # Registration flow
│           └── BiometricEnroll.jsx         # Face & voice enrollment wizard (+CSS)
│
├── plugins/                                # 🧩 Drop plugins here (auto-discovered)
│   └── __init__.py
│
├── mobile/                                 # 📱 React Native mobile skeleton
│   ├── App.js, index.js, app.json, package.json
│   └── src/screens/ (Home / Chat / Metrics / Settings)
│
├── desktop/                                # 🖥️ Desktop app skeleton (Tkinter)
│   ├── desktop_app.py
│   └── app_config.json
│
├── browser_extension/                      # 🌐 Web extension skeleton
│   ├── extension_manager.py
│   └── extension_config.json
│
├── deployment/                             # 🐳 Docker & CI/CD helpers
│   ├── docker_configs.json                 # 25+ pre-generated Docker configs
│   └── docker_ci_cd.py                     # Config generator script
│
├── tests/                                  # 🧪 Pytest suite (14 modules)
│   ├── conftest.py
│   ├── test_cases.json / voice_tests.json  # Fixture data
│   ├── test_intent_classifier.py
│   ├── test_conversation_memory.py
│   ├── test_vector_memory.py
│   ├── test_skill_handler.py
│   ├── test_reminder_scheduler.py
│   ├── test_productivity_skills.py
│   ├── test_user_profiles.py
│   ├── test_plugin_manager.py
│   ├── test_multilingual.py
│   ├── test_advanced_wake_word.py
│   ├── voice_testing.py
│   └── e2e_testing.py
│
├── data/                                   # 💾 Auto-created runtime dirs
│   ├── chroma_db/                          # ChromaDB vector persist directory
│   ├── reminders.json                      # APScheduler reminder records
│   ├── user_profiles.json                  # Identity profile data
│   ├── custom_qa.json                      # Custom Q&A pairs
│   ├── users.json                          # Auth user database (hashed)
│   ├── tokens.json                         # Auth token store
│   ├── biometric_auth/                     # Biometric templates + attempts
│   └── face_encodings.pkl                  # Face recognition encoding cache
│
├── models/                                 # 🤖 Auto-created ML model dir
│   ├── intent_classifier.pkl               # Trained TF-IDF + SVM pipeline
│   └── intents_data.pkl                    # Intent-label corpus
│
├── logs/                                   # 🪵 Auto-created log directory (loguru rotation)
│
└── Screenshots/                            # 📸 18 UI showcase screenshots
```

---

## ⚙️ Prerequisites

| Requirement | Minimum Version | Notes |
|-------------|-----------------|-------|
| **Python** | 3.11+ | 3.12 recommended for faster asyncio |
| **Node.js** | 18.17+ | LTS 20.x recommended (for Vite 5) |
| **npm** | 9+ | Bundled with Node.js |
| **Operating System** | Windows 10+ / macOS 12+ / Ubuntu 22.04+ | PC-control features are OS-aware |
| **Microphone** | Any | Required for voice & wake-word modes |
| **Speakers** | Any | Required for TTS output |
| **Webcam** | Any | Optional (face recognition enrollment) |
| **GPU (Optional)** | CUDA 11.8+ | Greatly speeds up Whisper + embeddings |
| **RAM** | 4 GB minimum, 8 GB recommended | 16 GB if running local LLMs + Whisper |
| **Disk** | 4 GB free | Models, chroma_db, and dependencies |

### 🧩 Optional External Dependencies

- **PyAudio** (for microphone access on some systems):
  ```bash
  # Windows (use pipwin or prebuilt wheel):
  pip install pipwin && pipwin install pyaudio
  # macOS:
  brew install portaudio && pip install pyaudio
  # Ubuntu/Debian:
  sudo apt-get install portaudio19-dev python3-pyaudio
  ```
- **Tesseract OCR** (for document OCR + screen understanding):
  ```bash
  # Windows: install from https://github.com/UB-Mannheim/tesseract/wiki
  # macOS: brew install tesseract
  # Ubuntu: sudo apt-get install tesseract-ocr
  ```
- **FFmpeg** (for audio processing, pydub, edge-tts caching):
  ```bash
  # Windows: choco install ffmpeg
  # macOS: brew install ffmpeg
  # Ubuntu: sudo apt-get install ffmpeg
  ```

---

## 📦 Installation

### 1️⃣ — Clone & Enter Project

```bash
cd "c:\Users\shaik\Downloads\Ai Voice Assstant"
```

### 2️⃣ — Create Python Virtual Environment (Recommended)

```bash
# Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate
```

### 3️⃣ — Install Python Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

> ⏳ First install can take 3-10 minutes because of heavy packages: **PyTorch**, **Transformers**, **face-recognition (dlib)**, **OpenCV**, **ChromaDB**.

> 💡 **Windows tip for dlib/face-recognition**: If `face-recognition` fails to build, install CMake + Visual Studio Build Tools (Desktop C++ workload) first, then retry. Alternatively, you can skip this feature by commenting out `face-recognition>=1.3.0` in [requirements.txt](file:///c:/Users/shaik/Downloads/Ai%20Voice%20Assstant/requirements.txt) and setting `ENABLE_FACE_RECOGNITION=false` in `.env`.

### 4️⃣ — Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 5️⃣ — Verify Installation

```bash
# Run built-in diagnostic suite (7 checks)
python main.py --test
```

You should see something like:
```
[PASS] Intent classifier: 10/10 patterns recognized.
[PASS] Skill handler working correctly.
[PASS] Conversation memory working correctly.
[PASS] LLM ready (provider chain available).
[PASS] Country lookup: India ...
[PASS] System info: Windows | CPU cores: ...
[PASS] Core assistant stack working correctly.
Diagnostics complete! Passed: 7/7. JARVIS is READY.
```

---

## 🔧 Configuration

All runtime configuration is managed via **environment variables** loaded from a `.env` file at the project root (auto-discovered by [config.py](file:///c:/Users/shaik/Downloads/Ai%20Voice%20Assstant/assistant/config.py)).

### Create `.env`

```bash
# Windows (PowerShell):
Copy-Item .env.example .env

# macOS/Linux:
cp .env.example .env
```

If `.env.example` doesn't exist yet, create a `.env` file with these contents:

```dotenv
# ==========================================
# JARVIS AI Assistant — Environment Config
# ==========================================

# ---- LLM Provider API Keys (pick at least ONE) ----
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxx
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxx

# ---- Wake-Word (Porcupine — optional, higher quality) ----
# Get free key at https://console.picovoice.ai/
PORCUPINE_ACCESS_KEY=

# ---- Assistant Behavior ----
ASSISTANT_NAME=Jarvis
WAKE_WORD=jarvis
JARVIS_WAKE_SENSITIVITY=0.65
JARVIS_LANGUAGE=en-US
JARVIS_TTS_ENGINE=pyttsx3           # pyttsx3 | gtts | edge-tts
JARVIS_STT_ENGINE=sr                # sr | whisper
CONFIDENCE_THRESHOLD=0.20

# ---- TTS defaults ----
DEFAULT_TTS_VOICE=en-US-ChristopherNeural
DEFAULT_TTS_RATE=200
DEFAULT_TTS_VOLUME=1.0

# ---- Server ----
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# ---- Vector Memory (ChromaDB) ----
CHROMA_PERSIST_DIR=./data/chroma_db
CHROMA_COLLECTION_NAME=jarvis_memory
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_MEMORY_TOP_K=5
VECTOR_MEMORY_MIN_SCORE=0.35
ENABLE_VECTOR_MEMORY=true

# ---- Feature Flags ----
ENABLE_AGENT=true
ENABLE_FACE_RECOGNITION=false
FACE_RECOGNITION_TOLERANCE=0.6

# ---- Storage Paths ----
REMINDER_DB_PATH=./data/reminders.json
USER_PROFILES_PATH=./data/user_profiles.json
CUSTOM_QA_PATH=./data/custom_qa.json
FACE_ENCODINGS_PATH=./data/face_encodings.pkl

# ---- Logging ----
LOG_LEVEL=INFO
LOG_FILE=./logs/jarvis_{time}.log
MAX_CONVERSATION_HISTORY=200
```

### 🔑 Getting API Keys

| Provider | URL | Free Tier? |
|----------|-----|------------|
| OpenAI GPT | https://platform.openai.com/api-keys | $5 credit for new users |
| Google Gemini | https://aistudio.google.com/apikey | ✅ 15 RPM free tier |
| Anthropic Claude | https://console.anthropic.com/ | $5 credit for new users |
| OpenRouter (meta-provider) | https://openrouter.ai/keys | Many free models |
| Picovoice Porcupine | https://console.picovoice.ai/ | ✅ Free tier |

---

## ▶️ Running the Project

### 🎯 Quick Start (Full Stack)

Open **two terminals** in the project root:

#### Terminal 1 — Backend Server (FastAPI on port 8000)
```bash
# Option A — via uvicorn directly (recommended for web UI):
uvicorn assistant.server.app:get_app --host 127.0.0.1 --port 8000 --reload

# Option B — server starts assistant lazily on first API call
```

#### Terminal 2 — Frontend Dev Server (Vite on port 3000)
```bash
cd frontend
npm run dev
```

Now open **http://localhost:3000** in your browser. You'll see:
1. **Login / Signup screen** → create an account
2. **(Optional)** Biometric enrollment via `/enroll` route
3. **Main Dashboard** → enjoy JARVIS!

> ✅ The Vite dev server auto-proxies `/api/*` → `http://localhost:8000` and `/ws/*` → `ws://localhost:8000`, so no extra CORS setup is needed in development.

---

### 🎙️ CLI Modes (Standalone — no frontend needed)

Run directly via [main.py](file:///c:/Users/shaik/Downloads/Ai%20Voice%20Assstant/main.py):

| Command | Mode | Description |
|---------|------|-------------|
| `python main.py` | **Text (default)** | Type queries, get text + optional voice replies |
| `python main.py --text` | **Text-only** | Force no TTS even if engine available |
| `python main.py --voice` | **Voice I/O** | Listen mic → transcribe → speak reply |
| `python main.py --wake` | **Wake-word** | Idle until you say **"Jarvis"**, then respond |
| `python main.py --test` | **Diagnostics** | Run 7-module sanity check suite |
| `python main.py --retrain` | **Re-train** | Rebuild intent classifier from corpus |

#### Extra CLI flags

```bash
# Use Whisper for STT + edge-tts for TTS:
python main.py --voice --stt-engine whisper --tts-engine edge-tts

# Force a specific LLM model:
python main.py --voice --llm gpt-4o
python main.py --text --llm gemini-1.5-flash
python main.py --text --llm claude-3-haiku

# Disable self-thinking agent for faster responses:
python main.py --text --no-agent
```

---

### 🏗️ Production Build

```bash
# 1. Build frontend
cd frontend
npm run build     # outputs to frontend/dist/
cd ..

# 2. Backend serves frontend/dist under /app
uvicorn assistant.server.app:get_app --host 0.0.0.0 --port 8000
```

Then visit: **http://localhost:8000/app/**

---

## 💡 How to Use

### 1️⃣ — First Login

1. Start the stack (see above).
2. Navigate to **http://localhost:3000**.
3. Click **Sign Up** → enter username, password, optional email.
4. You'll be auto-logged in and redirected to the Chat panel.
5. (Optional) Visit **http://localhost:3000/enroll** to enroll face & voice biometrics.

### 2️⃣ — Chat Panel

- **Text mode**: Type any message at the bottom input, press Enter.
- **Voice mode**: Click the mic icon 🎙️ (needs microphone permission).
- **Streaming**: JARVIS streams tokens character-by-character over WebSockets.
- **Intent + confidence scores**: Each response shows detected intent (e.g. `reminder`, `calculator`, `weather`).
- **Waveform animation**: Live neon visualizer when assistant is "speaking".

### 3️⃣ — Try These Example Commands

```text
General
———————
• Hello, how are you?
• What is your name?
• Tell me a joke.
• Thank you!

Time & Date
———————————
• What time is it?
• What's today's date?
• What time is it in Tokyo?

Weather & World
———————————————
• What's the weather in New York?
• Tell me about India.
• Convert 100 USD to INR.

Math
————
• What is 12 * 5 + 30?
• Calculate 256 squared.
• Solve (144 / 12) + 8

Productivity
————————————
• Remind me to take a break in 1 hour
• Show my reminders
• Send a WhatsApp message
• Translate "Good morning" to Spanish

PC Control
——————————
• Open Chrome
• Open VS Code
• Open Calculator
• Open Spotify
• Turn up the volume
• Mute the system
• Increase screen brightness
• Take a screenshot
• Close Edge
• Show system info

Smart & Fun
———————————
• Search the web for Python async best practices
• News about AI
• Play music
• Switch to female voice
```

### 4️⃣ — System Dashboard Tab

Live-updating charts (pushed via WebSockets every 1.5s):
- CPU % + frequency
- RAM used/total GB
- Disk usage
- Network up/down (Mbps)
- Uptime, process count, load average

### 5️⃣ — Memory Tab

View your **hybrid memory stats**:
- Short-term turns (conversation history)
- Long-term items (ChromaDB vector count)
- Index size on disk
- Top-K / min-score knobs
- Clear short / long / all memory

### 6️⃣ — Reminders Tab

- Click **Add Reminder** → e.g. `text: "Team standup"`, `when: "every weekday at 9:30am"`.
- Reminder scheduler uses natural-language parsing → APScheduler-backed persistent jobs.
- Triggered reminders fire audio + UI toast alert.

### 7️⃣ — Profiles Tab

Multi-user support with granular permissions:
- **Admin** → `can_shutdown_pc: true`, `can_delete_files: true`
- **User** → standard access
- **Guest** → read-only chat
- Click **Activate** to switch the assistant's active identity (language, TTS voice gender adapt).

### 8️⃣ — Settings Tab

Update in real-time (writes to `.env` automatically):
- Assistant name / wake-word / sensitivity
- TTS engine (pyttsx3 / gtts / edge-tts) + voice + rate
- STT engine (SpeechRecognition / Whisper)
- Feature toggles (agent, vector memory, face recognition)
- Top-K / min-score vector memory params
- Paste and save API keys securely (masked in UI responses)

---

## 🧠 Architecture Deep-Dive

```
                    ┌───────────────────────────────────────────────┐
                    │            Frontend (React + Vite)            │
                    │  Zustand stores │ Framer Motion │ Recharts    │
                    │  Axios (/api)    │  WebSockets (/ws/*)        │
                    └───────────────────┬───────────────────────────┘
                                        │
               HTTP REST / JSON         │      WebSocket / JSON
           (chat, metrics, CRUDs, auth) │   (chat streaming, metrics push)
                                        ▼
          ┌────────────────────────────────────────────────────────────────┐
          │                    FastAPI Server (app.py)                      │
          │  CORS │ Startup singleton │ Lifespan │ Pydantic schemas        │
          │  /api/* endpoints       │ /ws/chat │ /ws/metrics               │
          └───────────────────────────┬────────────────────────────────────┘
                                      │
                    Singleton: ─────── ▼ ────────────────────────────
                    │       AIAssistant (assistant/core/assistant.py) │
                    │                                                   │
                    │  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
                    │  │  Intent    │  │    LLM     │  │   Skill    │  │
                    │  │Classifier  │  │  Core      │  │  Handler   │  │
                    │  │ TF-IDF+SVM │  │4 providers │  │20+ intents │  │
                    │  └────────────┘  └────────────┘  └────────────┘  │
                    │                                                   │
                    │  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
                    │  │ Short-Term │  │ Long-Term  │  │ Enhanced   │  │
                    │  │ Conversation│  │  Vector    │  │   RAG      │  │
                    │  │   Memory   │  │ (ChromaDB) │  │ + KG       │  │
                    │  └────────────┘  └────────────┘  └────────────┘  │
                    │                                                   │
                    │  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
                    │  │   Voice    │  │   PC       │  │  Reminder  │  │
                    │  │  STT/TTS   │  │ Controller │  │ Scheduler  │  │
                    │  │  + Wake    │  │ (cross-OS) │  │APScheduler │  │
                    │  └────────────┘  └────────────┘  └────────────┘  │
                    │                                                   │
                    │  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
                    │  │  Plugin    │  │  Security  │  │  Profiles  │  │
                    │  │  Manager   │  │  (Bio/Auth)│  │  Manager   │  │
                    │  └────────────┘  └────────────┘  └────────────┘  │
                    └───────────────────────────────────────────────────┘
```

### 🧩 Key Architectural Decisions

| Decision | Why |
|----------|-----|
| **Hybrid Memory** | LLM context is finite — semantic vector memory scales to 100k+ items; short-term memory preserves conversation flow. |
| **Multi-Provider LLM Chain** | No single vendor lock-in + graceful fallback: GPT → Gemini → Anthropic → local/offline rule engine. |
| **Intent Classifier before LLM** | 80% of queries are deterministic (time, date, calc) — no LLM tokens needed, faster & cheaper. |
| **Pydantic v2 + .env settings** | Typed, validated config at startup — no runtime `KeyError`s from misconfigured env. |
| **Zustand (not Redux)** | 1/5th the boilerplate; persist middleware handles auth token refresh automatically. |
| **WS + REST dual API** | REST for simple CRUDs, WS for streaming tokens & 1.5s metrics push (no HTTP polling). |
| **Plugin auto-discovery** | Drop a `.py` file in `/plugins` with `INTENT_PATTERNS + handle()` — it works, no config edit. |

---

## 🔌 API Reference

The FastAPI server auto-generates **Swagger UI** and **ReDoc** documentation:

- **Swagger UI** → http://localhost:8000/docs
- **ReDoc** → http://localhost:8000/redoc
- **OpenAPI JSON** → http://localhost:8000/openapi.json

### 🗂️ Endpoint Cheat-Sheet

All REST endpoints live under `/api/`.

#### 🔐 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login` | `{ username, password }` → `{ success, token, user }` |
| `POST` | `/auth/signup` | `{ username, password, email? }` → register + auto-login |
| `POST` | `/auth/logout?token=` | Invalidate token server-side |
| `GET`  | `/auth/verify?token=` | Validate token expiry & user |
| `POST` | `/auth/biometric` | `{ username, face_features?, voice_features? }` → bio-login |
| `POST` | `/auth/enroll` | `username, auth_method, features[]` → enroll face/voice |
| `POST` | `/auth/check-biometric` | `username` → `{ has_biometric, has_face, has_voice }` |

#### 🖥️ System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | `{ status: "ok", uptime_sec }` (health-check) |
| `GET`  | `/status` | `AssistantStatus` — assistant mode, keys, features, plugins, skills |
| `GET`  | `/metrics` | `SystemMetrics` — CPU, RAM, Disk, NET, processes, load avg |

#### 💬 Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | `ChatRequest { message, user_id, speak, mode }` → `ChatResponse` w/ `thinking_ms` |
| `WS`   | `/ws/chat` | Send `{ message, user_id }` → receive `start` + `token*N` + `end` frames |
| `WS`   | `/ws/metrics` | Push: system metrics JSON every 1.5 seconds |

#### ⚙️ Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/settings` | Current config (API keys masked: `sk-****2f`) |
| `PUT`  | `/settings` | `SettingsUpdate` → persists to `.env`, reload flag |

#### 🧠 Memory
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/memory` | `MemoryStats { short_term_turns, long_term_items, size_bytes, top_k, min_score }` |
| `DELETE` | `/memory?kind=[all\|short\|long]` | Clear memory stores |

#### 🔔 Reminders
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/reminders` | List `{ reminders[], count }` (includes fired & cancelled) |
| `POST` | `/reminders?text=...&when_natural=...` | NL parser → add reminder, return `{ id, fire_at }` |
| `DELETE` | `/reminders/{rid}` | Cancel reminder by id → `{ cancelled: true/false }` |

#### 👤 Profiles
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/profiles` | `{ profiles[], active_user_id }` |
| `POST` | `/profiles` | `UserProfile` body → create new profile |
| `PUT`  | `/profiles/{pid}` | Update profile fields |
| `POST` | `/profiles/{pid}/activate` | Switch active user (language + TTS adapt) |

#### 🧩 Plugins & Skills
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/plugins` | `PluginInfo[]` — name, icon, examples, intent patterns |
| `POST` | `/skills/retrain` | Rebuild intent classifier → `{ status, classes[] }` |

---

## 🧩 Plugin System

JARVIS has a first-class plugin SDK. Drop a `.py` file into `/plugins/` and it's auto-loaded on startup.

### Example Plugin (`plugins/weather_advanced.py`)

```python
"""Advanced weather plugin with forecast support."""

PLUGIN_NAME = "Weather Advanced"
ICON = "🌦️"
INTENT_PATTERNS = [
    r"weather forecast (?:for|in|at)?\s*(?P<city>\w+)",
    r"(?P<days>\d+) day forecast (?:for|in)?\s*(?P<city>\w+)",
]
EXAMPLES = [
    "weather forecast for London",
    "7 day forecast in Mumbai",
]

def handle(text: str, match, assistant=None) -> dict:
    """Return either a string or a {text, intent, data} dict."""
    city = match.group("city")
    days = match.groupdict().get("days") or 3
    # Your custom logic here (call an external API, etc.)
    return {
        "text": f"🌦️ {days}-day forecast for {city}: Mostly sunny, highs of 28°C, lows of 20°C.",
        "data": {"city": city, "days": days, "source": "open-meteo"},
    }
```

**Plugin Contract:**
- `PLUGIN_NAME: str` — Display name
- `ICON: str` — Emoji icon (optional, defaults to `🧩`)
- `INTENT_PATTERNS: list[str]` — Regex patterns (case-insensitive) — first match wins
- `EXAMPLES: list[str]` — Shown in Skills Panel UI (optional)
- `handle(text, match, assistant) -> str | dict` — The handler. Return `str` for plain text, or `dict` with at least a `text` key.
- The `assistant` kwarg lets you call back into any subsystem (LLM, PC controller, memory, etc.).

---

## 🧪 Testing

JARVIS ships with a **14-module pytest suite** plus a 7-module CLI diagnostic.

### Run All Tests

```bash
# From project root:
python -m pytest tests/ -v --tb=short

# Or use the unified test runner:
python test_all_modules.py
```

### Individual Test Modules

| Test File | What It Covers |
|-----------|----------------|
| `tests/test_intent_classifier.py` | 20+ intent accuracy, retraining, confidence calibration |
| `tests/test_conversation_memory.py` | CRUD, LRU eviction, context windowing |
| `tests/test_vector_memory.py` | ChromaDB add/search/delete, JSON fallback path, embedding dims |
| `tests/test_skill_handler.py` | All 20 built-in skills with edge cases |
| `tests/test_reminder_scheduler.py` | NL parsing, cron/interval/date jobs, fire callbacks |
| `tests/test_productivity_skills.py` | Email, meeting prep, task parser workflows |
| `tests/test_user_profiles.py` | CRUD, permissions, activate-switch cycle |
| `tests/test_plugin_manager.py` | Plugin discovery, pattern matching, dispatching |
| `tests/test_multilingual.py` | langdetect + edge-tts voice map for 10 locales |
| `tests/test_advanced_wake_word.py` | Porcupine integration, sensitivity tuning |
| `tests/voice_testing.py` | End-to-end STT → chat → TTS audio pipeline |
| `tests/e2e_testing.py` | 30-case end-to-end scenarios from test_cases.json |
| `test_biometric.py` | Standalone: enroll → authenticate → lockout flow |
| `main.py --test` | Quick 7-step diagnostic (no pytest required) |

### ✅ Sample Test Output

```
tests/test_intent_classifier.py .... PASSED
tests/test_vector_memory.py ....... PASSED
tests/test_skill_handler.py ....... PASSED
tests/test_reminder_scheduler.py .. PASSED
==== 48 passed in 34.12s ====
```

---

## 🐳 Docker Deployment

The repository ships with a **Docker config generator** in [deployment/docker_ci_cd.py](file:///c:/Users/shaik/Downloads/Ai%20Voice%20Assstant/deployment/docker_ci_cd.py) and 25+ pre-generated configurations in [deployment/docker_configs.json](file:///c:/Users/shaik/Downloads/Ai%20Voice%20Assstant/deployment/docker_configs.json).

### Quick Dockerfile (save as `Dockerfile` in project root)

```dockerfile
# --- Base image: slim Python 3.11 ---
FROM python:3.11-slim

# --- System deps for audio, dlib, opencv, tesseract (optional — trim as needed) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake pkg-config \
    ffmpeg portaudio19-dev libasound2-dev \
    tesseract-ocr tesseract-ocr-eng \
    libsm6 libxext6 libxrender-dev libglib2.0-0 \
    curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Python deps ---
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# --- App code ---
COPY . .

# --- Healthcheck (matches generated configs) ---
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "assistant.server.app:get_app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build & Run

```bash
# Build image
docker build -t jarvis-assistant:latest .

# Run with .env mounted + persistent data/volume
docker run -d --name jarvis \
  -p 8000:8000 \
  --env-file .env \
  -v jarvis_data:/app/data \
  -v jarvis_models:/app/models \
  --restart unless-stopped \
  jarvis-assistant:latest

# Verify
curl http://localhost:8000/api/health
# → {"status":"ok","uptime_sec":...}
```

> ⚠️ **Note:** Microphone, speaker, camera, and PC-control features work best on bare-metal/host runs. Docker is excellent for the **server + web UI**; pair it with a local desktop CLI client or mobile app for full hardware access.

---

## 🛤️ Roadmap

- [ ] **Fully local LLM backend** — Llama 3 / Mistral via `llama.cpp` (no cloud keys required)
- [ ] **Voice Cloning (Coqui TTS)** — Train a voice from 1 minute of samples and use it as default TTS
- [ ] **Multi-room audio** — Sync JARVIS across multiple speakers via MQTT/WebRTC
- [ ] **GraphQL API v1** — Fully typed schema with subscriptions (already scaffolded in `developer/graphql_api.py`)
- [ ] **iOS/Android Release Builds** — Out of the mobile skeleton directory
- [ ] **Electron Wrapper** — Distribute a desktop app bundle with tray-icon & hotkey mic toggle
- [ ] **Plugin Marketplace v1** — Publish & install plugins from a registry
- [ ] **Streaming STT over WebSockets** — Real-time mic input from browser to backend
- [ ] **Fine-tuning pipeline** — Active-learning feedback → LoRA fine-tunes of the intent model
- [ ] **Kubernetes Helm chart** — HA deployment w/ ChromaHA + Redis cache

---

## 🤝 Contributing

Contributions are very welcome! Here's the workflow:

1. **Fork** the repo.
2. Create a feature branch: `git checkout -b feat/voice-cloning-ui`
3. Make changes and **run tests**: `python -m pytest tests/`
4. Ensure lint/diagnostics are clean (no `GetDiagnostics` errors).
5. **Squash** your commits into meaningful messages.
6. Open a **Pull Request** with screenshots if UI is touched.

### Coding Standards

- **Python**: Follow PEP 8, use type hints everywhere, prefer `loguru` over `print`.
- **React**: Functional components + hooks, Zustand stores for shared state, no Redux.
- **Tailwind**: Use existing `jarvis-*` tokens from `tailwind.config.js` — avoid hardcoded HEX colors.
- **Schemas**: Every API route needs a corresponding Pydantic model in `schemas.py`.
- **Tests**: New features ship with corresponding pytest module + a `--test` diagnostic entry if core.

---

## 📄 License

> **Educational / Personal Use License**
>
> This project is provided for **educational and personal use only**. You are free to study, modify, and run this code on your own hardware. Commercial redistribution, SaaS hosting, or selling derivative works without explicit written permission is **prohibited**.
>
> Third-party packages used in this project retain their respective licenses (MIT, Apache 2.0, BSD, etc.). See each package's metadata for details.

---

## 🙏 Acknowledgements

A huge thank-you to the open-source community for the libraries that make JARVIS possible:

- **FastAPI** team for the cleanest async framework out there
- **ChromaDB** team for the simplest, most Pythonic vector store
- **HuggingFace** for Transformers, Datasets, and the hub
- **Picovoice** for Porcupine wake-word engine
- **Microsoft** for `edge-tts` — truly incredible free neural voices
- **dlib & ageitgey** for the `face-recognition` library
- **Tailwind Labs** + **Framer** for the beautiful UI stack
- **Iron Man (2008)** — the eternal inspiration for "a butler in a box"

---

<p align="center">
  <img src="https://img.shields.io/badge/Built%20with-%F0%9F%92%9C-ff2e88?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Made%20for-Makers-7b2ff7?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Powered%20by-AI-00eaff?style=for-the-badge" />
</p>

<p align="center">
  <strong>Questions? Issues?</strong><br />
  Open an issue in the repository or say <em>"show help"</em> to JARVIS in the chat.
</p>

---
