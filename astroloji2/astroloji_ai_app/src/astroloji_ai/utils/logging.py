from typing import Any, Dict

import structlog
import logging
from logging.config import dictConfig


def configure_logging(log_level: str) -> None:
    dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': log_level.upper(),
            },
        },
        'loggers': {
            'astroloji_ai': {
                'handlers': ['console'],
                'level': log_level.upper(),
                'propagate': False,
            },
        },
    })


def bind_request(logger: structlog.stdlib.BoundLogger, **kwargs: Any) -> structlog.stdlib.BoundLogger:
    return logger.bind(**kwargs)