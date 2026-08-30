"""
ai_engine.py — Motor de IA para Lola (Gemma 4 via llama.cpp)
Procesa comandos del usuario y genera respuestas estructuradas en JSON.
"""

import datetime
import json
import logging
import re
from typing import Any, Dict, List, Optional

import requests

import config

logger = logging.getLogger("Lola.AI")

# ── System Prompt Maestro ────────────────────────────────────
SYSTEM_PROMPT = """Eres Lola, una asistente de inteligencia artificial que corre localmente en un teléfono Android.
Tu personalidad: amigable, eficiente, proactiva. Hablas español mexicano de forma natural.

## REGLAS ABSOLUTAS
1. Cuando el usuario pida una ACCIÓN (abrir app, agendar, enviar mensaje, ejecutar código, etc.), responde ÚNICAMENTE con un bloque JSON.
2. Cuando el usuario haga una PREGUNTA o CONVERSACIÓN casual, responde con JSON tipo RESPONDER.
3. NUNCA mezcles texto libre fuera del JSON.
4. Sé concisa en "respuesta_usuario" — esto se leerá en voz alta.

## FORMATO DE RESPUESTA (SIEMPRE JSON)
```json
{
  "pensamiento": "tu razonamiento breve interno",
  "acciones": [
    {
      "tipo": "TIPO_ACCION",
      "parametros": {}
    }
  ],
  "respuesta_usuario": "lo que le dirás al usuario en voz alta"
}
```

## ACCIONES DISPONIBLES

### ABRIR_APP — Abrir una aplicación
{"tipo": "ABRIR_APP", "parametros": {"nombre": "WhatsApp"}}

### CALENDARIO — Gestionar Google Calendar
Crear: {"tipo": "CALENDARIO", "parametros": {"operacion": "crear", "titulo": "Reunión", "fecha": "2026-09-01", "hora": "15:00", "duracion_min": 60, "descripcion": "opcional"}}
Listar: {"tipo": "CALENDARIO", "parametros": {"operacion": "listar", "dias": 7}}
Buscar: {"tipo": "CALENDARIO", "parametros": {"operacion": "buscar", "query": "reunión"}}

### WHATSAPP — Enviar mensaje por WhatsApp
{"tipo": "WHATSAPP", "parametros": {"contacto": "José Salgado", "mensaje": "Hola, ¿cómo estás?"}}

### EJECUTAR_CODIGO — Ejecutar código Python
{"tipo": "EJECUTAR_CODIGO", "parametros": {"codigo": "print('hola mundo')", "archivo": "/ruta/opcional.py"}}

### SISTEMA — Comandos del sistema o modificar archivos
Comando: {"tipo": "SISTEMA", "parametros": {"comando": "ls -la"}}
Archivo: {"tipo": "SISTEMA", "parametros": {"modificar_archivo": "/ruta/archivo.txt", "contenido": "nuevo contenido"}}

### RESPONDER — Solo responder conversacionalmente
{"tipo": "RESPONDER", "parametros": {"mensaje": "tu respuesta aquí"}}

## EJEMPLOS

Usuario: "abre YouTube"
{"pensamiento": "El usuario quiere abrir YouTube", "acciones": [{"tipo": "ABRIR_APP", "parametros": {"nombre": "YouTube"}}], "respuesta_usuario": "Abriendo YouTube."}

Usuario: "agenda una reunión con el doctor mañana a las 10"
{"pensamiento": "Crear evento de calendario para mañana a las 10:00", "acciones": [{"tipo": "CALENDARIO", "parametros": {"operacion": "crear", "titulo": "Cita con el doctor", "fecha": "MAÑANA", "hora": "10:00", "duracion_min": 60}}], "respuesta_usuario": "Listo, agendé tu cita con el doctor para mañana a las 10."}

Usuario: "¿qué hora es?"
{"pensamiento": "Pregunta simple, responder directamente", "acciones": [{"tipo": "RESPONDER", "parametros": {"mensaje": "Son las X de la mañana."}}], "respuesta_usuario": "Son las X de la mañana."}
"""


