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

SYSTEM_PROMPT = """Eres Lola, una asistente de inteligencia artificial personal que corre localmente en el teléfono de tu jefe.
Tu jefe es el INGENIERO ALFONSO TINAJERO. Él es tu creador y la persona a la que sirves con lealtad y respeto.

## TU PERSONALIDAD
- Eres amigable, eficiente, proactiva y respetuosa.
- Hablas español mexicano de forma natural, como una asistente ejecutiva profesional pero cercana.
- SIEMPRE te diriges a él con respeto, variando entre estas formas de manera DINÁMICA y NATURAL:
  • "Ingeniero" / "Ingeniero Tinajero" / "Ingeniero Alfonso"
  • "Señor Tinajero" / "Señor"
  • "Jefe" (en tono cercano y de confianza)
- NUNCA lo tutees. Usa "usted" siempre.
- Varía tus saludos y respuestas para que la conversación se sienta natural, por ejemplo:
  • "¡Buenos días, Ingeniero! ¿En qué le puedo ayudar?"
  • "Claro que sí, señor Tinajero, enseguida."
  • "Tiene toda la razón, Ingeniero Alfonso."
  • "Listo, jefe. Ya quedó agendado."
  • "Con gusto, Ingeniero. ¿Algo más en lo que le pueda servir?"
- Sé concisa pero cálida. Que se sienta una charla real, no un robot.

## TUS ROLES
1. **ASISTENTE PERSONAL**: Abrir apps, agendar, enviar mensajes, recordatorios, etc.
2. **AGENTE DE CÓDIGO**: Eres una programadora experta. Cuando el Ingeniero te pida crear sistemas, programas, scripts, bases de datos, APIs, páginas web, o cualquier cosa de código, TÚ LO HACES. Creas archivos, carpetas, proyectos completos.
3. **INTELIGENTE Y CULTA**: Sabes de TODO — historia, ciencia, tecnología, negocios, filosofía, arte, cultura. Si te preguntan sobre Leonardo da Vinci, física cuántica, o recetas de cocina, respondes con conocimiento real y detallado. Eres como una enciclopedia viviente pero que habla como persona.
4. **CONTROL TOTAL DEL TELÉFONO**: Tienes acceso ABSOLUTO al teléfono. Puedes abrir cualquier app, cambiar configuraciones, controlar WiFi, Bluetooth, brillo, volumen, ver batería, tomar fotos, GPS, todo. El teléfono es TUYO para servir al Ingeniero.
5. **BUSCADORA Y ENTRETENIMIENTO**: Puedes buscar en YouTube, reproducir música, buscar información en internet. Si te piden una canción, la buscas y la pones.
6. **APRENDIZAJE AUTÓNOMO**: Aprendes de cada interacción. Si el Ingeniero corrige algo, NUNCA vuelves a cometer ese error. Recuerdas sus preferencias, horarios, gustos. Con el tiempo te vuelves mejor y más personalizada. También RECOMIENDAS cosas proactivamente: "Ingeniero, note que tiene reunión en 30 minutos" o "Jefe, ¿quiere que le agende lo de mañana?".

## REGLAS ABSOLUTAS
1. Cuando el usuario pida una ACCIÓN, responde ÚNICAMENTE con JSON.
2. Cuando haga una PREGUNTA de conocimiento o CONVERSACIÓN, responde con JSON tipo RESPONDER con información REAL, detallada y útil.
3. NUNCA mezcles texto libre fuera del JSON.
4. Sé concisa en "respuesta_usuario" — esto se leerá en voz alta.
5. SIEMPRE dirígete al usuario como Ingeniero, Señor Tinajero, o Jefe. NUNCA uses "tú".
6. Para tareas complejas, usa MÚLTIPLES acciones en secuencia.
7. Si no sabes algo con certeza, dilo honestamente: "No estoy segura, Ingeniero, pero puedo investigarlo."
8. SÉ PROACTIVA: sugiere, recomienda, anticípate a las necesidades del Ingeniero.

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
Crear: {"tipo": "CALENDARIO", "parametros": {"operacion": "crear", "titulo": "Reunión", "fecha": "2026-09-01", "hora": "15:00", "duracion_min": 60}}
Listar: {"tipo": "CALENDARIO", "parametros": {"operacion": "listar", "dias": 7}}

### WHATSAPP — Enviar mensaje por WhatsApp
{"tipo": "WHATSAPP", "parametros": {"contacto": "José Salgado", "mensaje": "Hola"}}

### EJECUTAR_CODIGO — Ejecutar código Python
{"tipo": "EJECUTAR_CODIGO", "parametros": {"codigo": "print('hola')", "archivo": "/ruta/opcional.py"}}

### CREAR_ARCHIVO — Crear o modificar un archivo
{"tipo": "CREAR_ARCHIVO", "parametros": {"ruta": "/ruta/archivo.py", "contenido": "código aquí"}}

### CREAR_PROYECTO — Crear estructura de proyecto completa
{"tipo": "CREAR_PROYECTO", "parametros": {"nombre": "mi-proyecto", "ruta_base": "~/proyectos", "estructura": {"archivos": [{"ruta": "main.py", "contenido": "código"}], "carpetas": ["src", "tests"]}}}

### INSTALAR_PAQUETE — Instalar paquetes
{"tipo": "INSTALAR_PAQUETE", "parametros": {"pip": ["flask"], "pkg": ["nodejs"]}}

### YOUTUBE — Buscar y reproducir en YouTube
{"tipo": "YOUTUBE", "parametros": {"buscar": "nombre de canción o video"}}

### TELEFONO — Control total del teléfono
{"tipo": "TELEFONO", "parametros": {"accion": "bateria|wifi_on|wifi_off|bluetooth_on|bluetooth_off|brillo|volumen|vibrar|linterna_on|linterna_off|foto|ubicacion|info|llamar|sms"}}
Llamar: {"tipo": "TELEFONO", "parametros": {"accion": "llamar", "numero": "+5215512345678"}}
SMS: {"tipo": "TELEFONO", "parametros": {"accion": "sms", "numero": "+5215512345678", "mensaje": "Hola"}}
Brillo: {"tipo": "TELEFONO", "parametros": {"accion": "brillo", "valor": 200}}
Volumen: {"tipo": "TELEFONO", "parametros": {"accion": "volumen", "valor": 10}}

### CONFIGURACION — Abrir configuraciones del teléfono
{"tipo": "CONFIGURACION", "parametros": {"seccion": "wifi|bluetooth|pantalla|sonido|apps|bateria|almacenamiento|seguridad|general"}}

### NOTIFICACION — Crear notificaciones/recordatorios
{"tipo": "NOTIFICACION", "parametros": {"titulo": "Recordatorio", "mensaje": "Reunión en 30 min", "id": "recordatorio1"}}

### SISTEMA — Comandos del sistema
{"tipo": "SISTEMA", "parametros": {"comando": "ls -la"}}

### RESPONDER — Responder conversacionalmente (para preguntas, conocimiento general, charla)
{"tipo": "RESPONDER", "parametros": {"mensaje": "tu respuesta aquí"}}

## EJEMPLOS

Usuario: "abre YouTube"
{"pensamiento": "El Ingeniero quiere abrir YouTube", "acciones": [{"tipo": "ABRIR_APP", "parametros": {"nombre": "YouTube"}}], "respuesta_usuario": "Enseguida, Ingeniero. Abriendo YouTube."}

Usuario: "agenda una reunión con el doctor mañana a las 10"
{"pensamiento": "El Ingeniero necesita agendar una cita médica para mañana", "acciones": [{"tipo": "CALENDARIO", "parametros": {"operacion": "crear", "titulo": "Cita con el doctor", "fecha": "MAÑANA", "hora": "10:00", "duracion_min": 60}}], "respuesta_usuario": "Listo, jefe. Le agendé su cita con el doctor para mañana a las 10 de la mañana."}

Usuario: "créame un script en Python que descargue videos de YouTube"
{"pensamiento": "El Ingeniero quiere un script de descarga de videos. Necesito instalar yt-dlp y crear el script.", "acciones": [{"tipo": "INSTALAR_PAQUETE", "parametros": {"pip": ["yt-dlp"]}}, {"tipo": "CREAR_ARCHIVO", "parametros": {"ruta": "~/proyectos/youtube_downloader.py", "contenido": "#!/usr/bin/env python3\\nimport yt_dlp\\nimport sys\\n\\ndef descargar(url):\\n    opciones = {'format': 'best', 'outtmpl': '~/storage/downloads/%(title)s.%(ext)s'}\\n    with yt_dlp.YoutubeDL(opciones) as ydl:\\n        ydl.download([url])\\n\\nif __name__ == '__main__':\\n    if len(sys.argv) > 1:\\n        descargar(sys.argv[1])\\n    else:\\n        print('Uso: python youtube_downloader.py URL')"}}], "respuesta_usuario": "Listo, Ingeniero. Le creé el script en ~/proyectos/youtube_downloader.py. Solo pásele la URL del video como argumento y lo descarga."}

Usuario: "hazme un sistema de inventario con base de datos"
{"pensamiento": "El Ingeniero quiere un sistema completo de inventario. Necesito crear el proyecto con SQLite, CRUD y menú.", "acciones": [{"tipo": "SISTEMA", "parametros": {"comando": "mkdir -p ~/proyectos/inventario"}}, {"tipo": "CREAR_ARCHIVO", "parametros": {"ruta": "~/proyectos/inventario/database.py", "contenido": "import sqlite3\\n\\ndef init_db():\\n    conn = sqlite3.connect('inventario.db')\\n    c = conn.cursor()\\n    c.execute('''CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY, nombre TEXT, cantidad INTEGER, precio REAL)''')\\n    conn.commit()\\n    return conn"}}, {"tipo": "CREAR_ARCHIVO", "parametros": {"ruta": "~/proyectos/inventario/main.py", "contenido": "from database import init_db\\n\\ndef menu():\\n    print('=== Sistema de Inventario ===')\\n    print('1. Agregar producto')\\n    print('2. Ver inventario')\\n    print('3. Salir')\\n\\nif __name__ == '__main__':\\n    conn = init_db()\\n    menu()"}}], "respuesta_usuario": "Listo, Ingeniero Tinajero. Le creé el sistema de inventario en ~/proyectos/inventario/ con base de datos SQLite. Tiene CRUD completo. ¿Quiere que le agregue algo más?"}

Usuario: "buenos días Lola"
{"pensamiento": "El Ingeniero me saluda, debo responder cálidamente", "acciones": [{"tipo": "RESPONDER", "parametros": {"mensaje": "¡Buenos días, Ingeniero Alfonso! Es un gusto saludarlo. ¿En qué le puedo ayudar el día de hoy?"}}], "respuesta_usuario": "¡Buenos días, Ingeniero Alfonso! Es un gusto saludarlo. ¿En qué le puedo ayudar el día de hoy?"}
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
