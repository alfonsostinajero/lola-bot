"""
action_executor.py — Ejecutor de acciones para Lola AI
Recibe acciones estructuradas del AI Engine y las ejecuta.
"""

import logging
import subprocess
import urllib.parse
from typing import Any, Dict

import config

logger = logging.getLogger("Lola.Executor")


class ActionExecutor:
    """Ejecuta acciones del sistema basadas en las respuestas del AI Engine."""

    def __init__(self):
        self._calendar = None  # Se inicializa lazy
        self._whatsapp = None  # Se inicializa lazy

        # Registro de handlers por tipo de acción
        self._handlers = {
            "ABRIR_APP": self._abrir_app,
            "CALENDARIO": self._calendario,
            "WHATSAPP": self._whatsapp_action,
            "EJECUTAR_CODIGO": self._ejecutar_codigo,
            "CREAR_ARCHIVO": self._crear_archivo,
            "CREAR_PROYECTO": self._crear_proyecto,
            "INSTALAR_PAQUETE": self._instalar_paquete,
            "SISTEMA": self._sistema,
            "RESPONDER": self._responder,
        }
        logger.info(f"ActionExecutor listo. Acciones: {list(self._handlers.keys())}")

    # ── Ejecutor principal ───────────────────────────────────

    def execute(self, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta todas las acciones de una respuesta del AI Engine.

        Args:
            ai_response: Dict con 'acciones' y 'respuesta_usuario' del AI Engine.

        Returns:
            Dict con resultados de ejecución.
        """
        results = []
        acciones = ai_response.get("acciones", [])
        respuesta = ai_response.get("respuesta_usuario", "")

        if not acciones:
            return {"success": True, "respuesta": respuesta, "resultados": []}

        for accion in acciones:
            tipo = accion.get("tipo", "").upper()
            parametros = accion.get("parametros", {})

            handler = self._handlers.get(tipo)
            if handler:
                logger.info(f"Ejecutando acción: {tipo} → {parametros}")
                try:
                    result = handler(parametros)
                    results.append({"tipo": tipo, "success": True, "data": result})
                except Exception as e:
                    logger.error(f"Error ejecutando {tipo}: {e}")
                    results.append({"tipo": tipo, "success": False, "error": str(e)})
            else:
                logger.warning(f"Acción desconocida: {tipo}")
                results.append({"tipo": tipo, "success": False, "error": "Acción no reconocida"})

        return {
            "success": all(r["success"] for r in results),
            "respuesta": respuesta,
            "resultados": results,
        }

    # ── Handlers de acciones ─────────────────────────────────

    def _abrir_app(self, params: Dict[str, Any]) -> Dict:
        """Abre una aplicación Android usando 'am start'."""
        nombre = params.get("nombre", "").lower()
        paquete = params.get("paquete") or config.APP_PACKAGES.get(nombre)

        if not paquete:
            # Intentar búsqueda parcial
            for key, pkg in config.APP_PACKAGES.items():
                if nombre in key or key in nombre:
                    paquete = pkg
                    break

        if not paquete:
            raise ValueError(f"App no encontrada: '{nombre}'. Agrega el paquete en config.APP_PACKAGES.")

        if config.IS_TERMUX:
            cmd = f"monkey -p {paquete} -c android.intent.category.LAUNCHER 1"
            subprocess.run(["sh", "-c", cmd], capture_output=True, timeout=10)

        logger.info(f"App abierta: {nombre} ({paquete})")
        return {"app": nombre, "paquete": paquete, "estado": "abierta"}

    def _calendario(self, params: Dict[str, Any]) -> Dict:
        """Gestiona operaciones de Google Calendar."""
        if self._calendar is None:
            from calendar_helper import CalendarHelper
            self._calendar = CalendarHelper()

        operacion = params.get("operacion", "").lower()

        if operacion == "crear":
            event_id = self._calendar.create_event(
                titulo=params.get("titulo", "Evento sin título"),
                fecha=params.get("fecha", ""),
                hora=params.get("hora", "12:00"),
                duracion=params.get("duracion_min", 60),
                descripcion=params.get("descripcion", ""),
            )
            return {"operacion": "crear", "event_id": event_id}

        elif operacion == "listar":
            events = self._calendar.list_events(dias=params.get("dias", 7))
            return {"operacion": "listar", "eventos": events}

        elif operacion == "buscar":
            events = self._calendar.search_events(query=params.get("query", ""))
            return {"operacion": "buscar", "eventos": events}

        elif operacion == "eliminar":
            success = self._calendar.delete_event(event_id=params.get("event_id", ""))
            return {"operacion": "eliminar", "success": success}

        elif operacion == "siguiente":
            event = self._calendar.get_next_event()
            return {"operacion": "siguiente", "evento": event}

        else:
            raise ValueError(f"Operación de calendario no reconocida: {operacion}")

    def _whatsapp_action(self, params: Dict[str, Any]) -> Dict:
        """Envía un mensaje por WhatsApp."""
        if self._whatsapp is None:
            from whatsapp_handler import WhatsAppHandler
            self._whatsapp = WhatsAppHandler()

        contacto = params.get("contacto", "")
        mensaje = params.get("mensaje", "")

        if not contacto or not mensaje:
            raise ValueError("Se requiere 'contacto' y 'mensaje' para WhatsApp.")

        success = self._whatsapp.send_message(contacto, mensaje)
        return {"contacto": contacto, "enviado": success}

    def _ejecutar_codigo(self, params: Dict[str, Any]) -> Dict:
        """Ejecuta código Python."""
        codigo = params.get("codigo", "")
        archivo = params.get("archivo", "")

        if archivo:
            result = subprocess.run(
                ["python", archivo], capture_output=True, text=True, timeout=30,
            )
            return {
                "modo": "archivo", "archivo": archivo,
                "stdout": result.stdout[:1000], "stderr": result.stderr[:500],
                "returncode": result.returncode,
            }
        elif codigo:
            result = subprocess.run(
                ["python", "-c", codigo], capture_output=True, text=True, timeout=30,
            )
            return {
                "modo": "inline",
                "stdout": result.stdout[:1000], "stderr": result.stderr[:500],
                "returncode": result.returncode,
            }
        else:
            raise ValueError("Se requiere 'codigo' o 'archivo' para ejecutar.")

    def _sistema(self, params: Dict[str, Any]) -> Dict:
        """Ejecuta comandos del sistema o modifica archivos."""
        from utils import sanitize_command, file_backup
        import os

        # Modificar archivo
        if "modificar_archivo" in params:
            ruta = params["modificar_archivo"]
            contenido = params.get("contenido", "")

            if os.path.exists(ruta):
                backup = file_backup(ruta)
                logger.info(f"Backup creado: {backup}")

            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)

            return {"accion": "modificar_archivo", "ruta": ruta, "estado": "modificado"}

        # Ejecutar comando
        comando = params.get("comando", "")
        if not comando:
            raise ValueError("Se requiere 'comando' o 'modificar_archivo'.")

        comando = sanitize_command(comando)
        result = subprocess.run(
            comando, shell=True, capture_output=True, text=True, timeout=30,
        )
        return {
            "accion": "comando", "comando": comando,
            "stdout": result.stdout[:2000], "stderr": result.stderr[:500],
            "returncode": result.returncode,
        }

    def _crear_archivo(self, params: Dict[str, Any]) -> Dict:
        """Crea o modifica un archivo con contenido específico."""
        import os

        ruta = params.get("ruta", "")
        contenido = params.get("contenido", "")

        if not ruta:
            raise ValueError("Se requiere 'ruta' para crear archivo.")

        # Expandir ~ a home
        ruta = os.path.expanduser(ruta)

        # Crear directorio padre si no existe
        directorio = os.path.dirname(ruta)
        if directorio:
            os.makedirs(directorio, exist_ok=True)

        # Escribir archivo
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)

        # Hacer ejecutable si es script
        if ruta.endswith((".sh", ".py")):
            os.chmod(ruta, 0o755)

        logger.info(f"Archivo creado: {ruta} ({len(contenido)} bytes)")
        return {"accion": "crear_archivo", "ruta": ruta, "bytes": len(contenido)}

    def _crear_proyecto(self, params: Dict[str, Any]) -> Dict:
        """Crea una estructura de proyecto completa con carpetas y archivos."""
        import os

        nombre = params.get("nombre", "proyecto")
        ruta_base = os.path.expanduser(params.get("ruta_base", "~/proyectos"))
        estructura = params.get("estructura", {})

        ruta_proyecto = os.path.join(ruta_base, nombre)
        os.makedirs(ruta_proyecto, exist_ok=True)

        archivos_creados = []

        # Crear carpetas
        for carpeta in estructura.get("carpetas", []):
            ruta_carpeta = os.path.join(ruta_proyecto, carpeta)
            os.makedirs(ruta_carpeta, exist_ok=True)

        # Crear archivos
        for archivo in estructura.get("archivos", []):
            ruta_archivo = os.path.join(ruta_proyecto, archivo.get("ruta", ""))
            contenido = archivo.get("contenido", "")

            directorio = os.path.dirname(ruta_archivo)
            if directorio:
                os.makedirs(directorio, exist_ok=True)

            with open(ruta_archivo, "w", encoding="utf-8") as f:
                f.write(contenido)

            archivos_creados.append(ruta_archivo)

        logger.info(f"Proyecto creado: {ruta_proyecto} ({len(archivos_creados)} archivos)")
        return {
            "accion": "crear_proyecto",
            "ruta": ruta_proyecto,
            "archivos_creados": archivos_creados,
        }

    def _instalar_paquete(self, params: Dict[str, Any]) -> Dict:
        """Instala paquetes de Python (pip) o del sistema (pkg)."""
        resultados = []

        # Instalar paquetes pip
        pip_packages = params.get("pip", [])
        if pip_packages:
            cmd = f"pip install {' '.join(pip_packages)}"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=120,
            )
            resultados.append({
                "tipo": "pip",
                "paquetes": pip_packages,
                "success": result.returncode == 0,
                "output": result.stdout[-500:] if result.stdout else result.stderr[-500:],
            })

        # Instalar paquetes del sistema (Termux)
        pkg_packages = params.get("pkg", [])
        if pkg_packages and config.IS_TERMUX:
            cmd = f"pkg install -y {' '.join(pkg_packages)}"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=120,
            )
            resultados.append({
                "tipo": "pkg",
                "paquetes": pkg_packages,
                "success": result.returncode == 0,
                "output": result.stdout[-500:] if result.stdout else result.stderr[-500:],
            })

        logger.info(f"Paquetes instalados: pip={pip_packages}, pkg={pkg_packages}")
        return {"accion": "instalar_paquete", "resultados": resultados}

    def _responder(self, params: Dict[str, Any]) -> Dict:
        """Simplemente retorna el mensaje para TTS (no ejecuta nada)."""
        return {"mensaje": params.get("mensaje", "")}
