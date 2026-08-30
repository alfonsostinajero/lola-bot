"""
voice_handler.py — Manejo de entrada/salida de voz para Lola
STT: Vosk (offline, gratuito)
TTS: Piper TTS (voz natural, gratuita) con fallback a termux-tts-speak
"""

import json
import math
import struct
import logging
import subprocess
import tempfile
import threading
import time
from typing import Optional

import pyaudio

import config

logger = logging.getLogger("Lola.Voice")


class VoiceHandler:
    """Maneja reconocimiento de voz (STT) y síntesis de voz (TTS)."""

    def __init__(self):
        self._pa = pyaudio.PyAudio()
        self._vosk_model = None
        self._recognizer = None
        self._init_stt()
        logger.info(
            f"VoiceHandler listo. TTS: {'Piper (natural)' if config.USE_PIPER_TTS else 'termux-tts-speak'}"
        )

    # ── STT (Speech-to-Text) ─────────────────────────────────

    def _init_stt(self) -> None:
        """Inicializa el modelo Vosk para transcripción."""
        try:
            from vosk import Model, KaldiRecognizer
            self._vosk_model = Model(config.VOSK_MODEL_PATH)
            self._recognizer = KaldiRecognizer(self._vosk_model, config.AUDIO_RATE)
            logger.info("Modelo Vosk cargado para STT.")
        except Exception as e:
            logger.error(f"Error cargando Vosk STT: {e}")

    def _rms(self, frame: bytes) -> float:
        """Calcula el nivel RMS del audio para detectar silencio."""
        count = len(frame) // 2
        if count == 0:
            return 0.0
        shorts = struct.unpack(f"{count}h", frame)
        return math.sqrt(sum(s ** 2 for s in shorts) / count)

    def listen_command(self, timeout: int = 0) -> str:
        """
        Escucha un comando de voz después del wake word.
        Retorna el texto transcrito.
        Detecta silencio para saber cuándo el usuario terminó de hablar.
        """
        if timeout == 0:
            timeout = config.LISTEN_TIMEOUT_SEC

        if not self._recognizer:
            logger.error("Vosk no disponible para STT.")
            return ""

        stream = self._pa.open(
            rate=config.AUDIO_RATE,
            channels=config.AUDIO_CHANNELS,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=config.AUDIO_CHUNK,
        )

        logger.info("Escuchando comando...")
        start_time = time.time()
        silence_start: Optional[float] = None
        has_speech = False

        try:
            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    logger.warning(f"Timeout de escucha ({timeout}s).")
                    break

                pcm = stream.read(config.AUDIO_CHUNK, exception_on_overflow=False)
                rms = self._rms(pcm)

                if rms >= config.SILENCE_THRESHOLD:
                    has_speech = True
                    silence_start = None
                elif has_speech:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > config.SILENCE_TIMEOUT_SEC:
                        logger.debug("Silencio detectado, fin del comando.")
                        break

                self._recognizer.AcceptWaveform(pcm)

            result = json.loads(self._recognizer.FinalResult())
            text = result.get("text", "").strip()
            logger.info(f"Comando transcrito: '{text}'")
            return text

        except Exception as e:
            logger.error(f"Error en listen_command: {e}")
            return ""
        finally:
            stream.stop_stream()
            stream.close()

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
            safe_text = text.replace("'", "'\\''")
            subprocess.run(
                [config.TTS_COMMAND, "-l", config.TTS_LANG, safe_text],
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
        """Libera recursos de audio."""
        if self._pa:
            self._pa.terminate()
        logger.info("VoiceHandler recursos liberados.")

    def __del__(self):
        self.cleanup()
