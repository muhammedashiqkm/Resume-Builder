import logging
from logging.handlers import RotatingFileHandler
import os


LOGS_DIRS = "logs"
if not os.path.exists(LOGS_DIRS):
    os.makedirs(LOGS_DIRS)


log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def setup_handler(logger_name: str, log_file: str, level=logging.INFO):
    handler = RotatingFileHandler(
        os.path.join(LOGS_DIRS, log_file),
        maxBytes=1024*1024*5,
        backupCount=5
    )
    handler.setFormatter(log_formatter)

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

app_logger = setup_handler('app', 'app.log')
error_logger = setup_handler('error', 'error.log')
access_logger = setup_handler('access', 'access.log')
security_logger = setup_handler('security', 'security')