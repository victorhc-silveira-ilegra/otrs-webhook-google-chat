from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import pymysql
from pymysql.err import IntegrityError

from infrastructure.logging import ALERT_DISPATCH_CLAIM_FAILED, log_event

logger = logging.getLogger(__name__)


def build_dedup_hash(*, title: str, queue_name: str) -> str:
    payload = f"{queue_name}\0{title}".encode()
    return hashlib.sha256(payload).hexdigest()


class OTRSDatabaseAlertDispatchLedger:
    def __init__(self, db_config: dict[str, str | int]) -> None:
        self._db_config = db_config

    def _connect(self) -> Any:
        return pymysql.connect(
            host=str(self._db_config["host"]),
            user=str(self._db_config["user"]),
            password=str(self._db_config["password"]),
            database=str(self._db_config["database"]),
            port=int(self._db_config.get("port", 3306)),
            autocommit=False,
        )

    def try_claim(
        self,
        *,
        ticket_id: int,
        title: str,
        queue_name: str,
        window_minutes: int,
    ) -> bool:
        cutoff_time = datetime.now(UTC) - timedelta(minutes=window_minutes)
        cutoff = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")
        created_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        dedup_hash = build_dedup_hash(title=title, queue_name=queue_name)
        conn: Any = None
        cursor: Any = None
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM gchat_alert_dispatch WHERE created_at < %s",
                (cutoff,),
            )
            cursor.execute(
                "INSERT INTO gchat_alert_dispatch "
                "(ticket_id, dedup_hash, title, queue_name, created_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (ticket_id, dedup_hash, title, queue_name, created_at),
            )
            conn.commit()
            return True
        except IntegrityError:
            if conn is not None:
                conn.rollback()
            return False
        except Exception as err:
            if conn is not None:
                conn.rollback()
            log_event(
                logger,
                logging.WARNING,
                ALERT_DISPATCH_CLAIM_FAILED,
                ticket_id=ticket_id,
                error_type=type(err).__name__,
                exc_info=logger.isEnabledFor(logging.DEBUG),
            )
            return True
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

    def release(self, *, ticket_id: int) -> None:
        conn: Any = None
        cursor: Any = None
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM gchat_alert_dispatch WHERE ticket_id = %s",
                (ticket_id,),
            )
            conn.commit()
        except Exception as err:
            if conn is not None:
                conn.rollback()
            log_event(
                logger,
                logging.WARNING,
                ALERT_DISPATCH_CLAIM_FAILED,
                ticket_id=ticket_id,
                error_type=type(err).__name__,
                exc_info=logger.isEnabledFor(logging.DEBUG),
            )
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()
