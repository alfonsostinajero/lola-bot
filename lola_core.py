"""
lola_core.py — Orquestador principal de Lola AI Assistant
Coordina todos los módulos: wake word, voz, IA, acciones, aprendizaje.

Uso:
    python lola_core.py                    # Modo completo (voz)
    python lola_core.py --mode text-only   # Modo texto (para testing)
    python lola_core.py --verbose          # Con logs detallados
    python lola_core.py --no-self-modify   # Sin auto-modificación
"""

import argparse
import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional

import config
from utils import setup_logging, format_datetime_spanish

logger = logging.getLogger("Lola")

# ── ASCII Art Banner ─────────────────────────────────────────
BANNER = """
╔══════════════════════════════════════════════╗
║                                              ║
║     ██╗      ██████╗ ██╗      █████╗         ║
║     ██║     ██╔═══██╗██║     ██╔══██╗        ║
║     ██║     ██║   ██║██║     ███████║        ║
║     ██║     ██║   ██║██║     ██╔══██║        ║
║     ███████╗╚██████╔╝███████╗██║  ██║        ║
║     ╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝        ║
║                                              ║
║   Asistente IA Local — v{version}              ║
║   Motorola Edge 20 · Snapdragon 778G         ║
║                                              ║
╚══════════════════════════════════════════════╝
"""


