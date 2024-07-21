import sys
import os
import platform
import logging
from PySide6.QtWidgets import QMessageBox


def get_error_report_path():
    system = platform.system()
    home_dir = os.path.expanduser("~")

    if system == "Linux" or system == "Darwin":  # Darwin is macOS
        config_dir = os.path.join(home_dir, '.config', 'iChart')
    elif system == "Windows":
        config_dir = os.path.join(home_dir, 'AppData', 'Local', 'iChart')
    else:
        raise OSError("Unsupported operating system")

    # Ensure the config directory exists
    os.makedirs(config_dir, exist_ok=True)

    return os.path.join(config_dir, 'error_report.log')


def setup_logging():
    # Configure console logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    logger = logging.getLogger('app_logger')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

    return logger


def log_uncaught_exceptions(exctype, value, tb):
    logger = logging.getLogger('app_logger')
    # Add a file handler dynamically when an error occurs
    error_report_path = get_error_report_path()
    file_handler = logging.FileHandler(error_report_path)
    file_handler.setLevel(logging.ERROR)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.error("Uncaught exception", exc_info=(exctype, value, tb))
    QMessageBox.critical(None, "An error occurred", f"An unexpected error occurred. Please share the log file placed in {error_report_path} with the developer.")

    # Remove file handler to avoid duplicate logs in the future
    logger.removeHandler(file_handler)


# Set the custom exception handler
sys.excepthook = log_uncaught_exceptions

# Initialize the logger
logger = setup_logging()
