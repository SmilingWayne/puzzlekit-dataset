# puzzle_scraper/logger.py  
"""Log configuration."""  
  
import logging  
import sys  
from datetime import datetime  
  
  
def setup_logger(name: str, log_file: str = None) -> logging.Logger:  
    """  
    Setup and return logger  
      
    Args:  
        name: logger name.  
        log_file: Log file path.
      
    Returns:  
    """  
    logger = logging.getLogger(name)  
    logger.setLevel(logging.DEBUG)  
      
    logger.handlers.clear()  
      
    console_handler = logging.StreamHandler(sys.stdout)  
    console_handler.setLevel(logging.INFO)  
    console_format = logging.Formatter(  
        '%(asctime)s | %(levelname)-8s | %(message)s',  
        datefmt='%H:%M:%S'  
    )  
    console_handler.setFormatter(console_format)  
    logger.addHandler(console_handler)  
      
    if log_file:  
        file_handler = logging.FileHandler(log_file, encoding='utf-8')  
        file_handler.setLevel(logging.DEBUG)  
        file_format = logging.Formatter(  
            '%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',  
            datefmt='%Y-%m-%d %H:%M:%S'  
        )  
        file_handler.setFormatter(file_format)  
        logger.addHandler(file_handler)  
      
    return logger  
  
  
def get_log_filename(puzzle_name: str) -> str:  
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  
    return f"logs/{puzzle_name}_{timestamp}.log"  
