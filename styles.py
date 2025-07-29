import platform
from pathlib import Path


def get_system_font():
    os_name = platform.system()

    if os_name == "Linux":
        available_fonts = Path('/usr/share/fonts').exists()
        if available_fonts:
            # Use fc-list to check for fonts
            import subprocess
            try:
                result = subprocess.run(['fc-list', ':', 'family'], capture_output=True, text=True)
                available_fonts = result.stdout
                if "Tahoma" in available_fonts:
                    return ("Tahoma", 12)
                else:
                    return ("DejaVu Sans", 12)
            except:
                return ("DejaVu Sans", 12)
        else:
            return ("DejaVu Sans", 12)
    else:
        fonts = {
            "Windows": ("Tahoma", 12),
            "Darwin": ("Tahoma", 12),
        }
        return fonts.get(os_name, ("Sans serif", 12))


font_family, size = get_system_font()
font_size = f'{size}px'
tab_menu_font_size = f'{size + 1}px'

general_stylesheet = f"""
QWidget {{
    font-family: '{font_family}';
    font-size: {font_size};
    color: black;
}}

/* QMainWindow styles */
QMainWindow {{
    background-color: white;
}}

/* QPushButton styles */
QPushButton {{
    margin-top: 5px;
    border: 1px solid #191919;
    padding: 5px;
    background-color: white;
    border-radius: 5px;
}}
QPushButton:hover {{
    background-color: #e7efff;
}}

QRadioButton {{
    margin: 5px;
    color: black;
}}

QRadioButton::indicator {{
    width: 20px;
    height: 20px;
}}

QRadioButton::indicator:unchecked {{
    image: url(:/images/circle-regular.svg);
}}

QRadioButton::indicator:checked {{
    image: url(:/images/circle-dot-regular.svg);
}}

QRadioButton:disabled {{
    color: gray; /* Text color when disabled */
}}

QRadioButton::indicator:disabled {{
    color: gray;
}}

QRadioButton::indicator:unchecked:disabled {{
    image: url(:/images/circle-regular-disabled.svg);
}}

QRadioButton::indicator:checked:disabled {{
    image: url(:/images/circle-dot-regular-disabled.svg);
}}

/* QLabel styles */
QLabel {{
    margin: 0px;
    font-style: italic;
    color: black;
}}

/* QLineEdit styles */
QLineEdit {{
    color: black;
    background-color: white;
    border: 1px solid gray;
    padding: 4px;
    margin 0px;
}}

QCheckBox {{
    margin: 5px;
    background-color: white;
}}

QCheckBox::indicator {{
    background-color: white; 
    border: 1px solid black; 
}}

QCheckBox::indicator:checked {{
    background-color: white; /* Background color when checked */
    border: 1px solid black; /* Border color when checked */
    image: url(:/images/check-solid.svg);
    width: 14px;
    height: 14px;
}}

QCheckBox::indicator:unchecked {{
    background-color: white;
    border: 1px solid black;
    width: 14px;
    height: 14px;
}}

QCheckBox::indicator:unchecked:disabled {{
    background-color: lightgray;
    color: lightgray;
    border: 1px solid darkgray;
}}

QCheckBox::indicator:checked:disabled {{
    background-color: lightgray;
    color: lightgray;
    border: 1px solid darkgray;
}}

QCheckBox:disabled {{
    color: gray;
}}

/* QGroupBox styles */
QGroupBox {{
    border: 1px solid silver;
    border-radius: 5px;
    margin-top: 20px; /* Space above the group box */
    font-weight: bold;
    color: #323232;
}}

/* QGroupBox Title styles */
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top center; /* Center the title */
    padding: 0 3px;
}}

/* QTabWidget styles */
QTabWidget::pane {{
    border: 1px solid black;
    margin-top: 0px;
    border-bottom-left-radius: 20px;
    border-bottom-right-radius: 20px;
}}

QTabWidget {{
    min-width: 199px;
    max-width: 199px;
}}

QTabWidget::tab-bar {{
    position: absolute;
    left: 0;
}}

/* Styling for individual tabs */
QTabBar::tab {{
    background: white;
    padding: 5 11 5 11px;
    border: 0px solid #5a93cc;
    border-bottom-color: transparent;  /* Makes the bottom border of the tab invisible */
    font-family: '{font_family}';
    font-size: {tab_menu_font_size};
    min-width: 43px;
    max-width: 43px;
}}

/* Styling for the first tab */
QTabBar::tab:first {{
    border-top-left-radius: 10px;  /* Rounds the top left corner of the first tab */
    border-top: 1px solid black;
    border-left: 1px solid black;
    border-right: 1px solid black;
}}

QTabBar::tab:second {{
    border-top: 1px solid black;
}}

QTabBar::tab:last {{
    border-top: 1px solid black;
    border-left: 1px solid black;
    border-right: 1px solid black;
    border-top-right-radius: 10px;
}}

/* Styling for selected and hovered tabs */
QTabBar::tab:selected {{
    background: #d7dfef;
}}

QTabBar::tab:hover {{
    background: #e7efff;
}}

/* QDateEdit styles */
QDateEdit {{
    color: black;
    background-color: white;
    border: 1px solid gray;
    padding: 3px;
}}

QCalendarWidget QToolButton {{
    color: black; /* Text color for the header */
    background-color: lightgray;
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: lightgray;
}}

QCalendarWidget QAbstractItemView {{
    background-color: white;
    color: black;
}}

QCalendarWidget QTableView {{
    background-color: white;
}}

/* QListWidget styles */
QListWidget {{
    border: 1px solid gray;
    padding: 5px;
    color: black;
    background-color: white;
}}

QListWidget::item {{
    color: black;
    background-color: white;
}}

QListWidget::item:selected {{
    background-color: #d3d3d3; /* Slightly darker background color for selected items */
}}

/* QDialog styles */
QDialog {{
    background-color: #f0f0f0;
}}

QComboBox {{
    color: black;
    background-color: #ececec;
    border: 1px solid gray;
    padding: 3px;
    border-radius: 0px;  /* Remove rounded corners */
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: gray;
    border-left-style: solid;
    border-top-right-radius: 0px;
    border-bottom-right-radius: 0px;
    background-color: #ececec;
}}

QComboBox::down-arrow {{
    image: none;  /* Remove default arrow if you want */
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid black;
}}

QComboBox QAbstractItemView {{
    color: black;
    background-color: white;
    border: 1px solid gray;
    selection-background-color: #e7efff;
}}

/* QFileDialog styles */
QFileDialog {{
    background-color: #f0f0f0;
}}

/* QMessageBox styles */
QMessageBox {{
    background-color: #f0f0f0;
}}

QSpinBox {{
    color: black;
    background-color: #ececec;
}}

QDoubleSpinBox {{
    color: black;
    background-color: #ececec;
}}

QDialog {{
    background-color: #f9f9f9;
    color: black;
}}

QScrollArea QWidget {{
    background-color: #f9f9f9;
    color: black;
}}

/* QMenu styles */
QMenu {{
    background-color: white;
    color: black;
    border: 1px solid gray;
    padding: 2px;
}}

QMenu::item {{
    background-color: white;
    color: black;
    padding: 5px 20px;
}}

QMenu::item:selected {{
    background-color: #e7efff;
    color: black;
}}

QMenu::item:disabled {{
    background-color: white;
    color: gray;
}}

QMenu::separator {{
    height: 1px;
    background-color: gray;
    margin: 2px 0px;
}}
"""
