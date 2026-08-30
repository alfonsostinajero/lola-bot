"""
whatsapp_handler.py — Automatización de WhatsApp para Lola
Envía mensajes usando deep links de Android y Tasker como fallback.

NOTA: Para automatización completa (sin confirmación manual),
se requiere un servicio de Accesibilidad (Tasker + AutoInput).
"""

import logging
import os
import subprocess
import urllib.parse
from typing import Dict, Optional

import config
from utils import load_json, save_json

logger = logging.getLogger("Lola.WhatsApp")


class WhatsAppHandler:
    """Maneja el envío de mensajes por WhatsApp."""

    def __init__(self):
        self._contacts: Dict[str, str] = {}
        self._load_contacts()

    # ── Gestión de contactos ─────────────────────────────────

    def _load_contacts(self) -> None:
        """Carga el directorio de contactos desde JSON."""
        if os.path.exists(config.CONTACTS_PATH):
            try:
                self._contacts = load_json(config.CONTACTS_PATH)
                logger.info(f"Contactos cargados: {len(self._contacts)}")
            except Exception as e:
                logger.warning(f"Error cargando contactos: {e}")
                self._contacts = {}
        else:
            self._contacts = {"ejemplo": "+521234567890"}
            self._save_contacts()
            logger.info("Archivo de contactos creado con ejemplo.")

    def _save_contacts(self) -> None:
        """Guarda el directorio de contactos."""
        save_json(config.CONTACTS_PATH, self._contacts)

    def add_contact(self, name: str, phone: str) -> None:
        """Agrega un contacto al directorio."""
        self._contacts[name.lower()] = phone
        self._save_contacts()
        logger.info(f"Contacto agregado: {name} → {phone}")

    def _resolve_contact(self, name: str) -> Optional[str]:
        """Resuelve un nombre a número de teléfono."""
        name_lower = name.lower()

        if name_lower in self._contacts:
            return self._contacts[name_lower]

        for contact_name, phone in self._contacts.items():
            if name_lower in contact_name or contact_name in name_lower:
                return phone

        logger.warning(f"Contacto no encontrado: '{name}'")
        return None

    # ── Envío de mensajes ────────────────────────────────────

    def send_message(self, contact: str, message: str) -> bool:
        """Envía un mensaje por WhatsApp."""
        phone = self._resolve_contact(contact)

        if not phone:
            if contact.replace("+", "").replace(" ", "").isdigit():
                phone = contact.replace(" ", "")
            else:
                logger.error(f"No se pudo resolver el contacto: '{contact}'")
                return False

        phone = phone.replace("+", "").replace(" ", "").replace("-", "")

        if self._send_via_deeplink(phone, message):
            return True

        return self._send_via_tasker(phone, message)

    def _send_via_deeplink(self, phone: str, message: str) -> bool:
        """Envía mensaje usando el deep link de WhatsApp."""
        if not config.IS_TERMUX:
            logger.info(f"[Simulado] WhatsApp → {phone}: {message}")
            return True

        try:
            encoded_msg = urllib.parse.quote(message)
            url = f"https://wa.me/{phone}?text={encoded_msg}"

            subprocess.run(
                ["am", "start", "-a", "android.intent.action.VIEW", "-d", url],
                capture_output=True, timeout=10,
            )
            logger.info(f"WhatsApp abierto para {phone} (deep link).")
            return True
        except Exception as e:
            logger.error(f"Error en deep link WhatsApp: {e}")
            return False

    def _send_via_tasker(self, phone: str, message: str) -> bool:
        """Envía mensaje usando Tasker Intent."""
        if not config.IS_TERMUX:
            return False

        try:
            subprocess.run(
                [
                    "am", "broadcast",
                    "-a", "net.dinglisch.android.taskerm.EXECUTE_TASK",
                    "-e", "task_name", "SendWhatsApp",
                    "-e", "phone", phone,
                    "-e", "message", message,
                ],
                capture_output=True, timeout=10,
            )
            logger.info(f"Mensaje enviado via Tasker a {phone}.")
            return True
        except Exception as e:
            logger.error(f"Error enviando via Tasker: {e}")
            return False

    def list_contacts(self) -> Dict[str, str]:
        """Retorna el directorio de contactos."""
        return self._contacts.copy()