class LolaAssistant:
    """
    Orquestador principal que coordina todos los módulos de Lola.

    Flujo principal:
    1. Escuchar wake word "Lola"
    2. Capturar comando de voz
    3. Procesar con Gemma 4 (enriquecido con contexto aprendido)
    4. Ejecutar acción correspondiente
    5. Responder por voz
    6. Registrar interacción para aprendizaje
    """

    def __init__(
        self,
        mode: str = "full",
        verbose: bool = False,
        self_modify: bool = True,
    ):
        self.mode = mode
        self.is_running = False
        self._self_modify = self_modify

        # Configurar logging
        level = logging.DEBUG if verbose else logging.INFO
        setup_logging("Lola", level)

        # Inicializar módulos
        logger.info("Inicializando módulos de Lola...")
        self._init_modules()
        logger.info("Todos los módulos inicializados. ✓")

    def _init_modules(self) -> None:
        """Inicializa todos los sub-módulos."""
        # Self Learner (siempre activo)
        from self_learner import SelfLearner
        self.learner = SelfLearner()
        logger.info("  ✓ Self Learner")

        # AI Engine (con contexto del learner)
        from ai_engine import AIEngine
        dynamic_prompt = self.learner.build_dynamic_prompt_additions()
        self.ai = AIEngine(extra_system_context=dynamic_prompt)
        logger.info("  ✓ AI Engine (Gemma 4)")

        # Action Executor
        from action_executor import ActionExecutor
        self.executor = ActionExecutor()
        logger.info("  ✓ Action Executor")

        # Módulos de voz (solo si no es modo texto)
        self.wake_word = None
        self.voice = None
        if self.mode != "text-only":
            try:
                from wake_word import WakeWordDetector
                self.wake_word = WakeWordDetector()
                logger.info("  ✓ Wake Word Detector")
            except Exception as e:
                logger.warning(f"  ✗ Wake Word no disponible: {e}")

            try:
                from voice_handler import VoiceHandler
                self.voice = VoiceHandler()
                logger.info("  ✓ Voice Handler (Piper TTS)")
            except Exception as e:
                logger.warning(f"  ✗ Voice Handler no disponible: {e}")

        # Self Modifier (opcional)
        self.modifier = None
        if self._self_modify:
            from self_modifier import SelfModifier
            self.modifier = SelfModifier()
            logger.info("  ✓ Self Modifier")

    # ── Bucle principal ──────────────────────────────────────

    async def run(self) -> None:
        """Bucle principal asíncrono de Lola."""
        self.is_running = True
        self._print_banner()
        self._greet()

        # Tarea de auto-mejora periódica
        improve_task = None
        if self._self_modify:
            improve_task = asyncio.create_task(self._periodic_self_improve())

        try:
            while self.is_running:
                if self.mode == "text-only":
                    await self._text_loop()
                else:
                    await self._voice_loop()
        except KeyboardInterrupt:
            logger.info("Interrupción por teclado.")
        except Exception as e:
            logger.error(f"Error en bucle principal: {e}", exc_info=True)
        finally:
            if improve_task:
                improve_task.cancel()
            self.shutdown()

    async def _voice_loop(self) -> None:
        """Un ciclo del bucle de voz."""
        if not self.wake_word:
            logger.error("Wake word no disponible. Cambiando a modo texto.")
            self.mode = "text-only"
            return

        # Esperar wake word
        loop = asyncio.get_event_loop()
        detected = await loop.run_in_executor(None, self.wake_word.listen_for_wake_word)

        if not detected:
            return

        # ¡Wake word detectada!
        logger.info("═" * 40)
        logger.info("🎤 Wake word detectada. Escuchando comando...")

        if self.voice:
            self.voice.play_chime()

        # Capturar comando
        command = ""
        if self.voice:
            command = await loop.run_in_executor(None, self.voice.listen_command)

        if not command:
            if self.voice:
                self.voice.speak_async("No te escuché. ¿Puedes repetir?")
            return

        # Procesar
        response = await self.process_command(command)

        # Responder por voz
        if self.voice and response:
            self.voice.speak(response)

    async def _text_loop(self) -> None:
        """Un ciclo del bucle de texto (para testing)."""
        loop = asyncio.get_event_loop()
        try:
            user_input = await loop.run_in_executor(None, input, "\n🟢 Tú: ")
        except EOFError:
            self.is_running = False
            return

        if not user_input:
            return

        if user_input.lower() in ("salir", "exit", "quit", "bye", "adiós"):
            print("\n🔴 Lola: ¡Hasta luego! Que te vaya bien. 👋")
            self.is_running = False
            return

        if user_input.lower() == "status":
            self._print_status()
            return

        response = await self.process_command(user_input)
        print(f"\n🤖 Lola: {response}")

    # ── Procesamiento de comandos ────────────────────────────

    async def process_command(self, text: str) -> str:
        """
        Pipeline completo de procesamiento de un comando.

        1. Obtener contexto del Self Learner
        2. Procesar con AI Engine
        3. Ejecutar acciones
        4. Registrar resultado
        5. Retornar respuesta
        """
        start = time.time()

        try:
            # 1. Contexto enriquecido
            context = self.learner.get_context_enrichment(text)

            # 2. Procesar con IA
            ai_response = self.ai.process(text, context)
            logger.info(f"AI Response: {json.dumps(ai_response, ensure_ascii=False)[:200]}")

            # 3. Ejecutar acciones
            exec_result = self.executor.execute(ai_response)
            success = exec_result.get("success", False)
            respuesta = (
                exec_result.get("respuesta", "")
                or ai_response.get("respuesta_usuario", "")
            )

            # 4. Registrar interacción
            exec_time = int((time.time() - start) * 1000)
            action_type = ""
            if ai_response.get("acciones"):
                action_type = ai_response["acciones"][0].get("tipo", "")

            self.learner.log_interaction(
                user_input=text,
                ai_response=json.dumps(ai_response, ensure_ascii=False)[:500],
                action_taken=action_type,
                success=success,
                execution_time_ms=exec_time,
            )

            logger.info(f"Comando procesado en {exec_time}ms ({'✓' if success else '✗'})")
            return respuesta or "Listo."

        except Exception as e:
            logger.error(f"Error procesando comando: {e}", exc_info=True)
            self.learner.log_interaction(
                user_input=text,
                ai_response=str(e),
                action_taken="ERROR",
                success=False,
                feedback=str(e),
            )
            return f"Perdón, tuve un error: {str(e)[:100]}"

    # ── Auto-mejora periódica ────────────────────────────────

    async def _periodic_self_improve(self) -> None:
        """Ejecuta análisis de auto-mejora cada N horas."""
        interval = config.SELF_IMPROVE_INTERVAL_HOURS * 3600
        while self.is_running:
            await asyncio.sleep(interval)
            try:
                logger.info("🔄 Iniciando ciclo de auto-mejora...")

                suggestions = self.learner.suggest_improvements()
                for s in suggestions:
                    logger.info(f"  💡 Sugerencia: {s}")

                new_context = self.learner.build_dynamic_prompt_additions()
                self.ai.update_context(new_context)
                logger.info("  ✓ Contexto del AI actualizado con aprendizaje.")

                deleted = self.learner.periodic_cleanup()
                if deleted:
                    logger.info(f"  🗑️ {deleted} registros antiguos limpiados.")

                logger.info("🔄 Ciclo de auto-mejora completado.")
            except Exception as e:
                logger.error(f"Error en auto-mejora: {e}")

    # ── UI y utilidades ──────────────────────────────────────

    def _print_banner(self) -> None:
        """Imprime el banner de inicio."""
        print(BANNER.format(version=config.VERSION))

    def _greet(self) -> None:
        """Saludo de inicio."""
        now = format_datetime_spanish()
        greeting = f"¡Hola! Soy Lola, tu asistente. {now}. ¿En qué te ayudo?"

        if self.mode == "text-only":
            print(f"\n🤖 Lola: {greeting}")
            print("   (Escribe 'salir' para terminar, 'status' para ver estado)\n")
        elif self.voice:
            self.voice.speak_async(greeting)

    def _print_status(self) -> None:
        """Muestra el estado del sistema."""
        status = self.status()
        print("\n" + "═" * 45)
        print("  📊 ESTADO DE LOLA")
        print("═" * 45)
        for key, value in status.items():
            print(f"  {key}: {value}")
        print("═" * 45 + "\n")

    def status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sistema."""
        return {
            "🏷️ Versión": config.VERSION,
            "🎯 Modo": self.mode,
            "🔄 Auto-modificación": "Activa" if self._self_modify else "Desactivada",
            "🎤 Wake Word": "Listo" if self.wake_word else "No disponible",
            "🔊 Voz (TTS)": "Piper" if config.USE_PIPER_TTS else "termux-tts-speak",
            "📊 Tasa de éxito": f"{self.learner.get_success_rate():.0%}",
            "🧠 Modelo": config.MODEL_NAME,
            "📡 LLM Server": config.LLAMA_CPP_URL,
        }

    def shutdown(self) -> None:
        """Apagado limpio de todos los módulos."""
        logger.info("Apagando Lola...")
        self.is_running = False

        if self.wake_word:
            self.wake_word.cleanup()
        if self.voice:
            self.voice.cleanup()
        if self.learner:
            self.learner.close()

        logger.info("Lola apagada. ¡Hasta pronto! 👋")


# ── Punto de entrada ─────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Lola AI Assistant — Asistente de IA local",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Ejemplos:\n"
               "  python lola_core.py                    # Modo completo\n"
               "  python lola_core.py --mode text-only   # Testing por texto\n"
               "  python lola_core.py --verbose           # Logs detallados\n",
    )
    parser.add_argument(
        "--mode",
        choices=["full", "voice-only", "text-only"],
        default="full",
        help="Modo de ejecución (default: full)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Activar logs de depuración",
    )
    parser.add_argument(
        "--no-self-modify",
        action="store_true",
        help="Desactivar auto-modificación de código",
    )

    args = parser.parse_args()

    lola = LolaAssistant(
        mode=args.mode,
        verbose=args.verbose,
        self_modify=not args.no_self_modify,
    )

    # Signal handlers
    def signal_handler(sig, frame):
        lola.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)

    # Ejecutar
    try:
        asyncio.run(lola.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
