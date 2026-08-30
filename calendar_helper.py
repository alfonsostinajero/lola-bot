"""
calendar_helper.py — Integración con Google Calendar para Lola
Maneja autenticación OAuth2 y operaciones CRUD de eventos.

Cómo obtener credenciales (GRATIS):
1. Ve a https://console.cloud.google.com/
2. Crea un proyecto nuevo llamado 'Lola AI'
3. En 'APIs y Servicios' → 'Biblioteca', habilita 'Google Calendar API'
4. Ve a 'Credenciales' → 'Crear credenciales' → 'ID de cliente OAuth'
5. Tipo de aplicación: 'Aplicación de escritorio'
6. Descarga el JSON y renómbralo a 'credentials.json'
7. Cópialo a ~/.lola/data/credentials.json
8. La primera vez que uses el calendario, se abrirá el navegador para autorizar
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import config
from utils import parse_natural_date

logger = logging.getLogger("Lola.Calendar")


class CalendarHelper:
    """Gestiona la integración con Google Calendar."""

    def __init__(self):
        self._service = None
        self._authenticated = False
        self._timezone = config.CALENDAR_TIMEZONE

    # ── Autenticación ────────────────────────────────────

    def authenticate(self) -> bool:
        """
        Maneja el flujo OAuth2 de Google.
        Guarda y reutiliza tokens automáticamente.
        """
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError:
            logger.error(
                "Dependencias de Google no instaladas. Ejecuta:\n"
                "pip install google-auth google-auth-oauthlib google-api-python-client"
            )
            return False

        creds = None

        # Intentar cargar token existente
        if os.path.exists(config.CALENDAR_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(
                config.CALENDAR_TOKEN_PATH, config.CALENDAR_SCOPES
            )

        # Si no hay token o expiró
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refrescando token de Google Calendar...")
                creds.refresh(Request())
            else:
                if not os.path.exists(config.CALENDAR_CREDENTIALS_PATH):
                    logger.error(
                        f"No se encontró {config.CALENDAR_CREDENTIALS_PATH}. "
                        "Descarga las credenciales OAuth desde Google Cloud Console."
                    )
                    return False

                logger.info("Iniciando flujo de autorización OAuth...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.CALENDAR_CREDENTIALS_PATH,
                    config.CALENDAR_SCOPES,
                )
                creds = flow.run_local_server(port=0)

            # Guardar token para futuras sesiones
            with open(config.CALENDAR_TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())
            logger.info("Token de Google Calendar guardado.")

        self._service = build("calendar", "v3", credentials=creds)
        self._authenticated = True
        logger.info("Google Calendar autenticado correctamente.")
        return True

    def _ensure_auth(self) -> None:
        """Asegura que estemos autenticados antes de cualquier operación."""
        if not self._authenticated:
            if not self.authenticate():
                raise ConnectionError("No se pudo autenticar con Google Calendar.")

    # ── Operaciones CRUD ─────────────────────────────────

    def create_event(
        self,
        titulo: str,
        fecha: str,
        hora: str = "12:00",
        duracion: int = 60,
        descripcion: str = "",
    ) -> str:
        """
        Crea un evento en Google Calendar.
        
        Args:
            titulo: Nombre del evento.
            fecha: Fecha en formato 'YYYY-MM-DD' o lenguaje natural ('mañana').
            hora: Hora en formato 'HH:MM'.
            duracion: Duración en minutos.
            descripcion: Descripción opcional.
        
        Returns:
            ID del evento creado.
        """
        self._ensure_auth()

        # Parsear fecha natural si no es formato ISO
        if fecha and not fecha[0].isdigit():
            parsed = parse_natural_date(fecha)
            if parsed:
                fecha = parsed.strftime("%Y-%m-%d")
            else:
                fecha = datetime.now().strftime("%Y-%m-%d")

        start_str = f"{fecha}T{hora}:00"
        start_dt = datetime.fromisoformat(start_str)
        end_dt = start_dt + timedelta(minutes=duracion)

        event = {
            "summary": titulo,
            "description": descripcion,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": self._timezone,
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": self._timezone,
            },
        }

        result = self._service.events().insert(
            calendarId="primary", body=event
        ).execute()

        event_id = result.get("id", "")
        logger.info(f"Evento creado: '{titulo}' → {fecha} {hora} (ID: {event_id})")
        return event_id

    def list_events(self, fecha: Optional[str] = None, dias: int = 7) -> List[Dict[str, Any]]:
        """
        Lista eventos de los próximos N días.
        
        Args:
            fecha: Fecha inicio (por defecto hoy).
            dias: Número de días a buscar.
        
        Returns:
            Lista de eventos con título, fecha, hora.
        """
        self._ensure_auth()

        if fecha:
            start = datetime.fromisoformat(fecha)
        else:
            start = datetime.now()

        end = start + timedelta(days=dias)

        events_result = self._service.events().list(
            calendarId="primary",
            timeMin=start.isoformat() + "Z",
            timeMax=end.isoformat() + "Z",
            singleEvents=True,
            orderBy="startTime",
            maxResults=20,
        ).execute()

        events = []
        for event in events_result.get("items", []):
            start_info = event.get("start", {})
            events.append({
                "id": event.get("id"),
                "titulo": event.get("summary", "Sin título"),
                "fecha": start_info.get("dateTime", start_info.get("date", "")),
                "descripcion": event.get("description", ""),
            })

        logger.info(f"Se encontraron {len(events)} eventos en los próximos {dias} días.")
        return events

    def update_event(self, event_id: str, **kwargs) -> Dict[str, Any]:
        """Actualiza un evento existente."""
        self._ensure_auth()

        event = self._service.events().get(
            calendarId="primary", eventId=event_id
        ).execute()

        if "titulo" in kwargs:
            event["summary"] = kwargs["titulo"]
        if "descripcion" in kwargs:
            event["description"] = kwargs["descripcion"]

        updated = self._service.events().update(
            calendarId="primary", eventId=event_id, body=event
        ).execute()

        logger.info(f"Evento actualizado: {event_id}")
        return {"id": updated["id"], "titulo": updated.get("summary", "")}

    def delete_event(self, event_id: str) -> bool:
        """Elimina un evento."""
        self._ensure_auth()
        try:
            self._service.events().delete(
                calendarId="primary", eventId=event_id
            ).execute()
            logger.info(f"Evento eliminado: {event_id}")
            return True
        except Exception as e:
            logger.error(f"Error eliminando evento {event_id}: {e}")
            return False

    def get_next_event(self) -> Optional[Dict[str, Any]]:
        """Obtiene el próximo evento."""
        events = self.list_events(dias=7)
        return events[0] if events else None

    def search_events(self, query: str) -> List[Dict[str, Any]]:
        """Busca eventos por texto."""
        self._ensure_auth()

        events_result = self._service.events().list(
            calendarId="primary",
            q=query,
            timeMin=datetime.now().isoformat() + "Z",
            singleEvents=True,
            orderBy="startTime",
            maxResults=10,
        ).execute()

        events = []
        for event in events_result.get("items", []):
            start_info = event.get("start", {})
            events.append({
                "id": event.get("id"),
                "titulo": event.get("summary", "Sin título"),
                "fecha": start_info.get("dateTime", start_info.get("date", "")),
            })

        return events
