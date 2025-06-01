# Standard library imports
import io
import sys
import json
import time
import re
import copy
import platform
import logging
import traceback
import textwrap
import inspect
import zipfile
import importlib.util
import hashlib
import warnings
import requests
import tempfile
from pathlib import Path
from os import environ
from datetime import datetime
from urllib.parse import urlparse, unquote
from threading import Thread
import sqlite3

# External modules
import numpy as np
import pandas as pd
import matplotlib
import pgpy
import colorsys

# PySide6 GUI implementation
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QFrame, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QUrl
from PySide6.QtGui import QFont, QDesktopServices, QPixmap, QIcon, QPainter, QColor
from resources.resources_rc import *

# Fingerprint: 7621B7F1341F46231C2410A9BB1FEF6686C62068
PUBLIC_KEY = """-----BEGIN PGP PUBLIC KEY BLOCK-----

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
=0ass
-----END PGP PUBLIC KEY BLOCK-----
"""


def get_config_directory():
    system = platform.system()
    home_dir = Path.home()

    if system == "Linux" or system == "Darwin":  # Darwin is macOS
        config_dir = home_dir / '.config' / f'{APP_NAME}'
    elif system == "Windows":
        config_dir = home_dir / 'AppData' / 'Local' / f'{APP_NAME}'
    else:
        logger.warning(f"Unsupported operating system: {system}")
        config_dir = home_dir / f'.{APP_NAME}'  # Fallback

    return config_dir


# Parameters
DEBUGGING = True
LAUNCHER_ENVIRONMENT = '0.12.0'
APP_ZIP_FILENAME = "app_modules"
MAIN_MODULE_NAME = "app"
APP_NAME = 'OpenCelerator'
GITHUB_REPO = f"https://github.com/SJV-S/{APP_NAME}"
CONFIG_DIR = get_config_directory()
MESSAGES = {
    "DOWNLOAD_PERMISSION": f"Welcome to {APP_NAME}. The latest version will be downloaded. Would you like to continue? Manage update settings in the Config tab.",
    "UPDATE_AVAILABLE": "Version {} has been released. Download?",
    "DOWNLOAD_FAILED": "Failed to download or verify the update. Please try again later.",
    "NO_UPDATES": "No updates found or error checking for updates.",
    "ERROR_OCCURRED": "An error occurred: {}",
    "PREPARING_DOWNLOAD": "Preparing to download...",
    "DOWNLOADING_UPDATE": "Downloading update...",
    "DOWNLOADING_PROGRESS": "Downloading: {:.1f}%",
    "DOWNLOADING_SIGNATURE": "Downloading signature...",
    "VERIFYING_DOWNLOAD": "Verifying download...",
    "ENVIRONMENT_MISMATCH": f"The app needs to be updated manually. Please download a new version:"
}

#  PGPy warnings - not relevant for signature verification:
# - Using known trusted public key, not parsing unknown keys
# - Security handled via launcher updates, not revocation
# - Only using signature verification, usage flags irrelevant
warnings.filterwarnings("ignore", category=UserWarning, module="pgpy")


class Logger:
    def __init__(self, name=f"{APP_NAME}", level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Check if handlers are already configured to avoid duplicates
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)

            # Format for console output
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            console_handler.setFormatter(formatter)

            # Add handler to logger
            self.logger.addHandler(console_handler)

    # Convenience methods for different log levels
    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)

    def exception(self, msg):
        self.logger.exception(msg)

    def set_level(self, level):
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)


# Initialize global logger
logger = Logger()


def download_file_with_progress(url, destination, progress_callback=None):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0

        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size and progress_callback:
                        progress = (downloaded / total_size) * 100
                        progress_callback(MESSAGES["DOWNLOADING_PROGRESS"].format(progress))

        return True
    except Exception as e:
        logger.error(f"Error downloading file from {url}: {e}")
        return False


