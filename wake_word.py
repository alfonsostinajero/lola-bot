"""
wake_word.py — Detección de "Lola" con micrófono SIEMPRE ACTIVO.
Usa termux-microphone-record para grabar audio continuo.
Detecta la palabra "lola" analizando el audio con reconocimiento de Android.
Funciona como Alexa — siempre escuchando en segundo plano.
"""

import logging
import subprocess
import time
import os
import json
from typing import Optional

import config

logger = logging.getLogger("Lola.WakeWord")


class WakeWordDetector:
    """Detecta 'Lola' con micrófono siempre activo."""

    def __init__(self):
        self._running = True
        self._listen_method = "microphone"  # microphone o speech-to-text

        # Verificar qué método está disponible
        try:
            # Probar termux-microphone-record
            test = subprocess.run(
                ["which", "termux-microphone-record"],
                capture_output=True, text=True, timeout=5
            )
            if test.returncode == 0:
                self._listen_method = "microphone"
                logger.info("✅ Usando termux-microphone-record (micrófono continuo)")
            else:
                self._listen_method = "speech-to-text"
                logger.info("Usando termux-speech-to-text (fallback)")
        except Exception:
            self._listen_method = "speech-to-text"

        logger.info(f"WakeWordDetector listo. Palabra: '{config.WAKE_WORD}'")

    def listen_for_wake_word(self) -> bool:
        """Escucha continuamente hasta detectar 'Lola'."""
        if not config.IS_TERMUX:
            return self._listen_dev_mode()

        logger.info(f"🎤 Micrófono ACTIVO — esperando '{config.WAKE_WORD}'...")

        while self._running:
            try:
                # Grabar 4 segundos de audio
                audio_file = os.path.expanduser("~/.lola/data/wake_audio.wav")

                # Grabar audio silenciosamente
                rec_proc = subprocess.run(
                    ["termux-microphone-record", "-f", audio_file,
                     "-l", "4", "-e", "amr_wb", "-r", "16000"],
                    capture_output=True, timeout=6
                )

                # Esperar a que termine la grabación
                time.sleep(0.3)

                # Detener grabación
                subprocess.run(
                    ["termux-microphone-record", "-q"],
                    capture_output=True, timeout=3
                )

                # Ahora usar speech-to-text para analizar
                # Usamos termux-speech-to-text en modo rápido
                result = subprocess.run(
                    ["termux-speech-to-text"],
                    capture_output=True, text=True, timeout=6
                )

                if result.returncode == 0 and result.stdout.strip():
                    text = result.stdout.strip().lower()
                    logger.debug(f"Escuchado: '{text}'")

                    if config.WAKE_WORD in text:
                        logger.info(f"🎯 ¡LOLA detectada! → '{text}'")
                        # Limpiar archivo temporal
                        try:
                            os.remove(audio_file)
                        except Exception:
                            pass
                        return True

            except subprocess.TimeoutExpired:
                # Normal — volver a escuchar
                subprocess.run(
                    ["termux-microphone-record", "-q"],
                    capture_output=True, timeout=2
                )
                continue
            except KeyboardInterrupt:
                logger.info("Escucha interrumpida.")
                return False
            except Exception as e:
                logger.error(f"Error: {e}")
                subprocess.run(
                    ["termux-microphone-record", "-q"],
                    capture_output=True, timeout=2
                )
                time.sleep(1)

        return False

    def _listen_dev_mode(self) -> bool:
        """Modo desarrollo: input de texto."""
        text = input("🎤 Escribe algo (incluye 'lola'): ").lower()
        return config.WAKE_WORD in text

    def cleanup(self) -> None:
        """Detiene la escucha."""
        self._running = False
        try:
            subprocess.run(
                ["termux-microphone-record", "-q"],
                capture_output=True, timeout=2
            )
        except Exception:
            pass
        logger.info("WakeWordDetector detenido.")

    def __del__(self):
        self.cleanup()
