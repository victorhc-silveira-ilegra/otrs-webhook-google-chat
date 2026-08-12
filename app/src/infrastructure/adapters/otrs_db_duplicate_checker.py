from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import pymysql

from infrastructure.logging import ALERT_DEDUP_CHECK_FAILED, log_event

logger = logging.getLogger(__name__)


class OTRSDatabaseDuplicateChecker:
    def __init__(self, db_config: dict[str, str | int]) -> None:
        self._db_config = db_config

    def is_duplicate(
        self,
        *,
        title: str,
        queue_name: str,
        window_minutes: int,
        exclude_ticket_id: int,
    ) -> bool:
        cutoff_time = datetime.now(UTC) - timedelta(minutes=window_minutes)
        query = (
            "SELECT COUNT(*) "
            "FROM ticket t "
            "JOIN queue q ON t.queue_id = q.id "
            "WHERE t.title = %s "
            "AND q.name = %s "
            "AND t.create_time >= %s "
            "AND t.id <> %s "
            "AND t.ticket_state_id IN (1, 4)"
        )
        conn: Any = None
        cursor: Any = None
        try:
            conn = pymysql.connect(
                host=str(self._db_config["host"]),
                user=str(self._db_config["user"]),
                password=str(self._db_config["password"]),
                database=str(self._db_config["database"]),
                port=int(self._db_config.get("port", 3306)),
            )
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    title,
                    queue_name,
                    cutoff_time.strftime("%Y-%m-%d %H:%M:%S"),
                    exclude_ticket_id,
                ),
            )
            row = cursor.fetchone()
            count = int(row[0]) if row is not None else 0
            return count > 0
        except Exception as err:
            log_event(
                logger,
                logging.WARNING,
                ALERT_DEDUP_CHECK_FAILED,
                ticket_id=exclude_ticket_id,
                error_type=type(err).__name__,
                exc_info=logger.isEnabledFor(logging.DEBUG),
            )
            return False
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()
