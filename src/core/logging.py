"""
Logging configuration for the SchoolConnect-AI unified backend.
"""

import logging
import sys
from typing import Optional

from src.core.config import get_settings

def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        log_level: Optional override for log level from settings
        
    Returns:
        Logger instance for the application
    """
    settings = get_settings()
    level = log_level or settings.LOG_LEVEL
    
    # Create logger
    logger = logging.getLogger("schoolconnect_ai")
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create file handler
    file_handler = logging.FileHandler("app.log", mode="a")
    file_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        "\n%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Add formatter to handlers
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Force all loggers to use the same handlers
    for handler in logging.getLogger().handlers:
        logging.getLogger('werkzeug').addHandler(handler)
        logging.getLogger('urllib3').addHandler(handler)
    
    return logger
