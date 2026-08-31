"""
voice_handler.py — Manejo de voz para Lola
STT: Vosk (offline, continuo, siempre activo) con fallback a termux-speech-to-text
TTS: termux-tts-speak (voz del sistema Android)
"""

import json
import logging
import os
import subprocess
import threading
import time
from typing import Optional

import config

logger = logging.getLogger("Lola.Voice")


class VoiceHandler:
    """Maneja reconocimiento de voz (STT) y síntesis de voz (TTS)."""

    def __init__(self):
        self._vosk_available = False
        self._model = None

        # Intentar cargar Vosk
        try:
            import vosk
            model_path = config.VOSK_MODEL_PATH
            if os.path.exists(model_path):
                vosk.SetLogLevel(-1)
                self._model = vosk.Model(model_path)
                self._vosk_available = True
                logger.info("✅ VoiceHandler con Vosk (escucha continua)")
            else:
                logger.info("VoiceHandler sin Vosk (usando termux-speech-to-text)")
        except ImportError:
            logger.info("VoiceHandler sin Vosk (usando termux-speech-to-text)")

    # ── STT (Speech-to-Text) ─────────────────────────────────

    def listen_command(self, timeout: int = 0) -> str:
        """Escucha un comando de voz después del wake word."""
        if timeout == 0:
            timeout = config.LISTEN_TIMEOUT_SEC

        if not config.IS_TERMUX:
            try:
                return input("🎤 Comando: ")
            except EOFError:
                return ""

        if self._vosk_available:
            return self._listen_vosk(timeout)
        else:
            return self._listen_termux(timeout)

    def _listen_vosk(self, timeout: int) -> str:
        """Escucha comando con Vosk (micrófono siempre activo, sin diálogo)."""
        import vosk

        logger.info("🎤 Escuchando comando con Vosk...")

        rec = vosk.KaldiRecognizer(self._model, 16000)
        full_text = ""

        try:
            proc = subprocess.Popen(
                ["termux-microphone-record", "-f", "/dev/fd/1",
                 "-r", "16000", "-c", "1", "-e", "s16le", "-l", str(timeout)],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )

            silence_start = None
            start_time = time.time()

            while (time.time() - start_time) < timeout + 2:
                data = proc.stdout.read(4000)
                if not data:
                    break

                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").strip()
                    if text:
                        full_text += " " + text
                        silence_start = None
                    else:
                        if full_text and silence_start is None:
                            silence_start = time.time()
                else:
                    partial = json.loads(rec.PartialResult())
                    if partial.get("partial", ""):
                        silence_start = None

                # Si ya hay texto y 2 seg de silencio, terminar
                if full_text and silence_start and (time.time() - silence_start) > 2:
                    break

            proc.kill()
            proc.wait()

            # Obtener resultado final
            final = json.loads(rec.FinalResult())
            final_text = final.get("text", "").strip()
            if final_text:
                full_text += " " + final_text

            full_text = full_text.strip()
            if full_text:
                logger.info(f"Comando: '{full_text}'")
            else:
                logger.warning("No se detectó comando.")

            return full_text

        except Exception as e:
            logger.error(f"Error en Vosk listen: {e}")
            return self._listen_termux(timeout)

    def _listen_termux(self, timeout: int) -> str:
        """Fallback: usa termux-speech-to-text."""
        logger.info("Escuchando comando (termux-speech-to-text)...")
        try:
            result = subprocess.run(
                ["termux-speech-to-text"],
                capture_output=True,
                text=True,
                timeout=timeout + 5,
            )

            if result.returncode == 0 and result.stdout.strip():
                text = result.stdout.strip()
                logger.info(f"Comando: '{text}'")
                return text
            return ""

        except subprocess.TimeoutExpired:
            return ""
        except Exception as e:
            logger.error(f"Error STT: {e}")
            return ""

    # ── TTS (Text-to-Speech) ─────────────────────────────────

    def speak(self, text: str) -> None:
        """Habla usando termux-tts-speak."""
        if not text:
            return

        logger.info(f"Hablando: '{text[:80]}...'" if len(text) > 80 else f"Hablando: '{text}'")

        if not config.IS_TERMUX:
            logger.info(f"[TTS]: {text}")
            return

        try:
            # Cortar texto largo
            if len(text) > 300:
                text = text[:300]

            proc = subprocess.Popen(
                ["termux-tts-speak", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
                logger.warning("TTS timeout")

        except Exception as e:
            logger.error(f"Error TTS: {e}")

    def speak_async(self, text: str) -> None:
        """Habla sin bloquear."""
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()

    def play_chime(self) -> None:
        """Vibra y muestra toast cuando detecta wake word."""
        try:
            if config.IS_TERMUX:
                subprocess.Popen(
                    ["termux-vibrate", "-d", "200"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                subprocess.Popen(
                    ["termux-toast", "🎤 Te escucho, Ingeniero..."],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass

    def cleanup(self) -> None:
        logger.info("VoiceHandler recursos liberados.")

    def __del__(self):
        self.cleanup()
