"""
self_modifier.py — Módulo de auto-modificación de código para Lola AI
Permite que Lola modifique su propio código de forma segura:
- Backup automático antes de cada cambio
- Validación de sintaxis antes de aplicar
- Rollback automático si algo falla
- Módulos protegidos que NUNCA se modifican
- Hot-reload sin reiniciar
"""

import ast
import importlib
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import config

logger = logging.getLogger("Lola.Modifier")


class SelfModifier:
    """
    Sistema de auto-modificación de código con múltiples capas de seguridad.
    
    Seguridad:
    - self_modifier.py y config.py NUNCA se auto-modifican
    - lola_core.py, ai_engine.py requieren aprobación explícita
    - Máximo 10 versiones de backup por módulo
    - Validación de sintaxis obligatoria antes de aplicar
    - Rollback automático si falla el hot-reload
    """

    def __init__(self, project_dir: Optional[str] = None):
        self._project_dir = Path(project_dir or str(config.PROJECT_DIR))
        self._backup_dir = Path(str(config.BACKUP_DIR))
        self._log_file = Path(str(config.LOG_DIR)) / "modifications.json"
        self._max_versions = config.MAX_BACKUP_VERSIONS
        
        # Asegurar directorios
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        if not self._log_file.exists():
            self._log_file.write_text("[]", encoding="utf-8")
        
        logger.info(f"SelfModifier listo. Proyecto: {self._project_dir}")

    # ── Lectura de código ────────────────────────────────

    def read_own_source(self, module_name: str) -> str:
        """
        Lee el código fuente de cualquier módulo del proyecto.
        
        Args:
            module_name: Nombre del módulo (sin .py).
        
        Returns:
            Código fuente como string.
        """
        path = self._module_path(module_name)
        if not path.exists():
            raise FileNotFoundError(f"Módulo no encontrado: {module_name} ({path})")
        return path.read_text(encoding="utf-8")

    def _module_path(self, module_name: str) -> Path:
        """Obtiene la ruta de un módulo."""
        name = module_name.replace(".py", "")
        return self._project_dir / f"{name}.py"

    # ── Proponer modificación ────────────────────────────

    def propose_modification(
        self, module_name: str, description: str, ai_engine=None
    ) -> Dict[str, Any]:
        """
        Propone una modificación de código usando el AI Engine.
        
        Args:
            module_name: Módulo a modificar.
            description: Descripción de la mejora deseada.
            ai_engine: Instancia del AIEngine para generar código.
        
        Returns:
            Dict con la propuesta de modificación.
        """
        current_code = self.read_own_source(module_name)

        if ai_engine:
            prompt = (
                f"Modifica el siguiente código Python según esta descripción: {description}\n\n"
                f"Código actual:\n```python\n{current_code[:3000]}\n```\n\n"
                "Responde SOLO con el código Python completo modificado, sin explicaciones."
            )
            response = ai_engine.process(prompt)
            proposed_code = response.get("respuesta_usuario", current_code)
        else:
            proposed_code = current_code  # Sin IA, no hay propuesta

        proposal = {
            "module": module_name,
            "description": description,
            "original_code_hash": hash(current_code),
            "proposed_code": proposed_code,
            "timestamp": datetime.now().isoformat(),
            "validated": False,
        }

        # Validar sintaxis automáticamente
        is_valid, msg = self.validate_code(proposed_code)
        proposal["validated"] = is_valid
        proposal["validation_message"] = msg

        return proposal

    # ── Aplicar modificación ─────────────────────────────

    def apply_modification(
        self, module_name: str, modification: Dict[str, Any], auto_approved: bool = False
    ) -> bool:
        """
        Aplica una modificación de código con todas las capas de seguridad.
        
        Proceso:
        1. Verificar que el módulo no está protegido
        2. Validar sintaxis del código nuevo
        3. Crear backup del código actual
        4. Escribir código nuevo
        5. Intentar hot-reload
        6. Si falla → rollback automático
        
        Args:
            module_name: Módulo a modificar.
            modification: Dict con 'proposed_code'.
            auto_approved: Si True, permite modificar módulos que requieren aprobación.
        
        Returns:
            True si la modificación se aplicó exitosamente.
        """
        # SEGURIDAD: Verificar protección
        clean_name = module_name.replace(".py", "")
        
        if clean_name in config.PROTECTED_MODULES:
            logger.warning(
                f"❌ BLOQUEADO: '{clean_name}' es un módulo protegido. "
                "NUNCA se puede auto-modificar."
            )
            self._log_modification(module_name, False, "Módulo protegido")
            return False

        if clean_name in config.APPROVAL_REQUIRED_MODULES and not auto_approved:
            logger.warning(
                f"⚠️ '{clean_name}' requiere aprobación explícita. "
                "Usa auto_approved=True para forzar."
            )
            self._log_modification(module_name, False, "Requiere aprobación")
            return False

        new_code = modification.get("proposed_code", "")
        if not new_code:
            logger.error("No hay código propuesto en la modificación.")
            return False

        # Validar sintaxis
        is_valid, msg = self.validate_code(new_code)
        if not is_valid:
            logger.error(f"❌ Sintaxis inválida: {msg}")
            self._log_modification(module_name, False, f"Sintaxis inválida: {msg}")
            return False

        path = self._module_path(module_name)

        # Crear backup
        if path.exists():
            backup_path = self._create_backup(module_name)
            logger.info(f"Backup creado: {backup_path}")

        # Aplicar cambio
        try:
            path.write_text(new_code, encoding="utf-8")
            logger.info(f"Código escrito en {path}")

            # Hot-reload
            if not self.hot_reload(clean_name):
                raise RuntimeError("Hot-reload falló")

            self._log_modification(
                module_name, True,
                modification.get("description", "Modificación aplicada")
            )
            logger.info(f"✅ Módulo '{module_name}' modificado y recargado exitosamente.")
            return True

        except Exception as e:
            logger.error(f"Error aplicando modificación: {e}. Iniciando rollback...")
            self.rollback(module_name)
            self._log_modification(module_name, False, f"Error + rollback: {e}")
            return False

    # ── Backup y Rollback ────────────────────────────────

    def _create_backup(self, module_name: str) -> str:
        """Crea backup con timestamp y limpia versiones antiguas."""
        clean_name = module_name.replace(".py", "")
        source = self._module_path(module_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{clean_name}_{timestamp}.py"
        backup_path = self._backup_dir / backup_name

        shutil.copy2(str(source), str(backup_path))

        # Limpiar versiones antiguas
        self._cleanup_old_backups(clean_name)

        return str(backup_path)

    def _cleanup_old_backups(self, module_name: str) -> None:
        """Mantiene solo las últimas N versiones de backup."""
        backups = sorted(
            [f for f in self._backup_dir.iterdir() if f.name.startswith(f"{module_name}_")],
            key=lambda f: f.stat().st_mtime,
        )
        if len(backups) > self._max_versions:
            for old in backups[: len(backups) - self._max_versions]:
                old.unlink()
                logger.debug(f"Backup antiguo eliminado: {old.name}")

    def rollback(self, module_name: str, version: Optional[str] = None) -> bool:
        """
        Restaura un módulo desde su backup más reciente.
        
        Args:
            module_name: Módulo a restaurar.
            version: Nombre específico del backup. Si None, usa el más reciente.
        """
        clean_name = module_name.replace(".py", "")
        target = self._module_path(module_name)

        if version:
            backup = self._backup_dir / version
        else:
            backups = sorted(
                [f for f in self._backup_dir.iterdir() if f.name.startswith(f"{clean_name}_")],
                key=lambda f: f.stat().st_mtime,
            )
            if not backups:
                logger.error(f"No hay backups disponibles para '{module_name}'.")
                return False
            backup = backups[-1]

        try:
            shutil.copy2(str(backup), str(target))
            self.hot_reload(clean_name)
            logger.info(f"🔄 Rollback exitoso: {module_name} restaurado desde {backup.name}")
            return True
        except Exception as e:
            logger.error(f"❌ Rollback fallido para {module_name}: {e}")
            return False

    # ── Validación ───────────────────────────────────────

    def validate_code(self, code: str) -> Tuple[bool, str]:
        """
        Valida la sintaxis Python del código.
        
        Returns:
            Tuple (es_valido, mensaje).
        """
        try:
            ast.parse(code)
            return True, "Sintaxis válida"
        except SyntaxError as e:
            return False, f"Error de sintaxis en línea {e.lineno}: {e.msg}"

    # ── Hot Reload ───────────────────────────────────────

    def hot_reload(self, module_name: str) -> bool:
        """
        Recarga un módulo en caliente sin reiniciar el sistema.
        Usa importlib.reload() para módulos ya cargados.
        """
        try:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                logger.info(f"Módulo '{module_name}' recargado en caliente.")
            else:
                importlib.import_module(module_name)
                logger.info(f"Módulo '{module_name}' importado por primera vez.")
            return True
        except Exception as e:
            logger.error(f"Error en hot-reload de '{module_name}': {e}")
            return False

    # ── Historial ────────────────────────────────────────

    def get_modification_history(self, module_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene el historial de modificaciones."""
        try:
            logs = json.loads(self._log_file.read_text(encoding="utf-8"))
            if module_name:
                return [l for l in logs if l.get("module") == module_name]
            return logs
        except Exception:
            return []

    def _log_modification(self, module_name: str, success: bool, details: str) -> None:
        """Registra una modificación en el log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "module": module_name,
            "success": success,
            "details": details,
        }
        try:
            logs = json.loads(self._log_file.read_text(encoding="utf-8"))
            logs.append(entry)
            # Mantener solo las últimas 500 entradas
            if len(logs) > 500:
                logs = logs[-500:]
            self._log_file.write_text(
                json.dumps(logs, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Error escribiendo log de modificaciones: {e}")
