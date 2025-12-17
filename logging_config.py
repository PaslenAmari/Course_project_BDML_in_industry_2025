
"""
Centralized logging configuration for Language Learning Platform
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Setup a logger with both file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional specific log file name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    
    if log_file is None:
        log_file = f"{name.replace('.', '_')}.log"
    
    log_path = LOGS_DIR / log_file
    
    
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path,
        maxBytes=10 * 1024 * 1024,  
        backupCount=5,  
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        fmt='[%(levelname)s] %(name)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def setup_error_logger() -> logging.Logger:
    """Setup dedicated error logger"""
    logger = logging.getLogger("errors")
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.ERROR)
    
    error_handler = logging.handlers.RotatingFileHandler(
        filename=LOGS_DIR / "errors.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s | %(pathname)s:%(lineno)d',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_formatter)
    
    logger.addHandler(error_handler)
    
    return logger



app_logger = setup_logger("app", "app.log")
tutor_logger = setup_logger("tutor_agent", "tutor_agent.log")
planner_logger = setup_logger("curriculum_planner", "planner_agent.log")
database_logger = setup_logger("database", "database.log")
error_logger = setup_error_logger()
