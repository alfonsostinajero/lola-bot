#!/usr/bin/env python3
"""
lola_escucha.py — Lola Voice AI (Fluido como ChatGPT/Siri)

Diseño: SIN wake word. Usted habla → Lola responde → Usted habla.
Como una conversación natural. Siempre escuchando.

Flujo:
  1. Google Speech escucha (rápido, preciso)
  2. Texto va directo a Gemma 4
  3. Lola responde por voz inmediatamente
  4. Vuelve a escuchar
"""

import subprocess
import json
import sys
import os
import time
import threading
import re
import requests

# ── Configuración ──────────────────────────────────────────
GEMMA_URL = "http://127.0.0.1:8080/v1/chat/completions"
SYSTEM_PROMPT = """Eres Lola, asistente personal del Ingeniero Alfonso Tinajero.
Respondes en español, breve y directo (máximo 2 oraciones).
Llámalo "Ingeniero", "Señor" o "Jefe" de forma variada.
Siempre de usted, nunca de tú.
Eres inteligente, cálida y eficiente."""

# Historial de conversación para contexto
historial = [{"role": "system", "content": SYSTEM_PROMPT}]
MAX_HISTORIAL = 10


def escuchar():
    """Escucha con Google Speech. Retorna texto o vacío."""
    try:
        r = subprocess.run(
            ["termux-speech-to-text"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    return ""


def pensar(texto):
    """Envía a Gemma 4 y obtiene respuesta."""
    global historial

    historial.append({"role": "user", "content": texto})

    # Mantener historial corto
    if len(historial) > MAX_HISTORIAL:
        historial = [historial[0]] + historial[-MAX_HISTORIAL:]

    try:
        r = requests.post(GEMMA_URL, json={
            "messages": historial,
            "max_tokens": 150,
            "temperature": 0.7,
        }, timeout=30)

        data = r.json()
        respuesta = data["choices"][0]["message"]["content"]

        # Si Gemma devuelve JSON, extraer respuesta_usuario
        try:
            j = json.loads(respuesta)
            if "respuesta_usuario" in j:
                respuesta = j["respuesta_usuario"]
        except (json.JSONDecodeError, TypeError):
            pass

        # Limpiar respuesta
        respuesta = respuesta.strip()
        if len(respuesta) > 300:
            respuesta = respuesta[:300]

        historial.append({"role": "assistant", "content": respuesta})
        return respuesta

    except requests.exceptions.ConnectionError:
        return "Disculpe Ingeniero, Gemma 4 no está respondiendo."
    except Exception as e:
        return f"Error procesando, Ingeniero."


def hablar(texto):
    """Habla con termux-tts-speak. Espera a que termine."""
    if not texto:
        return
    try:
        proc = subprocess.Popen(
            ["termux-tts-speak", texto],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
    except Exception:
        pass


def ejecutar_accion(texto):
    """Detecta acciones especiales y las ejecuta."""
    t = texto.lower()

    # YouTube
    if "youtube" in t or "música" in t or "canción" in t:
        busqueda = re.sub(r'(busca|pon|reproduce|en youtube|música|canción|de)\s*', '', t, flags=re.I).strip()
        if busqueda:
            url = f"https://www.youtube.com/results?search_query={busqueda.replace(' ', '+')}"
            subprocess.Popen(["termux-open-url", url],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Buscando {busqueda} en YouTube, Ingeniero."

    # Batería
    if "batería" in t or "bateria" in t:
        try:
            r = subprocess.run(["termux-battery-status"],
                               capture_output=True, text=True, timeout=5)
            info = json.loads(r.stdout)
            return f"Tiene {info.get('percentage', '?')}% de batería, Ingeniero."
        except Exception:
            pass

    # Hora
    if "hora" in t and ("qué" in t or "que" in t):
        from datetime import datetime
        ahora = datetime.now().strftime("%I:%M %p")
        return f"Son las {ahora}, Ingeniero."

    # Linterna
    if "linterna" in t or "flash" in t:
        if "apaga" in t or "apagar" in t:
            subprocess.run(["termux-torch", "off"], capture_output=True, timeout=3)
            return "Linterna apagada, Ingeniero."
        else:
            subprocess.run(["termux-torch", "on"], capture_output=True, timeout=3)
            return "Linterna encendida, Ingeniero."

    return None  # No es acción especial, usar Gemma 4


def main():
    print("")
    print("╔══════════════════════════════════════════╗")
    print("║  🤖 LOLA AI — Conversación Natural       ║")
    print("║  🎤 Solo hable, Lola siempre escucha     ║")
    print("║  🗣️  Hable normal, como con una persona  ║")
    print("║  ❌ Ctrl+C para apagar                   ║")
    print("╚══════════════════════════════════════════╝")
    print("")

    # Notificación persistente
    subprocess.Popen(
        ["termux-notification", "--title", "🤖 Lola AI",
         "--content", "Hable, Lola escucha siempre",
         "--ongoing", "--id", "lola_active"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    # Saludo inicial
    saludo = "Buenas, Ingeniero. Lola lista. Solo hable."
    print(f"🤖 {saludo}")
    hablar(saludo)

    while True:
        try:
            # ── ESCUCHAR ──
            print("🎤 ...", end="", flush=True)
            texto = escuchar()

            if not texto or len(texto) < 2:
                print("\r          \r", end="", flush=True)
                continue

            print(f"\r🗣️  Usted: {texto}")

            # ── ACCIÓN RÁPIDA ──
            accion = ejecutar_accion(texto)
            if accion:
                print(f"🤖 Lola: {accion}")
                hablar(accion)
                continue

            # ── PENSAR (Gemma 4) ──
            respuesta = pensar(texto)
            print(f"🤖 Lola: {respuesta}")

            # ── HABLAR ──
            hablar(respuesta)

        except KeyboardInterrupt:
            print("\n\n👋 Hasta luego, Ingeniero. Lola se apaga.")
            hablar("Hasta luego, Ingeniero.")
            break
        except Exception as e:
            print(f"⚠️  {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