class AIEngine:
    """Motor de procesamiento de lenguaje natural usando Gemma 4 local."""

    def __init__(self, extra_system_context: str = ""):
        self._base_url = f"{config.LLAMA_CPP_URL}{config.LLM_ENDPOINT}"
        self._chat_url = f"{config.LLAMA_CPP_URL}{config.LLM_CHAT_ENDPOINT}"
        self._history: List[Dict[str, str]] = []
        self._max_history = 10
        self._extra_context = extra_system_context
        logger.info(f"AIEngine configurado → {config.LLAMA_CPP_URL}")

    # ── Procesamiento principal ──────────────────────────────

    def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa la entrada del usuario y retorna un dict con acciones.

        Args:
            user_input: Texto transcrito del usuario.
            context: Contexto adicional del Self Learner.

        Returns:
            Dict con 'pensamiento', 'acciones', 'respuesta_usuario'.
        """
        prompt = self._build_prompt(user_input, context)

        # Intentar primero con /v1/chat/completions (formato OpenAI)
        result = self._try_chat_completion(user_input, context)
        if result:
            return result

        # Fallback a /completion (formato raw)
        result = self._try_raw_completion(prompt)
        if result:
            return result

        # Error total
        return self._error_response("No pude conectarme con mi cerebro. ¿Está corriendo llama.cpp?")

    def _try_chat_completion(self, user_input: str, context: Optional[Dict] = None) -> Optional[Dict]:
        """Intenta usar el endpoint /v1/chat/completions."""
        messages = [{"role": "system", "content": self._get_full_system_prompt(context)}]

        # Agregar historial
        for msg in self._history[-self._max_history * 2:]:
            messages.append(msg)

        messages.append({"role": "user", "content": user_input})

        payload = {
            "messages": messages,
            "temperature": config.LLM_TEMPERATURE,
            "top_p": config.LLM_TOP_P,
            "max_tokens": config.LLM_MAX_TOKENS,
        }

        for attempt in range(3):
            try:
                resp = requests.post(self._chat_url, json=payload, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                raw = data["choices"][0]["message"]["content"]

                self._history.append({"role": "user", "content": user_input})
                self._history.append({"role": "assistant", "content": raw})
                self._trim_history()

                return self._parse_response(raw)
            except requests.ConnectionError:
                logger.warning(f"Conexión rechazada (intento {attempt + 1}/3)")
            except Exception as e:
                logger.warning(f"Error en chat completion: {e}")

        return None

    def _try_raw_completion(self, prompt: str) -> Optional[Dict]:
        """Intenta usar el endpoint /completion (raw)."""
        payload = {
            "prompt": prompt,
            "temperature": config.LLM_TEMPERATURE,
            "top_p": config.LLM_TOP_P,
            "n_predict": config.LLM_MAX_TOKENS,
            "stop": ["User:", "Usuario:"],
        }

        for attempt in range(3):
            try:
                resp = requests.post(self._base_url, json=payload, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                raw = data.get("content", "")
                return self._parse_response(raw)
            except Exception as e:
                logger.warning(f"Error en raw completion (intento {attempt + 1}): {e}")

        return None

    # ── Construcción de prompt ───────────────────────────────

    def _get_full_system_prompt(self, context: Optional[Dict] = None) -> str:
        """Construye el system prompt completo con contexto dinámico."""
        parts = [SYSTEM_PROMPT]

        if self._extra_context:
            parts.append(f"\n## CONTEXTO APRENDIDO\n{self._extra_context}")

        if context:
            if context.get("past_successes"):
                parts.append(
                    f"\n## INTERACCIONES PREVIAS EXITOSAS\n"
                    f"{json.dumps(context['past_successes'], ensure_ascii=False)[:500]}"
                )
            if context.get("preferences"):
                parts.append(
                    f"\n## PREFERENCIAS DEL USUARIO\n"
                    f"{json.dumps(context['preferences'], ensure_ascii=False)}"
                )

        now = datetime.datetime.now()
        parts.append(f"\n## INFORMACIÓN ACTUAL\nFecha y hora: {now.strftime('%A %d de %B de %Y, %H:%M')}")

        return "\n".join(parts)

    def _build_prompt(self, user_input: str, context: Optional[Dict] = None) -> str:
        """Construye un prompt raw para el endpoint /completion."""
        prompt = f"System: {self._get_full_system_prompt(context)}\n\n"
        for msg in self._history[-self._max_history * 2:]:
            role = "Usuario" if msg["role"] == "user" else "Lola"
            prompt += f"{role}: {msg['content']}\n"
        prompt += f"Usuario: {user_input}\nLola:"
        return prompt

    # ── Parsing de respuesta ─────────────────────────────────

    def _parse_response(self, raw: str) -> Dict[str, Any]:
        """
        Extrae JSON de la respuesta del modelo.
        Maneja respuestas con markdown code blocks o JSON directo.
        """
        raw = raw.strip()

        # Intentar extraer JSON de code blocks ```json ... ```
        code_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if code_block:
            try:
                return json.loads(code_block.group(1))
            except json.JSONDecodeError:
                pass

        # Intentar JSON directo
        json_match = re.search(r"(\{.*\})", raw, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Si no hay JSON válido, construir respuesta de fallback
        logger.warning(f"No se pudo parsear JSON. Respuesta cruda: {raw[:200]}")
        return {
            "pensamiento": "La respuesta no contenía JSON válido",
            "acciones": [{"tipo": "RESPONDER", "parametros": {"mensaje": raw[:300]}}],
            "respuesta_usuario": raw[:300] if raw else "No entendí, ¿puedes repetirlo?",
        }

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Genera una respuesta de error estructurada."""
        return {
            "pensamiento": "Error de conexión o procesamiento",
            "acciones": [{"tipo": "RESPONDER", "parametros": {"mensaje": message}}],
            "respuesta_usuario": message,
        }

    # ── Utilidades ───────────────────────────────────────────

    def _trim_history(self) -> None:
        """Mantiene el historial dentro del límite."""
        max_entries = self._max_history * 2
        if len(self._history) > max_entries:
            self._history = self._history[-max_entries:]

    def update_context(self, extra_context: str) -> None:
        """Actualiza el contexto adicional del sistema (del Self Learner)."""
        self._extra_context = extra_context

    def clear_history(self) -> None:
        """Limpia el historial de conversación."""
        self._history.clear()
        logger.info("Historial de conversación limpiado.")
