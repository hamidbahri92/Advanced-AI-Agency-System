import logging
import sys
from pathlib import Path
from typing import Optional

from ..config import Config

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger.
    
    Args:
        name: Name for the logger
        level: Logging level (defaults to Config.LOG_LEVEL)
    
    Returns:
        Configured logger
    """
    # Use configured log level if none provided
    if level is None:
        level = Config.LOG_LEVEL
    
    # Create the logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Check if the logger already has handlers
    if logger.handlers:
        return logger
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create log directory if it doesn't exist
    log_dir = Config.LOG_DIR
    log_dir.mkdir(exist_ok=True)
    
    # Create file handler
    file_handler = logging.FileHandler(log_dir / f"{name.split('.')[-1]}.log")
    file_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set formatter for handlers
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
