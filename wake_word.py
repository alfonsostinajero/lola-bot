"""
wake_word.py — Detección de palabra de activación para Lola
Usa Porcupine (si hay API key) o Vosk como fallback gratuito.
Optimizado para consumo mínimo de CPU en escucha continua.
"""

import json
import struct
import logging
import time
from typing import Optional

import pyaudio

import config

logger = logging.getLogger("Lola.WakeWord")


class WakeWordDetector:
    """Detecta la palabra de activación 'Lola' usando Porcupine o Vosk."""

    def __init__(self):
        self._pa: Optional[pyaudio.PyAudio] = None
        self._porcupine = None
        self._vosk_model = None
        self._vosk_rec = None
        self._use_porcupine = False
        self._init_audio()
        self._init_detector()

    # ── Inicialización ───────────────────────────────────────

    def _init_audio(self) -> None:
        """Inicializa PyAudio."""
        self._pa = pyaudio.PyAudio()
        logger.info("PyAudio inicializado.")

    def _init_detector(self) -> None:
        """Intenta Porcupine; si falla, usa Vosk."""
        if config.PORCUPINE_ACCESS_KEY:
            try:
                import pvporcupine
                self._porcupine = pvporcupine.create(
                    access_key=config.PORCUPINE_ACCESS_KEY,
                    keywords=["picovoice"],  # Reemplazar con .ppn custom de 'Lola'
                )
                self._use_porcupine = True
                logger.info("Porcupine inicializado correctamente.")
                return
            except Exception as e:
                logger.warning(f"Porcupine no disponible: {e}")

        # Fallback: Vosk (100% gratuito)
        self._init_vosk()

    def _init_vosk(self) -> None:
        """Inicializa Vosk para detección de wake word por transcripción."""
        try:
            from vosk import Model, KaldiRecognizer
            self._vosk_model = Model(config.VOSK_MODEL_PATH)
            self._vosk_rec = KaldiRecognizer(self._vosk_model, config.AUDIO_RATE)
            self._vosk_rec.SetWords(True)
            logger.info("Vosk inicializado como detector de wake word.")
        except Exception as e:
            logger.error(f"Error inicializando Vosk: {e}")
            raise RuntimeError(
                "No se pudo inicializar ningún detector de wake word. "
                "Instala vosk y descarga el modelo español."
            )

    # ── Escucha ──────────────────────────────────────────────

    def listen_for_wake_word(self) -> bool:
        """
        Bloquea hasta detectar la palabra 'Lola'.
        Retorna True cuando se detecta.
        """
        rate = (
            self._porcupine.sample_rate
            if self._use_porcupine
            else config.AUDIO_RATE
        )
        frame_len = (
            self._porcupine.frame_length
            if self._use_porcupine
            else config.AUDIO_CHUNK
        )

        stream = self._pa.open(
            rate=rate,
            channels=config.AUDIO_CHANNELS,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=frame_len,
        )

        logger.info(f"Escuchando wake word '{config.WAKE_WORD}'...")
        try:
            while True:
                pcm = stream.read(frame_len, exception_on_overflow=False)

                if self._use_porcupine:
                    unpacked = struct.unpack_from(
                        "h" * self._porcupine.frame_length, pcm
                    )
                    if self._porcupine.process(unpacked) >= 0:
                        logger.info("¡Wake word detectada! (Porcupine)")
                        return True
                else:
                    if self._vosk_rec.AcceptWaveform(pcm):
                        result = json.loads(self._vosk_rec.Result())
                        text = result.get("text", "").lower()
                        if config.WAKE_WORD in text:
                            logger.info(f"¡Wake word detectada! (Vosk) → '{text}'")
                            return True
                    else:
                        # Revisar resultados parciales para menor latencia
                        partial = json.loads(self._vosk_rec.PartialResult())
                        partial_text = partial.get("partial", "").lower()
                        if config.WAKE_WORD in partial_text:
                            logger.info(f"¡Wake word detectada! (Vosk parcial) → '{partial_text}'")
                            self._vosk_rec.Reset()
                            return True
        except KeyboardInterrupt:
            logger.info("Escucha interrumpida por el usuario.")
            return False
        except Exception as e:
            logger.error(f"Error en escucha de wake word: {e}")
            time.sleep(1)
            return False
        finally:
            stream.stop_stream()
            stream.close()

    # ── Limpieza ─────────────────────────────────────────────

    def cleanup(self) -> None:
        """Libera recursos de audio y detector."""
        if self._porcupine is not None:
            self._porcupine.delete()
            self._porcupine = None
        if self._pa is not None:
            self._pa.terminate()
            self._pa = None
        logger.info("Recursos de WakeWordDetector liberados.")

    def __del__(self):
        self.cleanup()
