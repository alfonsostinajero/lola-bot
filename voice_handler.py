"""
voice_handler.py — Manejo de voz para Lola
STT: termux-speech-to-text (Android nativo)
TTS: termux-tts-speak (voz del sistema)
Diseñado para que NUNCA se trabe.
"""

import logging
import subprocess
import threading

import config

logger = logging.getLogger("Lola.Voice")


class VoiceHandler:
    """Maneja voz de entrada y salida."""

    def __init__(self):
        logger.info("✅ VoiceHandler listo")

    def listen_command(self, timeout: int = 0) -> str:
        """Escucha comando de voz después del wake word."""
        if timeout == 0:
            timeout = config.LISTEN_TIMEOUT_SEC

        if not config.IS_TERMUX:
            try:
                return input("🎤 Comando: ")
            except EOFError:
                return ""

        logger.info("🎤 Escuchando comando...")
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

            logger.warning("No se detectó comando.")
            return ""

        except subprocess.TimeoutExpired:
            logger.warning("Timeout escuchando comando.")
            return ""
        except Exception as e:
            logger.error(f"Error STT: {e}")
            return ""

    def speak(self, text: str) -> None:
        """Habla usando termux-tts-speak. NO se traba."""
        if not text:
            return

        log_text = f"'{text[:80]}...'" if len(text) > 80 else f"'{text}'"
        logger.info(f"Hablando: {log_text}")

        if not config.IS_TERMUX:
            logger.info(f"[TTS]: {text}")
            return

        try:
            # Cortar texto largo para evitar problemas
            if len(text) > 250:
                text = text[:250]

            # Usar Popen para NO bloquear
            proc = subprocess.Popen(
                ["termux-tts-speak", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Esperar máximo 15 seg
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
                logger.warning("TTS cortado por timeout")

        except Exception as e:
            logger.error(f"Error TTS: {e}")

    def speak_async(self, text: str) -> None:
        """Habla sin bloquear el programa."""
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()

    def play_chime(self) -> None:
        """Vibra cuando detecta wake word."""
        if config.IS_TERMUX:
            try:
                subprocess.Popen(
                    ["termux-vibrate", "-d", "300"],
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
        logger.info("VoiceHandler liberado.")

    def __del__(self):
        self.cleanup()
