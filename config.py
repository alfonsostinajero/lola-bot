"""
config.py — Configuración central de Lola AI Assistant
Optimizado para Motorola Edge 20 (Snapdragon 778G) + Termux
"""

import os
from pathlib import Path

# ─── Versión ─────────────────────────────────────────────────
VERSION = "1.0.0"
NOMBRE = "Lola"

# ─── Detección de entorno ────────────────────────────────────
IS_TERMUX = os.path.exists("/data/data/com.termux")
IS_WINDOWS = os.name == "nt"

# ─── Rutas base ──────────────────────────────────────────────
if IS_TERMUX:
    HOME = Path(os.environ.get("HOME", "/data/data/com.termux/files/home"))
    PROJECT_DIR = HOME / "lola-bot"
    LOLA_DIR = HOME / ".lola"
else:
    HOME = Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))
    PROJECT_DIR = HOME / "Desktop" / "lola-bot"
    LOLA_DIR = HOME / ".lola"

# ─── Directorios ─────────────────────────────────────────────
DATA_DIR = LOLA_DIR / "data"
LOG_DIR = LOLA_DIR / "logs"
BACKUP_DIR = LOLA_DIR / "backups"
MODELS_DIR = LOLA_DIR / "models"

# ─── Wake Word ───────────────────────────────────────────────
WAKE_WORD = "lola"
PORCUPINE_ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY", "")

# ─── Audio ───────────────────────────────────────────────────
AUDIO_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_CHUNK = 512
SILENCE_THRESHOLD = 500
SILENCE_TIMEOUT_SEC = 2.0
LISTEN_TIMEOUT_SEC = 10

# ─── Modelos de voz ──────────────────────────────────────────
VOSK_MODEL_PATH = str(MODELS_DIR / "vosk-model-small-es-0.42")

# ─── Piper TTS (voz natural, gratuita) ───────────────────────
PIPER_BINARY = str(LOLA_DIR / "piper" / "piper")
PIPER_MODEL = str(MODELS_DIR / "es_MX-claude-high.onnx")
PIPER_MODEL_JSON = str(MODELS_DIR / "es_MX-claude-high.onnx.json")
USE_PIPER_TTS = True  # True = voz natural, False = termux-tts-speak

# ─── LLM (Gemma 4 via llama.cpp) ─────────────────────────────
LLAMA_CPP_HOST = "http://127.0.0.1"
LLAMA_CPP_PORT = 8080
LLAMA_CPP_URL = f"{LLAMA_CPP_HOST}:{LLAMA_CPP_PORT}"
LLM_ENDPOINT = "/completion"
LLM_CHAT_ENDPOINT = "/v1/chat/completions"
MODEL_PATH = str(MODELS_DIR / "gemma-4-e2b-it-Q4_K_M.gguf")
MODEL_NAME = "gemma-4-e2b"
FALLBACK_MODEL = "gemma-4-e4b"

# ─── Parámetros LLM ──────────────────────────────────────────
LLM_TEMPERATURE = 0.7
LLM_TOP_P = 0.9
LLM_MAX_TOKENS = 512
LLM_CONTEXT_SIZE = 2048
LLM_THREADS = 4  # Óptimo para Snapdragon 778G (8 cores, 4 dedicados)

# ─── TTS fallback (Android nativo) ───────────────────────────
TTS_COMMAND = "termux-tts-speak"
TTS_LANG = "es"

# ─── Google Calendar ─────────────────────────────────────────
CALENDAR_CREDENTIALS_PATH = str(DATA_DIR / "credentials.json")
CALENDAR_TOKEN_PATH = str(DATA_DIR / "token.json")
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_TIMEZONE = "America/Mexico_City"

# ─── Contactos WhatsApp ──────────────────────────────────────
CONTACTS_PATH = str(DATA_DIR / "contacts.json")

# ─── Auto-aprendizaje ────────────────────────────────────────
DB_PATH = str(DATA_DIR / "lola_learning.db")
LEARNING_CLEANUP_DAYS = 30
CORRECTION_THRESHOLD = 3  # Después de 3 correcciones, aprende automáticamente

# ─── Auto-modificación ───────────────────────────────────────
MAX_BACKUP_VERSIONS = 10
SELF_IMPROVE_INTERVAL_HOURS = 6
PROTECTED_MODULES = ["self_modifier", "config"]  # NUNCA se auto-modifican
APPROVAL_REQUIRED_MODULES = ["lola_core", "ai_engine", "action_executor"]
AUTO_MODIFY_MODULES = ["voice_handler", "calendar_helper", "whatsapp_handler", "utils"]

# ─── Mapeo de apps Android (paquete → nombre) ────────────────
APP_PACKAGES = {
    "pydroid 3": "ru.iiec.pydroid3",
    "pydroid": "ru.iiec.pydroid3",
    "chrome": "com.android.chrome",
    "whatsapp": "com.whatsapp",
    "youtube": "com.google.android.youtube",
    "spotify": "com.spotify.music",
    "telegram": "org.telegram.messenger",
    "cámara": "com.motorola.camera3",
    "camera": "com.motorola.camera3",
    "ajustes": "com.android.settings",
    "settings": "com.android.settings",
    "google maps": "com.google.android.apps.maps",
    "maps": "com.google.android.apps.maps",
    "calendar": "com.google.android.calendar",
    "calendario": "com.google.android.calendar",
    "gmail": "com.google.android.gm",
    "files": "com.google.android.apps.nbu.files",
    "archivos": "com.google.android.apps.nbu.files",
    "termux": "com.termux",
    "tasker": "net.dinglisch.android.taskerm",
    "macrodroid": "com.arlosoft.macrodroid",
}

# ─── Crear directorios al importar ───────────────────────────
for d in [DATA_DIR, LOG_DIR, BACKUP_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
