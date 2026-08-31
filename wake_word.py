"""
wake_word.py — Detección continua de "Lola" con micrófono siempre activo.
Usa Vosk para reconocimiento offline en tiempo real.
El micrófono NUNCA se apaga — siempre escuchando.
"""

import json
import logging
import os
import queue
import subprocess
import sys
import time
import threading
from typing import Optional

import config

logger = logging.getLogger("Lola.WakeWord")


class WakeWordDetector:
    """Detecta 'Lola' con micrófono siempre activo usando Vosk."""

    def __init__(self):
        self._running = True
        self._audio_queue = queue.Queue()
        self._vosk_available = False
        self._recorder_process = None

        # Intentar inicializar Vosk
        try:
            import vosk
            model_path = config.VOSK_MODEL_PATH
            if os.path.exists(model_path):
                vosk.SetLogLevel(-1)  # Silenciar logs de vosk
                self._model = vosk.Model(model_path)
                self._vosk_available = True
                logger.info(f"✅ Vosk inicializado (modelo: {model_path})")
            else:
                logger.warning(f"Modelo Vosk no encontrado en {model_path}")
        except ImportError:
            logger.warning("Vosk no instalado. pip install vosk")
        except Exception as e:
            logger.warning(f"Error inicializando Vosk: {e}")

        if not self._vosk_available:
            logger.info("Usando termux-speech-to-text como fallback (más lento)")

        logger.info(f"WakeWordDetector listo. Palabra: '{config.WAKE_WORD}'")

    def listen_for_wake_word(self) -> bool:
        """Escucha continuamente hasta detectar 'Lola'."""
        if self._vosk_available and config.IS_TERMUX:
            return self._listen_vosk_continuous()
        elif config.IS_TERMUX:
            return self._listen_termux_fallback()
        else:
            return self._listen_dev_mode()

    def _listen_vosk_continuous(self) -> bool:
        """Escucha continua con Vosk + termux-microphone-record."""
        import vosk

        logger.info("🎤 Micrófono ACTIVO — escuchando 'Lola'...")

        rec = vosk.KaldiRecognizer(self._model, 16000)

        while self._running:
            try:
                # Grabar audio en chunks con termux-microphone-record
                proc = subprocess.Popen(
                    ["termux-microphone-record", "-f", "/dev/fd/1",
                     "-r", "16000", "-c", "1", "-e", "s16le", "-l", "3"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )

                # Leer audio en chunks
                start_time = time.time()
                while self._running and (time.time() - start_time) < 3.5:
                    data = proc.stdout.read(4000)
                    if not data:
                        break

                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get("text", "").lower()
                        if text:
                            logger.debug(f"Escuchado: '{text}'")
                        if config.WAKE_WORD in text:
                            proc.kill()
                            logger.info(f"🎯 ¡Wake word detectada! → '{text}'")
                            return True
                    else:
                        partial = json.loads(rec.PartialResult())
                        partial_text = partial.get("partial", "").lower()
                        if config.WAKE_WORD in partial_text:
                            proc.kill()
                            logger.info(f"🎯 ¡Wake word detectada (parcial)! → '{partial_text}'")
                            return True

                # Limpiar
                proc.kill()
                proc.wait()

            except KeyboardInterrupt:
                return False
            except Exception as e:
                logger.error(f"Error en escucha Vosk: {e}")
                time.sleep(1)

        return False

    def _listen_termux_fallback(self) -> bool:
        """Fallback con termux-speech-to-text (más lento, abre diálogo)."""
        logger.info(f"Escuchando wake word '{config.WAKE_WORD}' (modo fallback)...")

        while self._running:
            try:
                result = subprocess.run(
                    ["termux-speech-to-text"],
                    capture_output=True,
                    text=True,
                    timeout=8,
                )

                if result.returncode == 0 and result.stdout.strip():
                    text = result.stdout.strip().lower()
                    logger.debug(f"Escuchado: '{text}'")

                    if config.WAKE_WORD in text:
                        logger.info(f"🎯 ¡Wake word detectada! → '{text}'")
                        return True

            except subprocess.TimeoutExpired:
                continue
            except KeyboardInterrupt:
                return False
            except Exception as e:
                logger.error(f"Error en escucha: {e}")
                time.sleep(2)

        return False

    def _listen_dev_mode(self) -> bool:
        """Modo desarrollo: input de texto."""
        text = input("🎤 [Simular voz] Escribe algo: ").lower()
        if config.WAKE_WORD in text:
            return True
        return False

    def listen_and_get_text(self) -> Optional[str]:
        """Escucha y retorna el comando si viene junto con la wake word."""
        if not config.IS_TERMUX:
            text = input("🎤 Escribe: ")
            if config.WAKE_WORD in text.lower():
                parts = text.lower().split(config.WAKE_WORD, 1)
                return parts[1].strip() if len(parts) > 1 else ""
            return None

        try:
            result = subprocess.run(
                ["termux-speech-to-text"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                text = result.stdout.strip()
                if config.WAKE_WORD in text.lower():
                    parts = text.lower().split(config.WAKE_WORD, 1)
                    command = parts[1].strip() if len(parts) > 1 else ""
                    return command

        except Exception:
            pass

        return None

    def cleanup(self) -> None:
        """Detiene la escucha."""
        self._running = False
        if self._recorder_process:
            try:
                self._recorder_process.kill()
            except Exception:
                pass
        logger.info("WakeWordDetector detenido.")

    def __del__(self):
        self.cleanup()
