# puzzle_scraper/logger.py  
"""日志配置模块"""  
  
import logging  
import sys  
from datetime import datetime  
  
  
def setup_logger(name: str, log_file: str = None) -> logging.Logger:  
    """  
    设置并返回一个配置好的 logger  
      
    Args:  
        name: logger 名称  
        log_file: 日志文件路径，如果为 None 则只输出到控制台  
      
    Returns:  
        配置好的 Logger 实例  
    """  
    logger = logging.getLogger(name)  
    logger.setLevel(logging.DEBUG)  
      
    # 清除已有的 handlers  
    logger.handlers.clear()  
      
    # 控制台 handler  
    console_handler = logging.StreamHandler(sys.stdout)  
    console_handler.setLevel(logging.INFO)  
    console_format = logging.Formatter(  
        '%(asctime)s | %(levelname)-8s | %(message)s',  
        datefmt='%H:%M:%S'  
    )  
    console_handler.setFormatter(console_format)  
    logger.addHandler(console_handler)  
      
    # 文件 handler（如果指定了日志文件）  
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
    """生成带时间戳的日志文件名"""  
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  
    return f"logs/{puzzle_name}_{timestamp}.log"  