class ModuleVerifier:
    def calculate_file_hash(self, file_path):
        hash_obj = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                # Read the file in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return None

    def verify_module_integrity(self, module_path, version_str=None):
        # Calculate initial file hash
        file_hash = self.calculate_file_hash(module_path)
        if file_hash is None:
            logger.error("Failed to calculate initial file hash!")
            return False, None

        logger.info("\n==== STARTING PGP SIGNATURE VERIFICATION ====")
        logger.info(f"Module to verify: {module_path}")
        if version_str:
            logger.info(f"Module version: v{version_str}")
        logger.info(f"Initial file hash (SHA-256): {file_hash}")

        try:
            # File paths
            module_path = Path(module_path)
            sig_file = Path(f"{module_path}.sig")

            # Verify signature file exists
            if not sig_file.exists():
                logger.error(f"Signature file {sig_file} not found!")
                return False, None
            logger.info(f"Found signature file: {sig_file}")

            # Import the public key
            try:
                # Use the parse method that worked in debug
                key = pgpy.PGPKey()
                key.parse(PUBLIC_KEY)
                logger.info(f"Successfully imported public key: {key.fingerprint}")
            except Exception as e:
                logger.error(f"Failed to parse public key: {e}")
                return False, None

            # Read the file to be verified
            try:
                with open(module_path, 'rb') as f:
                    file_data = f.read()
                logger.info(f"Read {len(file_data)} bytes from file")
            except Exception as e:
                logger.error(f"Failed to read file: {e}")
                return False, None

            # Read and parse the signature - use ASCII mode as shown in debug output
            try:
                with open(sig_file, 'r') as f:  # Open as text, not binary
                    sig_content = f.read()

                # Use the method that worked in debug output
                signature = pgpy.PGPSignature.from_blob(sig_content)
                logger.info("Successfully parsed signature")
            except Exception as e:
                logger.error(f"Failed to parse signature: {e}")
                return False, None

            # Verify the signature
            try:
                # Handle the "No signatures to verify" error properly
                try:
                    verified = key.verify(file_data, signature)
                    if verified:
                        logger.info("SIGNATURE VERIFICATION SUCCESSFUL!")
                        return True, file_hash
                    else:
                        logger.info("Signature verification failed: Invalid signature")
                        return False, None
                except pgpy.errors.PGPError as pgp_err:
                    if "No signatures to verify" in str(pgp_err):
                        # This means it's a valid signature but from a different key
                        logger.error("Signature exists but was created with a different key")
                        return False, None
                    else:
                        raise
            except Exception as e:
                logger.error(f"ERROR during verification: {e}")
                return False, None

        except Exception as e:
            logger.critical(f"CRITICAL ERROR during signature verification: {e}")
            return False, None
        finally:
            logger.info("==== PGP SIGNATURE VERIFICATION COMPLETE ====\n")


