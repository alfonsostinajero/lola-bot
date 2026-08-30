# 🤖 Lola — Asistente IA Local para Android

<div align="center">

**Asistente de voz autónomo con IA local, auto-aprendizaje y auto-modificación de código**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Android](https://img.shields.io/badge/Android-Termux-green.svg)](https://termux.dev)
[![AI](https://img.shields.io/badge/AI-Gemma_4-orange.svg)](https://ai.google.dev/gemma)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## ¿Qué es Lola?

Lola es un asistente de IA que corre **100% local** en tu teléfono Android. No necesita internet para funcionar (excepto para Google Calendar y WhatsApp).

### ✨ Características

| Feature | Descripción |
|---|---|
| 🎤 **Wake Word** | Di "Lola" para activar (siempre escuchando) |
| 🔊 **Voz Natural** | TTS con Piper (no robótica, gratis) |
| 🧠 **IA Local** | Gemma 4 via llama.cpp (sin nube) |
| 📅 **Google Calendar** | Crear, leer y buscar eventos |
| 💬 **WhatsApp** | Enviar mensajes por voz |
| 📱 **Control de Apps** | Abrir cualquier app instalada |
| 🐍 **Ejecutar código** | Correr scripts Python |
| 📚 **Auto-aprendizaje** | Aprende de tus correcciones |
| 🔄 **Auto-modificación** | Mejora su propio código de forma segura |
| 🚀 **Auto-inicio** | Se activa al encender el teléfono |

### 📱 Hardware Requerido

- **Motorola Edge 20** (o similar con Snapdragon 778G+)
- 6+ GB RAM
- Conexión WiFi
- Sin necesidad de SIM

## 🚀 Instalación Rápida

### 1. Instalar apps en el teléfono

| App | Fuente |
|---|---|
| Termux | [F-Droid](https://f-droid.org/packages/com.termux/) |
| Termux:API | F-Droid |
| Termux:Boot | F-Droid |
| Tasker | Play Store |

> ⚠️ **NO instales Termux de Play Store**, está obsoleto.

### 2. Ejecutar el instalador

```bash
# En Termux:
cd ~
git clone https://github.com/TU_USUARIO/lola-bot.git
cd lola-bot
chmod +x setup.sh
bash setup.sh
```

El instalador hará todo automáticamente:
- Instalar paquetes del sistema
- Descargar modelo de voz español
- Instalar Piper TTS (voz natural)
- Compilar llama.cpp
- Descargar Gemma 4
- Configurar auto-inicio

### 3. Iniciar Lola

```bash
# Iniciar servidor de IA:
cd ~/llama.cpp
./build/bin/llama-server \
    -m ~/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf \
    --host 127.0.0.1 --port 8080 -c 2048 -t 4 &

# Iniciar Lola:
cd ~/lola-bot
python lola_core.py
```

O simplemente **reinicia el teléfono** — Lola inicia automáticamente.

## 🏗️ Arquitectura

```
📱 Motorola Edge 20 (Termux)
├── 🎤 Wake Word (Vosk/Porcupine) → Escucha "Lola"
├── 📝 STT (Vosk) → Voz a texto
├── 🧠 AI Engine (Gemma 4 + llama.cpp) → Procesa comandos
├── ⚡ Action Executor → Ejecuta acciones
│   ├── 📱 Abrir Apps (Android Intents)
│   ├── 📅 Google Calendar (API)
│   ├── 💬 WhatsApp (Deep Links)
│   ├── 🐍 Python (subprocess)
│   └── 🔧 Sistema (shell)
├── 🔊 TTS (Piper) → Texto a voz natural
├── 📚 Self Learner (SQLite) → Aprende del usuario
└── 🔄 Self Modifier → Mejora su código
```

## 📁 Estructura del Proyecto

```
lola-bot/
├── config.py            # Configuración central
├── lola_core.py         # Orquestador principal
├── wake_word.py         # Detección "Lola"
├── voice_handler.py     # STT + TTS (Piper)
├── ai_engine.py         # Motor IA + System Prompt
├── action_executor.py   # Ejecutor de acciones
├── calendar_helper.py   # Google Calendar
├── whatsapp_handler.py  # WhatsApp
├── self_learner.py      # Auto-aprendizaje
├── self_modifier.py     # Auto-modificación
├── utils.py             # Utilidades
├── setup.sh             # Instalador
├── requirements.txt     # Dependencias Python
└── README.md            # Esta guía
```

## 🎤 Comandos de Ejemplo

```
"Lola, abre YouTube"
"Lola, agenda una reunión mañana a las 3"
"Lola, mándale un mensaje a Pepe por WhatsApp"
"Lola, ¿qué eventos tengo esta semana?"
"Lola, ejecuta el script de backup"
"Lola, ¿qué hora es?"
"Lola, ¿cómo va tu tasa de éxito?"
```

## 🔒 Seguridad

- Los módulos `self_modifier.py` y `config.py` **NUNCA** se auto-modifican
- Todos los cambios de código requieren validación de sintaxis
- Backup automático antes de cualquier modificación
- Rollback automático si un cambio causa errores
- Comandos peligrosos del sistema están bloqueados

## 📄 Licencia

MIT License — Usa Lola libremente.

---

<div align="center">
Hecho con ❤️ para correr 100% local
</div>
