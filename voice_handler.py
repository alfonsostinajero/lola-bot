"""
voice_handler.py — Manejo de entrada/salida de voz para Lola
STT: termux-speech-to-text (Android nativo, gratuito, sin instalar nada)
TTS: termux-tts-speak con manejo robusto de errores
"""

import logging
import subprocess
import threading
from typing import Optional

import config

logger = logging.getLogger("Lola.Voice")


class VoiceHandler:
    """Maneja reconocimiento de voz (STT) y síntesis de voz (TTS)."""

    def __init__(self):
        self._tts_working = None  # None = no probado aún
        logger.info("VoiceHandler listo.")

    # ── STT (Speech-to-Text) ─────────────────────────────────

    def listen_command(self, timeout: int = 0) -> str:
        """
        Escucha un comando de voz después del wake word.
        Usa termux-speech-to-text (reconocimiento nativo de Android).
        """
        if timeout == 0:
            timeout = config.LISTEN_TIMEOUT_SEC

        if not config.IS_TERMUX:
            try:
                return input("🎤 Comando: ")
            except EOFError:
                return ""

        logger.info("Escuchando comando...")
        try:
            result = subprocess.run(
                ["termux-speech-to-text"],
                capture_output=True,
                text=True,
                timeout=timeout + 5,
            )

            if result.returncode == 0 and result.stdout.strip():
                text = result.stdout.strip()
                logger.info(f"Comando transcrito: '{text}'")
                return text
            else:
                logger.warning("No se detectó voz.")
                return ""

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout de escucha ({timeout}s).")
            return ""
        except Exception as e:
            logger.error(f"Error en listen_command: {e}")
            return ""

    # ── TTS (Text-to-Speech) ─────────────────────────────────

    def speak(self, text: str) -> None:
        """Sintetiza y reproduce voz usando termux-tts-speak."""
        if not text:
            return

        logger.info(f"Hablando: '{text[:80]}...'" if len(text) > 80 else f"Hablando: '{text}'")

        if not config.IS_TERMUX:
            logger.info(f"[TTS simulado]: {text}")
            return

        self._speak_termux(text)

    def _speak_termux(self, text: str) -> None:
        """Usa termux-tts-speak con manejo robusto."""
        try:
            # Cortar texto largo para evitar timeout
            if len(text) > 200:
                text = text[:200]

            # Ejecutar en background para no bloquear
            proc = subprocess.Popen(
                ["termux-tts-speak", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Esperar máximo 15 segundos
            try:
                proc.wait(timeout=15)
                self._tts_working = True
            except subprocess.TimeoutExpired:
                proc.kill()
                logger.warning("TTS timeout - matando proceso")
                self._tts_working = False

        except FileNotFoundError:
            logger.error("termux-tts-speak no disponible. Instala Termux:API.")
            self._tts_working = False
        except Exception as e:
            logger.error(f"Error en TTS: {e}")
            self._tts_working = False

    def speak_async(self, text: str) -> None:
        """Habla en un hilo aparte (no bloquea el flujo principal)."""
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()

    def play_chime(self) -> None:
        """Reproduce un sonido de activación cuando se detecta el wake word."""
        try:
            if config.IS_TERMUX:
                # Vibrar + notificación como chime
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
            else:
                logger.info("🔔 *chime* (simulado)")
        except Exception as e:
            logger.debug(f"No se pudo reproducir chime: {e}")

    # ── Limpieza ─────────────────────────────────────────────

    def cleanup(self) -> None:
        """Libera recursos."""
        logger.info("VoiceHandler recursos liberados.")

    def __del__(self):
        self.cleanup()
