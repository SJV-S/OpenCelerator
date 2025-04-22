import sys
import platform
import logging
import traceback
from pathlib import Path
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout, QApplication
from PySide6.QtCore import Qt


def get_error_report_path():
    system = platform.system()
    home_dir = Path.home()

    if system == "Linux" or system == "Darwin":  # Darwin is macOS
        config_dir = home_dir / '.config' / 'OpenCelerator'
    elif system == "Windows":
        config_dir = home_dir / 'AppData' / 'Local' / 'OpenCelerator'
    else:
        raise OSError("Unsupported operating system")

    # Ensure the config directory exists
    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir / 'error_report.log'


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


class ErrorDialog(QDialog):
    def __init__(self, error_message, error_report_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("An error occurred")
        self.setFixedWidth(550)
        self.setFixedHeight(400)

        self.error_message = error_message
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # Combine all text into a single top label for easier editing
        combined_text = (
            "An error has occurred.\n"
            "Please copy and send to: opencelerator.9qpel@simplelogin.com\n"
            f"All error reports are saved here: {str(error_report_path)}\n"
            "\nTechnical details:"
        )
        top_label = QLabel(combined_text)
        top_label.setWordWrap(True)
        top_label.setStyleSheet("font-style: normal;")
        top_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(top_label, 0)  # 0 stretch factor

        # Error text area (scrollable and selectable)
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setText(error_message)
        self.error_text.setMinimumHeight(100)
        layout.addWidget(self.error_text, 1)  # 1 stretch factor - this will expand

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        # Copy button
        copy_button = QPushButton("Copy Error to Clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        copy_button.setStyleSheet("font-style: normal;")
        button_layout.addWidget(copy_button)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("font-style: normal;")
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout, 0)  # 0 stretch factor
        self.setLayout(layout)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.error_message)


def log_uncaught_exceptions(exctype, value, tb):
    logger = logging.getLogger('app_logger')
    # Add a file handler dynamically when an error occurs
    error_report_path = get_error_report_path()
    file_handler = logging.FileHandler(error_report_path)
    file_handler.setLevel(logging.ERROR)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Format the error traceback as a string
    error_message = ''.join(traceback.format_exception(exctype, value, tb))

    # Log to file
    logger.error("Uncaught exception", exc_info=(exctype, value, tb))

    # Show the custom dialog directly
    dialog = ErrorDialog(error_message, error_report_path)
    dialog.exec()

    # Remove file handler to avoid duplicate logs in the future
    logger.removeHandler(file_handler)


# Set the custom exception handler
sys.excepthook = log_uncaught_exceptions

# Initialize the logger
logger = setup_logging()
