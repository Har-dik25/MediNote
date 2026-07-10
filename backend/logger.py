"""
MediMate — Structured Logging
==============================
Centralized logging module with structured JSON-style logging.
Provides request tracing (timestamp, input hash, model response time).
"""

import logging
import hashlib
import time
import functools
from datetime import datetime


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Creates a configured logger with a consistent format.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.setLevel(level)
    return logger


def hash_input(text: str) -> str:
    """Generate a short hash of the input for tracing without storing PHI."""
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def log_request(logger: logging.Logger, action: str, input_text: str, **kwargs):
    """
    Log a structured request entry.
    
    Args:
        logger: Logger instance
        action: Action name (e.g., 'generate_soap', 'search_guidelines')
        input_text: The input text (will be hashed for privacy)
        **kwargs: Additional key-value pairs to log
    """
    extras = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    logger.info(
        f"ACTION={action} | input_hash={hash_input(input_text)} | "
        f"timestamp={datetime.utcnow().isoformat()}Z"
        + (f" | {extras}" if extras else "")
    )


def log_response(logger: logging.Logger, action: str, elapsed_ms: float, success: bool, **kwargs):
    """
    Log a structured response entry.
    
    Args:
        logger: Logger instance
        action: Action name
        elapsed_ms: Time taken in milliseconds
        success: Whether the action succeeded
        **kwargs: Additional key-value pairs to log
    """
    extras = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    level = logging.INFO if success else logging.ERROR
    logger.log(
        level,
        f"RESPONSE={action} | elapsed_ms={elapsed_ms:.1f} | success={success}"
        + (f" | {extras}" if extras else "")
    )


def timed(logger: logging.Logger, action: str):
    """
    Decorator that logs the execution time and success/failure of a function.
    
    Usage:
        @timed(logger, "generate_soap")
        def generate_soap_note(transcript):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start) * 1000
                log_response(logger, action, elapsed, success=True)
                return result
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                log_response(logger, action, elapsed, success=False, error=str(e))
                raise
        return wrapper
    return decorator
