"""
Unified logging system for UE-traffic simulator with color support
"""
import logging
import sys
from typing import Optional


# ANSI 顏色代碼
class LogColors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # 亮色
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'


class ColoredFormatter(logging.Formatter):
    """自定義帶顏色的日誌格式器"""
    
    # 各等級的顏色配置
    LEVEL_COLORS = {
        logging.DEBUG: LogColors.CYAN,
        logging.INFO: LogColors.GREEN,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.BOLD + LogColors.BRIGHT_RED,
    }
    
    def format(self, record):
        # 獲取對應等級的顏色
        color = self.LEVEL_COLORS.get(record.levelno, LogColors.RESET)
        
        # 格式化日誌
        levelname = f"{color}[{record.levelname}]{LogColors.RESET}"
        message = record.getMessage()
        
        return f"{levelname} {message}"


# 全局 logger 實例
_logger: Optional[logging.Logger] = None


def setup_logger(name: str = "UE-traffic", level: int = logging.INFO) -> logging.Logger:
    """
    設置全局 logger
    
    Args:
        name: logger 名稱
        level: 日誌等級 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        配置好的 logger 實例
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger(name)
    _logger.setLevel(level)
    
    # 移除所有現有的 handlers
    _logger.handlers.clear()
    
    # 創建 console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 創建帶顏色的 formatter
    formatter = ColoredFormatter()
    console_handler.setFormatter(formatter)
    
    # 添加 handler
    _logger.addHandler(console_handler)
    
    # 防止日誌傳播到根 logger
    _logger.propagate = False
    
    return _logger


def get_logger() -> logging.Logger:
    """
    獲取全局 logger 實例
    
    Returns:
        logger 實例
    """
    global _logger
    
    if _logger is None:
        # 如果還沒初始化，使用默認設置
        _logger = setup_logger()
    
    return _logger


def set_log_level(level: int):
    """
    設置日誌等級
    
    Args:
        level: 日誌等級 (logging.DEBUG, logging.INFO, etc.)
    """
    logger = get_logger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


def set_log_level_by_name(level_name: str):
    """
    通過名稱設置日誌等級
    
    Args:
        level_name: 等級名稱 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    level = level_map.get(level_name.upper(), logging.INFO)
    set_log_level(level)
