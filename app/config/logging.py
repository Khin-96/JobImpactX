import logging
import logging.config
import os
from pythonjsonlogger import jsonlogger

def setup_logging(log_level: str = "INFO"):
    """Configure JSON logging for production."""
    
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(timestamp)s %(level)s %(name)s %(message)s"
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "default": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": "json"
            },
            "file": {
                "level": log_level,
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "json"
            }
        },
        "loggers": {
            "": {
                "handlers": ["default", "file"],
                "level": log_level,
                "propagate": True
            },
            "sqlalchemy.engine": {
                "handlers": ["default"],
                "level": "WARNING"
            }
        }
    }
    
    logging.config.dictConfig(log_config)
    return logging.getLogger(__name__)