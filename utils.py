"""
utils.py — Funciones utilitarias para Lola AI Assistant
"""

import json
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import config


def setup_logging(name: str = "Lola", level: int = logging.INFO) -> logging.Logger:
    """Configura y retorna un logger con formato estándar."""
    log_file = config.LOG_DIR / f"{name.lower()}.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(str(log_file), encoding="utf-8")
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger


def safe_execute(func: Callable, *args: Any, **kwargs: Any) -> Tuple[bool, Any]:
    """Ejecuta una función capturando excepciones. Retorna (éxito, resultado_o_error)."""
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        logging.getLogger("Lola.Utils").error(f"Error en {func.__name__}: {e}")
        return False, str(e)


def format_datetime_spanish(dt: Optional[datetime] = None) -> str:
    """
    Formatea fecha/hora en español natural.
    Ej: 'Lunes 15 de Enero de 2026 a las 3:00 PM'
    """
    if dt is None:
        dt = datetime.now()

    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = [
        "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ]

    dia_sem = dias[dt.weekday()]
    mes = meses[dt.month]
    hora = dt.strftime("%I:%M %p")

    return f"{dia_sem} {dt.day} de {mes} de {dt.year} a las {hora}"


def parse_natural_date(text: str) -> Optional[datetime]:
    """
    Parsea fechas en lenguaje natural español.
    Soporta: 'hoy', 'mañana', 'pasado mañana', 'el lunes', 'en 2 horas', etc.
    """
    text = text.lower().strip()
    now = datetime.now()

    if "hoy" in text:
        return now
    if "mañana" in text and "pasado" not in text:
        return now + timedelta(days=1)
    if "pasado mañana" in text:
        return now + timedelta(days=2)

    hours_match = re.search(r"en\s+(\d+)\s*horas?", text)
    if hours_match:
        return now + timedelta(hours=int(hours_match.group(1)))

    mins_match = re.search(r"en\s+(\d+)\s*minutos?", text)
    if mins_match:
        return now + timedelta(minutes=int(mins_match.group(1)))

    days_match = re.search(r"en\s+(\d+)\s*d[ií]as?", text)
    if days_match:
        return now + timedelta(days=int(days_match.group(1)))

    dias_semana = {
        "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
        "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6,
    }
    for dia_nombre, dia_num in dias_semana.items():
        if dia_nombre in text:
            days_ahead = dia_num - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return now + timedelta(days=days_ahead)

    return None


def sanitize_command(cmd: str) -> str:
    """Limpia un comando shell para prevenir inyección básica."""
    dangerous = ["rm -rf /", "mkfs", "dd if=", "> /dev/", ":(){ :|:& };:"]
    for d in dangerous:
        if d in cmd:
            return "echo 'Comando bloqueado por seguridad'"
    return cmd


def get_device_info() -> Dict[str, Any]:
    """Obtiene información del dispositivo Android via Termux:API."""
    info = {}

    if not config.IS_TERMUX:
        return {"entorno": "no-termux", "nota": "Info de dispositivo solo disponible en Termux"}

    try:
        result = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
        info["bateria"] = json.loads(result.stdout)
    except Exception:
        info["bateria"] = "no disponible"

    try:
        result = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=5)
        info["wifi"] = json.loads(result.stdout)
    except Exception:
        info["wifi"] = "no disponible"

    return info


def file_backup(filepath: str) -> str:
    """Crea un backup con timestamp de un archivo."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = Path(filepath).stem
    ext = Path(filepath).suffix
    backup_path = str(config.BACKUP_DIR / f"{name}_{timestamp}{ext}")
    shutil.copy2(filepath, backup_path)
    return backup_path


def load_json(path: str) -> Dict[str, Any]:
    """Carga un archivo JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Any) -> None:
    """Guarda datos en un archivo JSON."""
    ensure_dir(str(Path(path).parent))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ensure_dir(path: str) -> None:
    """Crea un directorio si no existe."""
    Path(path).mkdir(parents=True, exist_ok=True)