class GuiInterface:
    def __init__(self):
        self._download_window = None
        self.loop_is_initialized = False
        sys.app = QApplication(sys.argv)

    def center_window(self, window):
        window_geometry = window.frameGeometry()
        screen_center = window.screen().availableGeometry().center()
        window_geometry.moveCenter(screen_center)
        window.move(window_geometry.topLeft())
        return window.width(), window.height()

    def show_download_permission_dialog(self, version=None):
        # Create the dialog without fixed size
        dialog = QDialog()
        dialog.setWindowTitle(f"{APP_NAME}")
        dialog.resize(400, 160)  # Initial size, but resizable
        dialog.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        # Main layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        # Create horizontal layout
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)
        layout.addLayout(top_layout)

        # Create icon label with celeration.svg
        icon_label = QLabel()
        icon_pixmap = QPixmap(":/images/celeration.svg")
        colored_pixmap = QPixmap(icon_pixmap.size())
        colored_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(colored_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawPixmap(0, 0, icon_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.setBrush(QColor('#05c3de'))
        painter.setPen(QColor('#05c3de'))
        painter.drawRect(colored_pixmap.rect())
        painter.end()

        icon_label.setPixmap(colored_pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        top_layout.addWidget(icon_label)

        # Set dialog message based on version
        if version:
            message = MESSAGES["UPDATE_AVAILABLE"].format(version)
        else:
            message = MESSAGES["DOWNLOAD_PERMISSION"]

        # Create message label
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        top_layout.addWidget(msg_label, 1)

        # Create button layout
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        # Add stretchers on both sides to center the buttons
        button_layout.addStretch(1)

        # Create buttons
        yes_btn = QPushButton("Yes")
        no_btn = QPushButton("No")
        yes_btn.setMinimumWidth(80)
        no_btn.setMinimumWidth(80)
        button_layout.addWidget(yes_btn)
        button_layout.addWidget(no_btn)

        # Add equal stretch on the right side
        button_layout.addStretch(1)

        # Connect buttons
        no_btn.clicked.connect(dialog.reject)
        yes_btn.clicked.connect(dialog.accept)

        # Center the dialog
        self.center_window(dialog)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            return True
        return False

    def show_error_dialog(self, message):
        # Create error dialog
        error_dialog = QDialog()
        error_dialog.setWindowTitle("Update Required")
        error_dialog.setMinimumSize(450, 180)  # Increased height for link
        error_dialog.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        # Create layout
        layout = QVBoxLayout(error_dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        # Create message label - centered
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg_label)

        # Add GitHub repo link if this is an environment mismatch
        if "manually" in message.lower():
            # Add some spacing
            layout.addSpacing(10)

            # Create clickable link
            download_from_github_string = 'https://github.com/SJV-S/OpenCelerator?tab=readme-ov-file#download--installation'
            link_label = QLabel(f'<a href="{download_from_github_string}" style="color: #0066cc; text-decoration: none;">{GITHUB_REPO}</a>')
            link_label.setOpenExternalLinks(True)
            link_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            link_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            layout.addWidget(link_label)

        # Add spacing before button
        layout.addSpacing(15)

        # Create button layout
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        # Add spacer to center the OK button
        button_layout.addStretch()

        # Create OK button
        ok_btn = QPushButton("OK")
        ok_btn.setMinimumWidth(80)
        ok_btn.clicked.connect(error_dialog.accept)
        button_layout.addWidget(ok_btn)
        button_layout.addStretch()

        # Center the dialog
        self.center_window(error_dialog)

        # Show the dialog
        error_dialog.exec()

        # Exit
        sys.exit(0)

    def create_download_window(self, version):
        class DownloadWindow(QDialog):
            def __init__(self, version, gui_interface):
                super().__init__()
                self.gui_interface = gui_interface

                # Configure window
                self.setWindowTitle(f"{APP_NAME} Update v{version}")
                self.setMinimumSize(450, 150)
                self.setFixedSize(450, 150)
                self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

                # Create layout
                main_layout = QVBoxLayout(self)

                # Version label
                version_label = QLabel(f"Updating to v{version}")
                version_font = QFont(version_label.font())
                version_font.setBold(True)
                version_font.setPointSize(12)
                version_label.setFont(version_font)
                main_layout.addWidget(version_label)

                # Status frame
                status_frame = QFrame()
                status_layout = QHBoxLayout(status_frame)
                status_layout.setContentsMargins(0, 0, 0, 0)
                main_layout.addWidget(status_frame)

                # Status icon
                self.status_icon = QLabel("⏳")
                status_layout.addWidget(self.status_icon)

                # Status text
                self.status_label = QLabel(MESSAGES["PREPARING_DOWNLOAD"])
                status_layout.addWidget(self.status_label)
                status_layout.addStretch()

                # Progress bar
                self.progress_bar = QProgressBar()
                self.progress_bar.setTextVisible(True)
                self.progress_bar.setRange(0, 0)  # Indeterminate mode
                main_layout.addWidget(self.progress_bar)

                # Center the window
                self.gui_interface.center_window(self)

                # Show the window
                self.show()
                self.raise_()
                self.activateWindow()

            def update_status(self, message):
                self.status_label.setText(message)

                # If message contains a percentage, update progress bar and icon
                if "%" in message:
                    try:
                        percentage = float(message.split("%")[0].split(": ")[1])
                        self.progress_bar.setRange(0, 100)
                        self.progress_bar.setValue(int(percentage))

                        # Update icon based on progress
                        if percentage < 25:
                            self.status_icon.setText("⏳")
                        elif percentage < 50:
                            self.status_icon.setText("📦")
                        elif percentage < 75:
                            self.status_icon.setText("📥")
                        else:
                            self.status_icon.setText("🔄")
                    except (ValueError, IndexError):
                        pass
                else:
                    # Reset to indeterminate
                    self.progress_bar.setRange(0, 0)
                    self.status_icon.setText("⏳")

            def show(self):
                super().show()
                self.raise_()
                self.activateWindow()

            def close(self):
                try:
                    super().close()
                except:
                    pass  # Ignore errors if window is already closed

        self._download_window = DownloadWindow(version, self)
        return self._download_window

    def create_progress_signals(self):
        class ProgressCallbacks(QObject):
            # Define signals
            progress_signal = Signal(str)
            finished_signal = Signal(bool, object)

            def __init__(self, gui_interface):
                super().__init__()
                self.gui = gui_interface
                self.progress_callback = None
                self.finished_callback = None

                # Connect signals to slots
                self.progress_signal.connect(self._on_progress_internal)
                self.finished_signal.connect(self._on_finished_internal)

            def update_progress(self, message):
                self.progress_signal.emit(message)

            def complete(self, success, file_path):
                self.finished_signal.emit(success, file_path)

            def _on_progress_internal(self, message):
                if self.progress_callback:
                    self.progress_callback(message)

            def _on_finished_internal(self, success, file_path):
                # Clean up the download window first
                if self.gui._download_window:
                    try:
                        self.gui._download_window.close()
                        self.gui._download_window = None
                    except:
                        pass

                # Then call the callback if there is one
                if self.finished_callback:
                    self.finished_callback(success, file_path)

            def on_progress(self, callback):
                self.progress_callback = callback

            def on_finished(self, callback):
                self.finished_callback = callback

        return ProgressCallbacks(self)

    def run_event_loop(self):
        self.loop_is_initialized = True
        return sys.app.exec()


class ModuleLoader:
    def __init__(self, app_zip_filename=APP_ZIP_FILENAME):
        self.app_zip_filename = app_zip_filename
        self.verifier = ModuleVerifier()

    def find_external_module(self):
        directory = CONFIG_DIR

        if not directory.exists():
            logger.info(f"Config directory does not exist: {directory}")
            return None, False, None, None, None

        module_pattern = re.compile(r'app_modules_v([\d\.]+)(?:_e([\d\.]+))?')
        found_modules = []

        for item in directory.iterdir():
            if not item.is_dir():
                continue

            match = module_pattern.match(item.name)
            if not match:
                continue

            version_str = match.group(1)
            env_str = match.group(2)

            logger.info(f"Found module folder: {item} (v{version_str}, e{env_str})")

            zip_filename = f"{self.app_zip_filename}_v{version_str}"
            if env_str:
                zip_filename += f"_e{env_str}"
            zip_filename += ".zip"

            zip_path = item / zip_filename

            if not (zip_path.exists() and zip_path.is_file()):
                logger.info(f"Expected zip file not found: {zip_path}")
                continue

            logger.info(f"Found zip file: {zip_path}")

            sig_path = Path(f"{zip_path}.sig")
            if sig_path.exists():
                logger.info(f"Found signature file: {sig_path}")
                found_modules.append((zip_path, version_str, env_str))
            else:
                logger.warning(f"Found zip file but missing signature: {sig_path}")

        if not found_modules:
            logger.info("No module zip file found.")
            return None, False, None, None, None

        # Sort by semantic version (convert version components to integers)
        found_modules.sort(key=lambda x: [int(part) for part in x[1].split('.')], reverse=True)
        latest_module = found_modules[0]
        zip_path, version_str, env_str = latest_module

        logger.info(f"Selected latest module: v{version_str}")
        return zip_path, True, MAIN_MODULE_NAME, version_str, env_str

    def extract_version_info_from_filename(self, filename):
        """Extract version and environment strings from a filename
        Expected format: app_modules_v0.11.0_e0.11.0.zip
        Returns (version_str, env_str) or (None, None) if not found
        """
        try:
            # Parse the new format: app_modules_v0.11.0_e0.11.0.zip
            parts = filename.split('_')
            if len(parts) >= 4:
                # Extract version without 'v' prefix
                version_str = parts[2][1:]  # Remove 'v' from v0.11.0
                # Extract environment without 'e' prefix
                env_str = parts[3][1:].split('.zip')[0]  # Remove 'e' from e0.11.0

                logger.info(f"Extracted version: {version_str}, environment: {env_str}")
                return version_str, env_str
            else:
                logger.info(f"Filename format does not match expected pattern: {filename}")
                return None, None
        except (IndexError, ValueError) as e:
            logger.error(f"Could not extract version info from filename '{filename}': {e}")
            return None, None

    def load_module_from_zip(self, zip_path, main_module_name, version_str=None, env_str=None):
        # For macOS, extract to temp directory instead of using direct ZIP imports
        if platform.system() == "Darwin":  # macOS
            temp_dir = tempfile.mkdtemp(prefix=f"{APP_NAME}_")
            logger.info(f"Extracting module to temporary directory: {temp_dir}")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Add the temp directory to sys.path
            if temp_dir not in sys.path:
                sys.path.insert(0, temp_dir)
        else:
            # Original approach for other platforms
            zip_path_str = str(zip_path.resolve())
            if zip_path_str not in sys.path:
                sys.path.insert(0, zip_path_str)

        # Import the main module
        try:
            main_module = __import__(main_module_name)

            # Store version and environment information
            if version_str:
                main_module.version = version_str
            if env_str:
                main_module.environment = env_str

            return main_module
        except ImportError:
            # If main module not found, try to find any Python file
            if platform.system() == "Darwin":
                # Look in temp directory
                py_files = list(Path(temp_dir).glob("*.py"))
                if py_files:
                    module_name = py_files[0].stem
                    spec = importlib.util.spec_from_file_location(module_name, py_files[0])
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    if version_str:
                        module.version = version_str
                    if env_str:
                        module.environment = env_str

                    return module
            else:
                # Look in ZIP file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    py_files = [f for f in zip_ref.namelist() if f.endswith(".py")]
                    if py_files:
                        fallback_name = py_files[0][:-3]  # Remove .py extension
                        module = __import__(fallback_name)

                        if version_str:
                            module.version = version_str
                        if env_str:
                            module.environment = env_str

                        return module

        raise ImportError(f"No suitable Python module found in {zip_path}")


class UpdateChecker:
    def __init__(self, github_repo=GITHUB_REPO, app_zip_filename=APP_ZIP_FILENAME):
        self.github_repo = github_repo
        self.app_zip_filename = app_zip_filename
        self.verifier = ModuleVerifier()
        self.loader = ModuleLoader()

    def check_for_updates_after_app_termination(self):
        try:
            # Read update preference
            update_policy = self.get_update_preference()

            # If updates are disabled, do nothing
            if update_policy != 'Auto':
                return

            # Check the last update date
            prefs_file = CONFIG_DIR / 'preferences.json'
            today = datetime.now().strftime('%Y-%m-%d')
            check_for_update = True

            if prefs_file.exists():
                try:
                    with open(prefs_file, 'r') as f:
                        preferences = json.load(f)
                        last_update_date = preferences.get('last_update_check', '')

                        # Don't check for updates if already checked today
                        if last_update_date == today:
                            logger.info(f"Already checked for updates today ({today}). Skipping.")
                            check_for_update = False
                except Exception as e:
                    logger.error(f"Error reading preferences: {e}")

            if not check_for_update:
                return

            # Update the last update check date
            try:
                if prefs_file.exists():
                    with open(prefs_file, 'r') as f:
                        preferences = json.load(f)
                else:
                    return

                preferences['last_update_check'] = today

                with open(prefs_file, 'w') as f:
                    json.dump(preferences, f, indent=2)
            except Exception as e:
                logger.error(f"Error updating last update date: {e}")

            # Check for available updates
            latest_version, download_url, sig_url, version_exists = self.check_for_updates()

            # If new version is available and not already downloaded
            if latest_version and not version_exists and update_policy == 'Auto':
                # Silently download update without GUI
                self.download_update(latest_version, download_url, sig_url)

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")

    def get_update_preference(self):
        default = 'Off'
        try:
            prefs_file = CONFIG_DIR / 'preferences.json'
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    preferences = json.load(f)
                return preferences.get('update', default)

            return default  # If file doesn't exist
        except Exception:
            return default  # On error

    def check_for_updates(self):
        # Check GitHub repository for available updates using GitHub's API.
        try:
            releases = self._fetch_github_releases()
            if not releases:
                return None, None, None, False

            # Check releases in order until we find one with required files
            for release_idx, release_data in enumerate(releases):
                logger.info(f"Checking release {release_idx + 1}/{len(releases)}")

                result = self._process_release(release_data)
                if result:
                    version, download_url, sig_url = result
                    version_exists = self._check_if_version_exists_locally(download_url, version)
                    return version, download_url, sig_url, version_exists

                logger.info(f"Release {release_idx + 1} incomplete, checking next release...")

            # If we get here, no valid release was found
            logger.error("No valid release found with required module files in any release")
            return None, None, None, False

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            traceback.print_exc()
            return None, None, None, False

    def _fetch_github_releases(self):
        # Extract owner and repo from GitHub URL
        parsed_url = urlparse(self.github_repo)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) != 2:
            logger.error(f"Invalid GitHub repo URL format: {self.github_repo}")
            return None

        owner, repo = path_parts
        logger.info(f"Checking for updates in repository: {owner}/{repo}")

        # Get all releases directly
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        logger.info(f"Getting all releases from: {api_url}")
        response = requests.get(api_url, timeout=15)
        logger.info(f"Releases request status code: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"Failed to get releases (status code: {response.status_code})")
            return None

        # Parse releases list
        releases = response.json()
        if not releases or not isinstance(releases, list) or len(releases) == 0:
            logger.error("No releases found or invalid response format")
            return None

        # Sort by created date (newest first)
        releases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        logger.info(f"Found {len(releases)} releases")

        return releases

    def _process_release(self, release_data):
        # Extract version from tag name
        tag_name = release_data.get("tag_name", "")
        version = tag_name.lstrip("v")
        if not version:
            logger.warning("Skipping release: no version in tag name")
            return None

        logger.info(f"Checking version: {version}")

        # Look for ZIP and signature assets
        assets = release_data.get("assets", [])
        logger.info(f"Found {len(assets)} assets in this release")

        download_url, sig_url = self._find_required_assets(assets)

        if download_url and sig_url:
            logger.info(f"Found valid release with all required files: v{version}")
            logger.info(f"Download URL: {download_url}")
            logger.info(f"Signature URL: {sig_url}")
            return version, download_url, sig_url
        else:
            # Log what was missing
            if not download_url:
                logger.warning("Missing ZIP module URL")
            if not sig_url:
                logger.warning("Missing signature file URL")
            return None

    def _find_required_assets(self, assets):
        download_url = None
        sig_url = None

        for asset in assets:
            asset_name = asset.get("name", "")
            asset_url = asset.get("browser_download_url", "")

            # Look for module ZIP file
            if asset_name.startswith(f"{self.app_zip_filename}_v") and asset_name.endswith(".zip"):
                download_url = asset_url
                logger.info(f"Found ZIP module: {asset_name}")

                # Extract environment string from the filename
                version_str, env_str = self.loader.extract_version_info_from_filename(asset_name)
                if env_str:
                    logger.info(f"Extracted environment: {env_str}")

            # Look for signature file
            elif asset_name.endswith(".zip.sig"):
                sig_url = asset_url
                logger.info(f"Found signature file: {asset_name}")

        return download_url, sig_url

    def _check_if_version_exists_locally(self, download_url, version):
        if not CONFIG_DIR or not CONFIG_DIR.exists():
            return False

        # Get folder path using utility function
        url_path = urlparse(download_url).path
        filename = Path(url_path).name
        version_folder = CONFIG_DIR / Path(filename).stem

        # Check for any file matching the pattern
        zip_files = list(version_folder.glob(f"{self.app_zip_filename}_v{version}_e*.zip"))

        if zip_files:
            zip_path = zip_files[0]  # Take the first match if multiple exist
            sig_path = Path(f"{zip_path}.sig")
            version_exists = zip_path.exists() and sig_path.exists()

            if version_exists:
                logger.info(f"Version {version} already exists locally at {zip_path}")
            else:
                logger.info(f"Version {version} does not exist locally")

            return version_exists

        return False

    def _ensure_directory_exists(self, directory_path):
        try:
            directory_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {e}")
            return False

    def download_update(self, version, download_url, sig_url, signals=None):
        # Download and verify an update
        # Headless download if signals is None
        try:
            # Ensure the config directory exists
            self._ensure_directory_exists(CONFIG_DIR)

            # Extract filename from the download URL to preserve the full format
            url_path = urlparse(download_url).path
            filename = Path(url_path).name
            version_folder = CONFIG_DIR / Path(filename).stem
            self._ensure_directory_exists(version_folder)

            # Prepare file paths
            zip_path = version_folder / filename
            sig_path = Path(f"{zip_path}.sig")

            # Download ZIP file
            if signals:
                signals.update_progress(MESSAGES["DOWNLOADING_UPDATE"])
                time.sleep(0.5)

            # Download with progress tracking
            success = download_file_with_progress(
                download_url,
                zip_path,
                progress_callback=signals.update_progress if signals else None
            )

            if not success:
                logger.error("Failed to download ZIP file")
                if signals:
                    signals.complete(False, None)
                return None

            # Download signature file
            if signals:
                signals.update_progress(MESSAGES["DOWNLOADING_SIGNATURE"])

            sig_response = requests.get(sig_url)
            sig_response.raise_for_status()

            with open(sig_path, 'w') as f:
                f.write(sig_response.text)

            # Verify the download
            if signals:
                signals.update_progress(MESSAGES["VERIFYING_DOWNLOAD"])
                time.sleep(0.5)

            # Verify the signature
            verification_result, _ = self.verifier.verify_module_integrity(zip_path, version)
            if not verification_result:
                # Remove files if verification fails
                zip_path.unlink(missing_ok=True)
                sig_path.unlink(missing_ok=True)
                # Try to remove the folder if it's empty
                try:
                    version_folder.rmdir()
                except:
                    pass

                if signals:
                    signals.complete(False, None)
                return None

            if signals:
                signals.complete(True, zip_path)
            return zip_path

        except Exception as e:
            logger.error(f"Error downloading update: {e}")
            traceback.print_exc()  # Add traceback for better error diagnosis
            if signals:
                signals.complete(False, None)
            return None


class AppLauncher:
    def __init__(self):
        self.verifier = ModuleVerifier()
        self.loader = ModuleLoader()
        self.gui = GuiInterface()

    def set_app_version(self, version_str):
        """
        Update the version in preferences.json and return whether it was an update or downgrade.
        Returns:
            - "update" if new version is higher than previous
            - "downgrade" if new version is lower than previous
            - None if version is unchanged or error occurred
        """
        # Update the version in preferences.json
        prefs_file = CONFIG_DIR / 'preferences.json'
        try:
            preferences = {}
            current_version = None

            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    preferences = json.load(f)
                    current_version = preferences.get('version')

            # If versions are the same, no change needed
            if current_version == version_str:
                logger.info(f"Version unchanged in preferences.json: {version_str}")
                return None

            # Determine if this is an update or downgrade using semantic versioning
            result = None
            if current_version:
                # Convert version strings to lists of integers for comparison
                try:
                    current_parts = [int(part) for part in current_version.split('.')]
                    new_parts = [int(part) for part in version_str.split('.')]

                    # Compare version components from left to right
                    for i in range(max(len(current_parts), len(new_parts))):
                        # If we run out of parts in either version, pad with zeros
                        current_part = current_parts[i] if i < len(current_parts) else 0
                        new_part = new_parts[i] if i < len(new_parts) else 0

                        if new_part > current_part:
                            result = "update"
                            break
                        elif new_part < current_part:
                            result = "downgrade"
                            break

                    # If all components were equal (shouldn't happen since we checked equality above)
                    if result is None:
                        return None

                except (ValueError, IndexError) as e:
                    logger.error(f"Error comparing versions: {e}")
                    # If there's an error in comparison, still update the version but return None
            else:
                # No previous version, so it's an update
                result = "update"

            # Set the version key to the current version_str
            preferences['version'] = version_str

            # Ensure the directory exists
            prefs_file.parent.mkdir(parents=True, exist_ok=True)

            # Write back the updated preferences
            with open(prefs_file, 'w') as f:
                json.dump(preferences, f, indent=2)

            logger.info(f"Updated preferences.json with version: {version_str} ({result})")
            return result

        except Exception as e:
            logger.error(f"Error updating version in preferences.json: {e}")
            return None

    def run_application(self, module_path, main_module_name, version_str, env_str=None):
        # If env_str wasn't provided, try to extract it from the filename
        if env_str is None:
            version_str, env_str = self.loader.extract_version_info_from_filename(module_path.name)
            if env_str is None:
                env_str = LAUNCHER_ENVIRONMENT.lstrip(".")  # Use default if extraction fails

        # Check if launcher environment matches the module environment
        if env_str != LAUNCHER_ENVIRONMENT.lstrip("."):
            logger.error(f"Environment mismatch: Launcher env={LAUNCHER_ENVIRONMENT.lstrip('.')}, Module env={env_str}")
            error_message = MESSAGES["ENVIRONMENT_MISMATCH"]
            self.gui.show_error_dialog(error_message)
            return 2  # Return special code for environment mismatch

        # Verify module integrity
        verification_result, initial_hash = self.verifier.verify_module_integrity(module_path, version_str)
        if not verification_result:
            logger.error(f"Error: Module integrity check failed!")
            return 1

        # Calculate hash again before loading to detect tampering
        current_hash = self.verifier.calculate_file_hash(module_path)
        if current_hash != initial_hash:
            logger.error(f"SECURITY ERROR: File hash mismatch detected!")
            logger.error(f"Initial hash: {initial_hash}")
            logger.error(f"Current hash: {current_hash}")
            logger.error("File appears to have been modified after verification!")
            return 1

        logger.info(f"File hash verification successful - no tampering detected")

        # Make version change status available in app.py if no download gui
        if not self.gui.loop_is_initialized:
            sys.version_change_status = self.set_app_version(version_str)

        # Load the module
        self.loader.load_module_from_zip(module_path, main_module_name, version_str, env_str)

        # Close Windows splash screen if present
        remove_splash_screen()

        if not self.gui.loop_is_initialized:
            return sys.app.exec()
        else:
            return 0


def remove_splash_screen():
    """Close Nuitka splash screen using Windows API"""
    if platform.system() == 'Windows':
        import ctypes

        user32 = ctypes.windll.user32
        WM_CLOSE = 0x0010

        hwnd = user32.FindWindowW("Splash", None)
        if hwnd:
            user32.SendMessageW(hwnd, WM_CLOSE, 0, 0)
            logger.info("Splash screen closed successfully")
            return True

        return False

def main():
    # Windows splash screen
    if platform.system() == 'Windows':  # Check if OS is Windows
        if "NUITKA_ONEFILE_PARENT" in environ:
            splash_filename = Path(tempfile.gettempdir()) / f"onefile_{int(environ['NUITKA_ONEFILE_PARENT'])}_splash_feedback.tmp"
            if splash_filename.exists():
                splash_filename.unlink()
            logger.info("Splash Screen has been removed")

    launcher = AppLauncher()  # GUI is initialized inside AppLauncher now
    loader = ModuleLoader()
    update_checker = UpdateChecker()
    gui = launcher.gui  # Get the already initialized GUI

    try:
        # Find the external module
        external_file, is_zip, main_module_name, version_str, env_str = loader.find_external_module()

        # If module found, run it
        if external_file is not None:
            logger.info(f"Found application at: {external_file.resolve()}")
            logger.info(f"Version: v{version_str}, Environment: e{env_str}")

            # Run the application first
            launcher.run_application(external_file, main_module_name, version_str, env_str)

            # Check for updates
            update_checker.check_for_updates_after_app_termination()

            return

        # Ask permission to download the latest version
        logger.info("No module found. Asking for permission to download the latest version...")
        if not gui.show_download_permission_dialog():
            logger.info("Download permission declined. Exiting gracefully.")
            return 0  # Exit with success code since this is a user choice, not an error

        # User approved, now check for updates
        logger.info("Checking for updates...")
        latest_version, download_url, sig_url, version_exists = update_checker.check_for_updates()

        if latest_version and download_url and sig_url:
            logger.info(f"Latest version: v{latest_version}")
            logger.info(f"Download URL: {download_url}")

            # Create download window
            download_window = gui.create_download_window(latest_version)
            download_window.show()

            # Create signals for progress updates
            signals = gui.create_progress_signals()
            signals.on_progress(download_window.update_status)

            # Handle download completion
            def on_download_finished(success, file_path):
                if success:
                    logger.info(f"Update downloaded successfully to {file_path}")
                    # Extract env_str from filename
                    version_str, env_str = loader.extract_version_info_from_filename(file_path.name)
                    if env_str is None:
                        logger.error(f"Could not extract environment string")
                        env_str = LAUNCHER_ENVIRONMENT.lstrip(".")  # Use default if extraction fails

                    # Launch the application
                    launcher.run_application(file_path, MAIN_MODULE_NAME, latest_version, env_str)

                else:
                    gui.show_error_dialog(MESSAGES["DOWNLOAD_FAILED"])
                    return 1

            signals.on_finished(on_download_finished)

            # Start download in a separate thread to keep UI responsive
            download_thread = Thread(
                target=update_checker.download_update,
                args=(latest_version, download_url, sig_url, signals)
            )
            download_thread.daemon = True
            download_thread.start()

            # Start the event loop
            return gui.run_event_loop()
        else:
            gui.show_error_dialog(MESSAGES["NO_UPDATES"])
            return 1

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        gui.show_error_dialog(MESSAGES["ERROR_OCCURRED"].format(str(e)))
        return 1


if __name__ == "__main__":
    if DEBUGGING:
        logger.set_level(logging.DEBUG)
    sys.exit(main())
