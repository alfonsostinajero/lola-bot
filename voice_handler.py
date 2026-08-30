"""
voice_handler.py — Manejo de entrada/salida de voz para Lola
STT: termux-speech-to-text (Android nativo, gratuito, sin instalar nada)
TTS: Piper TTS (voz natural) con fallback a termux-tts-speak
"""

import logging
import subprocess
import tempfile
import threading
from typing import Optional

import config

logger = logging.getLogger("Lola.Voice")


class VoiceHandler:
    """Maneja reconocimiento de voz (STT) y síntesis de voz (TTS)."""

    def __init__(self):
        logger.info(
            f"VoiceHandler listo. TTS: {'Piper (natural)' if config.USE_PIPER_TTS else 'termux-tts-speak'}"
        )

    # ── STT (Speech-to-Text) ─────────────────────────────────

    def listen_command(self, timeout: int = 0) -> str:
        """
        Escucha un comando de voz después del wake word.
        Usa termux-speech-to-text (reconocimiento nativo de Android).
        Retorna el texto transcrito.
        """
        if timeout == 0:
            timeout = config.LISTEN_TIMEOUT_SEC

        if not config.IS_TERMUX:
            # Modo desarrollo: input de texto
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
        """
        Sintetiza y reproduce voz.
        Usa Piper TTS (voz natural) o termux-tts-speak como fallback.
        """
        if not text:
            return

        logger.info(f"Hablando: '{text[:80]}...'" if len(text) > 80 else f"Hablando: '{text}'")

        if config.USE_PIPER_TTS:
            self._speak_piper(text)
        else:
            self._speak_termux(text)

    def _speak_piper(self, text: str) -> None:
        """
        Usa Piper TTS para generar voz natural.
        Piper genera un archivo WAV que luego se reproduce.
        """
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav_path = tmp.name

            # Piper lee de stdin y escribe WAV
            cmd = [
                config.PIPER_BINARY,
                "--model", config.PIPER_MODEL,
                "--output_file", wav_path,
            ]
            proc = subprocess.run(
                cmd,
                input=text,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if proc.returncode != 0:
                logger.warning(f"Piper falló: {proc.stderr}. Usando fallback.")
                self._speak_termux(text)
                return

            # Reproducir el WAV generado
            if config.IS_TERMUX:
                subprocess.run(
                    ["play", wav_path],  # sox play
                    capture_output=True,
                    timeout=30,
                )
            elif config.IS_WINDOWS:
                import os
                os.startfile(wav_path)

        except FileNotFoundError:
            logger.warning("Piper no encontrado. Usando fallback termux-tts-speak.")
            self._speak_termux(text)
        except Exception as e:
            logger.error(f"Error en Piper TTS: {e}")
            self._speak_termux(text)

    def _speak_termux(self, text: str) -> None:
        """Fallback: usa termux-tts-speak (voz del sistema Android)."""
        try:
            subprocess.run(
                [config.TTS_COMMAND, "-l", config.TTS_LANG, text],
                timeout=30,
            )
        except FileNotFoundError:
            logger.error(
                "termux-tts-speak no disponible. Instala Termux:API."
            )
        except Exception as e:
            logger.error(f"Error en termux-tts-speak: {e}")

    def speak_async(self, text: str) -> None:
        """Habla en un hilo aparte (no bloquea el flujo principal)."""
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()

    def play_chime(self) -> None:
        """Reproduce un sonido de activación cuando se detecta el wake word."""
        try:
            if config.IS_TERMUX:
                subprocess.run(
                    ["termux-notification", "--sound", "--title", "Lola",
                     "--content", "Te escucho..."],
                    timeout=5,
                )
            else:
                logger.info("🔔 *chime* (simulado en entorno no-Termux)")
        except Exception as e:
            logger.debug(f"No se pudo reproducir chime: {e}")

    # ── Limpieza ─────────────────────────────────────────────

    def cleanup(self) -> None:
        """Libera recursos."""
        logger.info("VoiceHandler recursos liberados.")

    def __del__(self):
        self.cleanup()
