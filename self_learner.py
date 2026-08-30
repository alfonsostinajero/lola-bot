"""
self_learner.py — Módulo de auto-aprendizaje para Lola AI
Registra interacciones, detecta patrones y aprende del usuario.
Usa SQLite para almacenamiento persistente y ligero.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import config

logger = logging.getLogger("Lola.Learner")


class SelfLearner:
    """
    Sistema de auto-aprendizaje que mejora a Lola con cada interacción.

    Funcionalidades:
    - Registra todas las interacciones (entrada, respuesta, éxito/fallo)
    - Detecta patrones de uso y preferencias
    - Aprende correcciones automáticamente (después de 3 correcciones iguales)
    - Enriquece el prompt del AI Engine con contexto aprendido
    """

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or config.DB_PATH
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    # ── Base de datos ────────────────────────────────────────

    def _init_db(self) -> None:
        """Inicializa la base de datos SQLite con el esquema completo."""
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        cursor = self._conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_input TEXT NOT NULL,
                ai_response TEXT,
                action_type TEXT,
                action_data TEXT,
                success BOOLEAN DEFAULT 1,
                feedback TEXT,
                execution_time_ms INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_input TEXT NOT NULL,
                corrected_action TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_interactions_timestamp
                ON interactions(timestamp);
            CREATE INDEX IF NOT EXISTS idx_interactions_action_type
                ON interactions(action_type);
            CREATE INDEX IF NOT EXISTS idx_corrections_input
                ON corrections(original_input);
        """)
        self._conn.commit()
        logger.info(f"Base de datos de aprendizaje inicializada: {self._db_path}")

    # ── Registro de interacciones ────────────────────────────

    def log_interaction(
        self,
        user_input: str,
        ai_response: str,
        action_taken: str,
        success: bool,
        feedback: Optional[str] = None,
        execution_time_ms: int = 0,
    ) -> None:
        """Registra una interacción completa."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO interactions
                (user_input, ai_response, action_type, success, feedback, execution_time_ms)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_input, ai_response, action_taken, success, feedback, execution_time_ms),
        )
        self._conn.commit()

        if not success and feedback:
            self._update_corrections(user_input, feedback)

        logger.debug(
            f"Interacción registrada: '{user_input[:50]}' → {action_taken} "
            f"({'✓' if success else '✗'}) [{execution_time_ms}ms]"
        )

    def _update_corrections(self, original_input: str, corrected_action: str) -> None:
        """Actualiza correcciones y aprende si se repiten."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT id, frequency FROM corrections WHERE original_input = ? AND corrected_action = ?",
            (original_input, corrected_action),
        )
        row = cursor.fetchone()

        if row:
            new_freq = row["frequency"] + 1
            cursor.execute(
                "UPDATE corrections SET frequency = ? WHERE id = ?",
                (new_freq, row["id"]),
            )
            if new_freq >= config.CORRECTION_THRESHOLD:
                self._auto_learn_pattern(original_input, corrected_action)
                logger.info(
                    f"¡Patrón aprendido automáticamente! '{original_input}' → '{corrected_action}'"
                )
        else:
            cursor.execute(
                "INSERT INTO corrections (original_input, corrected_action) VALUES (?, ?)",
                (original_input, corrected_action),
            )
        self._conn.commit()

    def _auto_learn_pattern(self, input_text: str, action: str) -> None:
        """Crea un patrón aprendido automáticamente."""
        pattern_data = json.dumps(
            {"input": input_text, "learned_action": action}, ensure_ascii=False,
        )
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO patterns (pattern_type, pattern_data, confidence) VALUES ('auto_correction', ?, 1.0)",
            (pattern_data,),
        )
        self._conn.commit()

    # ── Preferencias ─────────────────────────────────────────

    def learn_preference(self, key: str, value: Any) -> None:
        """Almacena o actualiza una preferencia del usuario."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO preferences (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, json.dumps(value, ensure_ascii=False)),
        )
        self._conn.commit()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Obtiene una preferencia del usuario."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
        row = cursor.fetchone()
        return json.loads(row["value"]) if row else default

    # ── Análisis ─────────────────────────────────────────────

    def get_patterns(self, pattern_type: str) -> List[Dict[str, Any]]:
        """Obtiene patrones aprendidos por tipo."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM patterns WHERE pattern_type = ? ORDER BY confidence DESC",
            (pattern_type,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def analyze_failures(self) -> List[Dict[str, Any]]:
        """Analiza interacciones fallidas recientes para detectar problemas."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT action_type, COUNT(*) as count,
                   GROUP_CONCAT(feedback, ' | ') as feedbacks
            FROM interactions
            WHERE success = 0 AND timestamp > datetime('now', '-7 days')
            GROUP BY action_type
            ORDER BY count DESC
            LIMIT 10
            """
        )
        return [dict(row) for row in cursor.fetchall()]

    def suggest_improvements(self) -> List[str]:
        """Genera sugerencias de mejora basadas en el análisis de datos."""
        suggestions = []
        failures = self.analyze_failures()

        for f in failures:
            if f["count"] >= 3:
                suggestions.append(
                    f"La acción '{f['action_type']}' ha fallado {f['count']} veces. "
                    f"Feedbacks: {f['feedbacks'][:200]}"
                )

        rate = self.get_success_rate()
        if rate < 0.7:
            suggestions.append(
                f"Tasa de éxito general baja ({rate:.0%}). "
                "Considerar revisión del system prompt o action_executor."
            )

        return suggestions if suggestions else ["Todo funciona bien. Sin sugerencias de mejora."]

    def get_context_enrichment(self, user_input: str) -> Dict[str, Any]:
        """Obtiene contexto enriquecido para el AI Engine."""
        context = {}

        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT corrected_action FROM corrections
            WHERE original_input LIKE ? AND frequency >= ?
            ORDER BY frequency DESC LIMIT 3
            """,
            (f"%{user_input}%", config.CORRECTION_THRESHOLD),
        )
        corrections = [row["corrected_action"] for row in cursor.fetchall()]
        if corrections:
            context["learned_corrections"] = corrections

        cursor.execute(
            """
            SELECT ai_response, action_type FROM interactions
            WHERE user_input LIKE ? AND success = 1
            ORDER BY timestamp DESC LIMIT 3
            """,
            (f"%{user_input[:30]}%",),
        )
        past = [
            {"response": row["ai_response"][:200], "type": row["action_type"]}
            for row in cursor.fetchall()
        ]
        if past:
            context["past_successes"] = past

        all_prefs = self._get_all_preferences()
        if all_prefs:
            context["preferences"] = all_prefs

        return context

    def _get_all_preferences(self) -> Dict[str, Any]:
        """Obtiene todas las preferencias."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT key, value FROM preferences")
        return {row["key"]: json.loads(row["value"]) for row in cursor.fetchall()}

    def build_dynamic_prompt_additions(self) -> str:
        """Construye texto adicional para el system prompt basado en aprendizaje."""
        parts = []

        prefs = self._get_all_preferences()
        if prefs:
            parts.append("Preferencias del usuario: " + json.dumps(prefs, ensure_ascii=False))

        patterns = self.get_patterns("auto_correction")
        if patterns:
            corrections_text = []
            for p in patterns[:5]:
                data = json.loads(p["pattern_data"])
                corrections_text.append(
                    f"- Cuando diga '{data['input']}', hacer: {data['learned_action']}"
                )
            parts.append("Correcciones aprendidas:\n" + "\n".join(corrections_text))

        return "\n".join(parts) if parts else ""

    def get_success_rate(self, action_type: Optional[str] = None) -> float:
        """Calcula la tasa de éxito."""
        cursor = self._conn.cursor()
        if action_type:
            cursor.execute(
                "SELECT COUNT(*) as total, SUM(success) as ok FROM interactions WHERE action_type = ?",
                (action_type,),
            )
        else:
            cursor.execute("SELECT COUNT(*) as total, SUM(success) as ok FROM interactions")

        row = cursor.fetchone()
        total = row["total"]
        ok = row["ok"] or 0
        return ok / total if total > 0 else 1.0

    # ── Exportar / Importar ──────────────────────────────────

    def export_knowledge(self) -> Dict[str, Any]:
        """Exporta toda la base de conocimientos."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM preferences")
        prefs = [dict(row) for row in cursor.fetchall()]
        cursor.execute("SELECT * FROM patterns")
        patterns = [dict(row) for row in cursor.fetchall()]
        cursor.execute("SELECT * FROM corrections WHERE frequency >= 2")
        corrections = [dict(row) for row in cursor.fetchall()]
        return {"preferences": prefs, "patterns": patterns, "corrections": corrections}

    def import_knowledge(self, data: Dict[str, Any]) -> bool:
        """Importa una base de conocimientos."""
        try:
            for pref in data.get("preferences", []):
                self.learn_preference(pref["key"], json.loads(pref["value"]))
            logger.info("Conocimiento importado correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error importando conocimiento: {e}")
            return False

    # ── Mantenimiento ────────────────────────────────────────

    def periodic_cleanup(self, days: Optional[int] = None) -> int:
        """Limpia datos antiguos. Retorna cantidad de registros eliminados."""
        days = days or config.LEARNING_CLEANUP_DAYS
        cursor = self._conn.cursor()
        cursor.execute(
            "DELETE FROM interactions WHERE timestamp < datetime('now', ?)",
            (f"-{days} days",),
        )
        deleted = cursor.rowcount
        self._conn.commit()
        if deleted:
            logger.info(f"Limpieza: {deleted} interacciones antiguas eliminadas.")
        return deleted

    def close(self) -> None:
        """Cierra la conexión a la base de datos."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __del__(self):
        self.close()
