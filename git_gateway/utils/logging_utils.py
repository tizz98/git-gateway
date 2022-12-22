"""Utilities for structured logging.
"""

import logging
import sys

import structlog
from structlog.contextvars import merge_contextvars


def rename_event_key(logger, method_name, event_dict):
    """Renames the `event` key to `message`

    This helper function renames the `event` key in structured logging
    entries to `message` key which conforms to Datadog's default
    attribute for log message text.
    """
    event_dict["message"] = event_dict.pop("event")
    return event_dict


def configure_logging() -> None:
    """A helper function to configure structured logging and root logger"""
    dev_logging = True
    shared_processors = [
        merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if dev_logging:
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()
        shared_processors.append(rename_event_key)

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer, foreign_pre_chain=shared_processors
    )

    structlog_processors = [
        structlog.stdlib.filter_by_level,
        *shared_processors,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    structlog.configure(
        processors=structlog_processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel("INFO")
    root_logger.handlers = []
    root_logger.addHandler(handler)
