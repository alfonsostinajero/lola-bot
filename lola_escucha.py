#!/usr/bin/env python3
"""
lola_escucha.py — Micrófono SIEMPRE ACTIVO como Alexa.
1. Graba audio continuamente con termux-microphone-record
2. Python analiza si hay voz (energía del audio)
3. Solo cuando hay voz → Google Speech transcribe
4. Si dice "Lola" → Gemma 4 procesa → responde por voz
"""

import subprocess
import os
import sys
import time
import struct
import math
import json

HOME = os.path.expanduser("~")
AUDIO_DIR = f"{HOME}/.lola/data/audio"
RAW_FILE = f"{AUDIO_DIR}/raw.m4a"
WAV_FILE = f"{AUDIO_DIR}/chunk.wav"
WAKE_WORD = "lola"
SILENCE_THRESHOLD = 500  # Ajustar si es muy sensible o poco sensible
GEMMA_URL = "http://127.0.0.1:8080/v1/chat/completions"

os.makedirs(AUDIO_DIR, exist_ok=True)


def grabar_audio():
    """Graba 3 segundos con el micrófono real del teléfono."""
    # Borrar archivos anteriores
    for f in [RAW_FILE, WAV_FILE]:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass

    # Grabar
    subprocess.run(
        ["termux-microphone-record", "-f", RAW_FILE, "-l", "3"],
        capture_output=True, timeout=5
    )
    time.sleep(3.3)
    subprocess.run(
        ["termux-microphone-record", "-q"],
        capture_output=True, timeout=3
    )
    time.sleep(0.2)


def convertir_a_wav():
    """Convierte m4a a WAV con ffmpeg."""
    if not os.path.exists(RAW_FILE) or os.path.getsize(RAW_FILE) < 100:
        return False
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", RAW_FILE, "-ar", "16000", "-ac", "1",
         "-acodec", "pcm_s16le", WAV_FILE],
        capture_output=True, timeout=10
    )
    return os.path.exists(WAV_FILE) and os.path.getsize(WAV_FILE) > 100


def hay_voz():
    """Analiza el WAV para detectar si hay voz (energía del audio)."""
    try:
        with open(WAV_FILE, "rb") as f:
            # Saltar header WAV (44 bytes)
            header = f.read(44)
            data = f.read()

        if len(data) < 100:
            return False

        # Calcular RMS (energía del audio)
        count = len(data) // 2
        shorts = struct.unpack(f"<{count}h", data[:count * 2])

        sum_squares = sum(s * s for s in shorts)
        rms = math.sqrt(sum_squares / count)

        return rms > SILENCE_THRESHOLD

    except Exception:
        return False


def escuchar_comando():
    """Usa Google Speech para transcribir lo que dice el usuario."""
    try:
        result = subprocess.run(
            ["termux-speech-to-text"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    return ""


def procesar_con_gemma(comando):
    """Envía el comando a Gemma 4 y obtiene respuesta."""
    try:
        import requests
        payload = {"messages": [{"role": "user", "content": comando}]}
        r = requests.post(GEMMA_URL, json=payload, timeout=30)
        data = r.json()
        contenido = data["choices"][0]["message"]["content"]

        # Intentar parsear JSON de Lola
        try:
            j = json.loads(contenido)
            return j.get("respuesta_usuario", contenido)[:300]
        except json.JSONDecodeError:
            return contenido[:300]

    except Exception as e:
        return f"Disculpe Ingeniero, hubo un error: {e}"


def hablar(texto):
    """Habla usando termux-tts-speak (no bloquea)."""
    if texto:
        subprocess.Popen(
            ["termux-tts-speak", texto[:300]],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def main():
    print("")
    print("╔══════════════════════════════════════╗")
    print("║  🤖 LOLA AI ACTIVA                  ║")
    print("║  🎤 Micrófono SIEMPRE activo         ║")
    print("║  Solo hable — Lola escucha           ║")
    print("╚══════════════════════════════════════╝")
    print("")

    subprocess.Popen(
        ["termux-notification", "--title", "Lola AI Activa",
         "--content", "Micrófono activo. Diga Lola.",
         "--ongoing", "--id", "lola_active"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    ciclo = 0
    while True:
        try:
            ciclo += 1

            # 1. Grabar 3 segundos
            grabar_audio()

            # 2. Convertir a WAV
            if not convertir_a_wav():
                continue

            # 3. ¿Hay voz?
            if not hay_voz():
                # Silencio — seguir escuchando (sin mostrar nada)
                continue

            # 4. ¡Hay voz! Transcribir con Google
            print("🎤 Voz detectada, escuchando...")
            texto = escuchar_comando()

            if not texto:
                continue

            print(f"🎧 Escuché: '{texto}'")

            # 5. ¿Dijo "Lola"?
            if WAKE_WORD in texto.lower():
                print("🎯 ¡LOLA ACTIVADA!")
                subprocess.Popen(
                    ["termux-vibrate", "-d", "300"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )

                # Sacar comando quitando "lola"
                import re
                comando = re.sub(r'(?i)lola\s*', '', texto).strip()

                # Si solo dijo "lola", preguntar qué necesita
                if len(comando) < 3:
                    hablar("Dígame, Ingeniero")
                    print("🎤 Escuchando comando...")
                    comando = escuchar_comando()

                if comando and len(comando) > 2:
                    print(f"📝 Comando: '{comando}'")
                    print("🧠 Procesando...")

                    respuesta = procesar_con_gemma(comando)
                    print(f"🤖 Lola: {respuesta}")
                    print("")
                    hablar(respuesta)

        except KeyboardInterrupt:
            print("\n👋 Lola apagada. ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
