"""
wake_word.py — Detección de palabra de activación para Lola
Usa termux-speech-to-text (Android nativo) para escuchar continuamente.
Optimizado para Termux en Motorola Edge 20.
"""

import json
import logging
import subprocess
import time
from typing import Optional

import config

logger = logging.getLogger("Lola.WakeWord")


class WakeWordDetector:
    """Detecta la palabra de activación 'Lola' usando el reconocimiento de voz de Android."""

    def __init__(self):
        self._running = True
        logger.info(f"WakeWordDetector inicializado. Palabra clave: '{config.WAKE_WORD}'")

    def listen_for_wake_word(self) -> bool:
        """
        Escucha continuamente hasta detectar la palabra 'Lola'.
        Usa termux-speech-to-text (reconocimiento nativo de Android).
        Retorna True cuando se detecta.
        """
        logger.info(f"Escuchando wake word '{config.WAKE_WORD}'...")

        while self._running:
            try:
                if config.IS_TERMUX:
                    # Usar reconocimiento de voz nativo de Android
                    result = subprocess.run(
                        ["termux-speech-to-text"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if result.returncode == 0 and result.stdout.strip():
                        text = result.stdout.strip().lower()
                        logger.debug(f"Escuchado: '{text}'")

                        if config.WAKE_WORD in text:
                            logger.info(f"¡Wake word detectada! → '{text}'")
                            # Retornar el texto sin la wake word para procesarlo
                            return True
                else:
                    # Modo desarrollo (no-Termux): simular con input
                    text = input("🎤 [Simular voz] Escribe algo: ").lower()
                    if config.WAKE_WORD in text:
                        return True

            except subprocess.TimeoutExpired:
                # Timeout normal — simplemente volver a escuchar
                continue
            except KeyboardInterrupt:
                logger.info("Escucha interrumpida por el usuario.")
                return False
            except Exception as e:
                logger.error(f"Error en escucha: {e}")
                time.sleep(2)  # Evitar loop rápido en errores

        return False

    def listen_and_get_text(self) -> Optional[str]:
        """
        Escucha y retorna el texto completo si contiene la wake word.
        Útil para obtener el comando junto con la wake word.
        Ej: "Lola abre YouTube" → retorna "abre YouTube"
        """
        if not config.IS_TERMUX:
            text = input("🎤 [Simular voz] Escribe algo: ")
            if config.WAKE_WORD in text.lower():
                # Quitar la wake word del texto
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
                    logger.info(f"Wake word + comando: '{command}'")
                    return command

        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            logger.error(f"Error en listen_and_get_text: {e}")

        return None

    def cleanup(self) -> None:
        """Detiene la escucha."""
        self._running = False
        logger.info("WakeWordDetector detenido.")

    def __del__(self):
        self.cleanup()
