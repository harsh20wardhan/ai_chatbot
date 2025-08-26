"""
Centralized Logging Configuration

Provides structured logging with correlation IDs and proper formatting
for debugging and monitoring.
"""

import logging
import logging.config
import sys
import os
from datetime import datetime
from typing import Dict, Any

def setup_logging(log_level: str = "INFO"):
    """Setup centralized logging configuration"""
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Custom formatter that includes correlation ID if available
    class CorrelationFormatter(logging.Formatter):
        def format(self, record):
            # Add correlation ID if available in extra
            correlation_id = getattr(record, 'correlation_id', None)
            if correlation_id:
                record.correlation_id = f"[{correlation_id[:8]}]"
            else:
                record.correlation_id = ""
            
            return super().format(record)
    
    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                '()': CorrelationFormatter,
                'format': '%(asctime)s - %(name)s - %(levelname)s %(correlation_id)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'detailed',
                'stream': sys.stdout
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': 'logs/fastapi_backend.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': 'logs/errors.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'file', 'error_file'],
                'level': 'DEBUG',
                'propagate': False
            },
            'uvicorn': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False
            },
            'uvicorn.access': {
                'handlers': ['file'],
                'level': 'INFO',
                'propagate': False
            },
            'asyncpg': {
                'handlers': ['file'],
                'level': 'WARNING',
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Log files: logs/fastapi_backend.log, logs/errors.log")

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)

def log_service_call(logger: logging.Logger, service_name: str, method_name: str, **kwargs):
    """Log a service method call with parameters"""
    logger.info(
        f"Service call: {service_name}.{method_name}",
        extra={
            "service": service_name,
            "method": method_name,
            "parameters": kwargs
        }
    )

def log_service_result(logger: logging.Logger, service_name: str, method_name: str, success: bool, **kwargs):
    """Log a service method result"""
    level = logging.INFO if success else logging.ERROR
    status = "SUCCESS" if success else "FAILED"
    
    logger.log(
        level,
        f"Service result: {service_name}.{method_name} - {status}",
        extra={
            "service": service_name,
            "method": method_name,
            "success": success,
            **kwargs
        }
    )

def log_database_operation(logger: logging.Logger, operation: str, table: str, **kwargs):
    """Log a database operation"""
    logger.debug(
        f"Database operation: {operation} on {table}",
        extra={
            "operation": operation,
            "table": table,
            **kwargs
        }
    )

def log_external_service_call(logger: logging.Logger, service: str, endpoint: str, **kwargs):
    """Log an external service call"""
    logger.info(
        f"External service call: {service} - {endpoint}",
        extra={
            "external_service": service,
            "endpoint": endpoint,
            **kwargs
        }
    )