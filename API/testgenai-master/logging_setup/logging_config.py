"""
Logging Configuration for DataSense Application
Provides structured logging with file rotation and multiple log levels
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'question_id'):
            log_data['question_id'] = record.question_id
        if hasattr(record, 'execution_time'):
            log_data['execution_time_ms'] = record.execution_time
        if hasattr(record, 'endpoint'):
            log_data['endpoint'] = record.endpoint
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'client_ip'):
            log_data['client_ip'] = record.client_ip

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_json: bool = True,
    enable_colored_console: bool = True
):
    """
    Setup comprehensive logging configuration

    Args:
        log_dir: Directory to store log files
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Whether to log to console
        enable_json: Whether to use JSON formatting for file logs
        enable_colored_console: Whether to use colored output in console
    """

    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # ========================================================================
    # File Handlers
    # ========================================================================

    # 1. General Application Log (Rotating)
    app_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / 'datasense.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)

    if enable_json:
        app_handler.setFormatter(JSONFormatter())
    else:
        app_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

    root_logger.addHandler(app_handler)

    # 2. Error Log (Only errors and critical)
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / 'error.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)

    if enable_json:
        error_handler.setFormatter(JSONFormatter())
    else:
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'File: %(pathname)s:%(lineno)d\n'
            'Function: %(funcName)s\n'
        ))

    root_logger.addHandler(error_handler)

    # 3. API Request/Response Log
    api_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / 'api_requests.log',
        maxBytes=20 * 1024 * 1024,  # 20MB
        backupCount=10,
        encoding='utf-8'
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(JSONFormatter())

    # Create API logger
    api_logger = logging.getLogger('api')
    api_logger.setLevel(logging.INFO)
    api_logger.addHandler(api_handler)
    api_logger.propagate = False  # Don't propagate to root

    # 4. SQL Query Log
    sql_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / 'sql_queries.log',
        maxBytes=15 * 1024 * 1024,  # 15MB
        backupCount=7,
        encoding='utf-8'
    )
    sql_handler.setLevel(logging.DEBUG)
    sql_handler.setFormatter(JSONFormatter())

    # Create SQL logger
    sql_logger = logging.getLogger('sql')
    sql_logger.setLevel(logging.DEBUG)
    sql_logger.addHandler(sql_handler)
    sql_logger.propagate = False

    # 5. Performance/Metrics Log
    perf_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / 'performance.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(JSONFormatter())

    # Create performance logger
    perf_logger = logging.getLogger('performance')
    perf_logger.setLevel(logging.INFO)
    perf_logger.addHandler(perf_handler)
    perf_logger.propagate = False

    # ========================================================================
    # Console Handler
    # ========================================================================

    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        if enable_colored_console:
            console_handler.setFormatter(ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
        else:
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))

        root_logger.addHandler(console_handler)

    # ========================================================================
    # Configure Third-Party Library Loggers
    # ========================================================================

    # Reduce noise from verbose libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)

    # Log startup message
    logging.info("=" * 60)
    logging.info("DataSense Logging System Initialized")
    logging.info(f"Log Directory: {log_path.absolute()}")
    logging.info(f"Log Level: {log_level}")
    logging.info(f"JSON Formatting: {enable_json}")
    logging.info("=" * 60)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module

    Usage:
        from config.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("This is a log message")
    """
    return logging.getLogger(name)


# Specialized logger helpers
def get_api_logger() -> logging.Logger:
    """Get logger for API requests/responses"""
    return logging.getLogger('api')


def get_sql_logger() -> logging.Logger:
    """Get logger for SQL queries"""
    return logging.getLogger('sql')


def get_performance_logger() -> logging.Logger:
    """Get logger for performance metrics"""
    return logging.getLogger('performance')


# Example usage functions
def log_api_request(
    endpoint: str,
    method: str,
    client_ip: str,
    user_id: int = None,
    status_code: int = None,
    execution_time: float = None
):
    """Log API request with structured data"""
    logger = get_api_logger()
    logger.info(
        f"{method} {endpoint}",
        extra={
            'endpoint': endpoint,
            'method': method,
            'client_ip': client_ip,
            'user_id': user_id,
            'status_code': status_code,
            'execution_time': execution_time
        }
    )


def log_sql_query(
    query: str,
    execution_time: float = None,
    rows_affected: int = None,
    user_id: int = None,
    question_id: str = None,
    error: str = None
):
    """Log SQL query execution"""
    logger = get_sql_logger()

    log_level = logging.ERROR if error else logging.INFO

    logger.log(
        log_level,
        f"SQL Query Executed: {query[:100]}...",
        extra={
            'query': query,
            'execution_time': execution_time,
            'rows_affected': rows_affected,
            'user_id': user_id,
            'question_id': question_id,
            'error': error
        }
    )


def log_performance_metric(
    operation: str,
    duration_ms: float,
    metadata: dict = None
):
    """Log performance metrics"""
    logger = get_performance_logger()

    extra = {
        'operation': operation,
        'duration_ms': duration_ms
    }

    if metadata:
        extra.update(metadata)

    logger.info(f"Performance: {operation}", extra=extra)


# Initialize logging on module import (optional)
# Uncomment to auto-initialize with defaults
# setup_logging()
