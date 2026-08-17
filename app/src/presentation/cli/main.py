from __future__ import annotations

import argparse
import logging
import os
from collections.abc import Sequence

from application.use_cases.process_alert import ProcessAlertResult, ProcessAlertUseCase
from domain.entities.ticket import Ticket, TicketValidationError
from domain.services.alert_message_formatter import AlertMessageFormatter
from infrastructure.adapters.google_chat_webhook import (
    GoogleChatWebhookAdapter,
    WebhookDeliveryError,
)
from infrastructure.adapters.otrs_db_alert_dispatch_ledger import (
    OTRSDatabaseAlertDispatchLedger,
)
from infrastructure.config.settings import Settings
from infrastructure.logging import (
    ALERT_RUN_FAILED,
    ALERT_RUN_FINISHED,
    ALERT_RUN_SKIPPED_DUPLICATE,
    ALERT_RUN_SKIPPED_OUTSIDE_HOURS,
    ALERT_RUN_STARTED,
    log_event,
    truncate_preview,
)
from presentation.logging import attach_daily_stdio, resolve_log_timezone, setup_logging

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="otrs-gchat-alert",
        description="Envia alerta de ticket OTRS para webhook Google Chat",
    )
    parser.add_argument("--ticket-id", type=int, required=True)
    parser.add_argument("--ticket-number", type=str, required=True)
    parser.add_argument("--title", type=str, required=True)
    parser.add_argument("--queue", type=str, required=True)
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ticket_id: int | None = None
    try:
        settings = Settings.from_env()
        if settings.log_dir is not None:
            attach_daily_stdio(
                settings.log_dir,
                resolve_log_timezone(os.environ.get("WINDOW_TIMEZONE")),
            )
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file=settings.log_file,
        )
        ticket = Ticket(
            ticket_id=args.ticket_id,
            ticket_number=args.ticket_number,
            title=args.title,
            queue=args.queue,
        )
        ticket_id = ticket.ticket_id
        log_event(
            logger,
            logging.INFO,
            ALERT_RUN_STARTED,
            ticket_id=ticket.ticket_id,
            ticket_number=ticket.ticket_number,
            title_preview=truncate_preview(ticket.title),
        )
        adapter = GoogleChatWebhookAdapter(
            webhook_url=settings.webhook_url,
            timeout_seconds=settings.http_timeout_seconds,
            ticket_id=ticket.ticket_id,
        )
        dispatch_ledger = None
        if settings.dedup_enabled and settings.otrs_db_ready():
            dispatch_ledger = OTRSDatabaseAlertDispatchLedger(settings.otrs_db_config())
        result = ProcessAlertUseCase(
            notifier=adapter,
            formatter=AlertMessageFormatter(otrs_base_url=settings.otrs_base_url),
            dispatch_ledger=dispatch_ledger,
            dedup_window_minutes=settings.dedup_window_minutes,
            business_hours=settings.business_hours,
        ).execute(ticket)
        if result is ProcessAlertResult.SKIPPED_DUPLICATE:
            log_event(
                logger,
                logging.INFO,
                ALERT_RUN_SKIPPED_DUPLICATE,
                ticket_id=ticket.ticket_id,
                title=ticket.title,
                queue=ticket.queue,
            )
            return 0
        if result is ProcessAlertResult.SKIPPED_OUTSIDE_HOURS:
            log_event(
                logger,
                logging.INFO,
                ALERT_RUN_SKIPPED_OUTSIDE_HOURS,
                ticket_id=ticket.ticket_id,
                title=ticket.title,
                queue=ticket.queue,
            )
            return 0
        log_event(
            logger,
            logging.INFO,
            ALERT_RUN_FINISHED,
            ticket_id=ticket.ticket_id,
            status="ok",
        )
    except (TicketValidationError, ValueError, WebhookDeliveryError) as exc:
        log_event(
            logger,
            logging.ERROR,
            ALERT_RUN_FAILED,
            ticket_id=ticket_id if ticket_id is not None else args.ticket_id,
            status="error",
            error_type=type(exc).__name__,
            exc_info=logger.isEnabledFor(logging.DEBUG),
        )
        return 1
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
