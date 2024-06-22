
general_stylesheet = '''
QWidget {
    font-family: "Sans-serif";
    font-size: 12px;
}
/* QMainWindow styles */
QMainWindow {
    background-color: white;
}
/* QPushButton styles */
QPushButton {
    margin-top: 5px;
    border: 1px solid #191919;
    padding: 5px;
    background-color: white;
    border-radius: 5px;
}
QPushButton:hover {
    background-color: #e7efff;
}
/* QRadioButton styles */
QRadioButton {
    margin: 5px;
}
/* QLabel styles */
QLabel {
    margin: 0px;
    font-style: italic;
    color: black;
}
/* QLineEdit styles */
QLineEdit {
    border: 1px solid gray;
    padding: 4px;
    margin 0px;
}

QCheckBox {
    margin: 5px;
}
QCheckBox::indicator {
}
QCheckBox::indicator:unchecked {
}
QCheckBox::indicator:checked { 
}
/* QGroupBox styles */
QGroupBox {
    border: 1px solid silver;
    border-radius: 5px;
    margin-top: 20px; /* Space above the group box */
    font-weight: bold;
    color: #323232;
}
/* QGroupBox Title styles */
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center; /* Center the title */
    padding: 0 3px;
}
/* QTabWidget styles */
QTabWidget::pane {
    border: 1px solid black;
    margin-top: 0px;
    border-bottom-left-radius: 20px;
    border-bottom-right-radius: 20px;
}

/* QTabWidget styles */
QTabWidget {
    min-width: 184px;
    max-width: 184px;
}

QTabWidget::tab-bar {
}
/* Styling for individual tabs */
QTabBar::tab {
    background: white;
    padding: 5 11 5 11px;
    border: 0px solid #5a93cc;
    border-bottom-color: transparent;  /* Makes the bottom border of the tab invisible */
    font-family: "Sans-serif";
    font-size: 12px;
    min-width: 38px;
    max-width: 38px;
    
}
/* Styling for the first tab */
QTabBar::tab:first {
    border-top-left-radius: 10px;  /* Rounds the top left corner of the first tab */
    border-top: 1px solid black;
    border-left: 1px solid black;
    border-right: 1px solid black;

}
QTabBar::tab:second {
    border-top: 1px solid black;

}
QTabBar::tab:last {
    border-top: 1px solid black;
    border-left: 1px solid black;
    border-right: 1px solid black;
    border-top-right-radius: 10px;

}
/* Styling for selected and hovered tabs */
QTabBar::tab:selected {
    background: #d7dfef;
}

QTabBar::tab:hover {
    background: #e7efff;
}

/* QDateEdit styles */
QDateEdit {
    border: 1px solid gray;
    padding: 3px;
}
/* QListWidget styles */
QListWidget {
    border: 1px solid gray;
    padding: 5px;
}
/* QDialog styles */
QDialog {
    background-color: #f0f0f0;
}
/* QComboBox styles */
QComboBox {
    border: 1px solid gray;
    padding: 3px;
}
/* QFileDialog styles */
QFileDialog {
    background-color: #f0f0f0;
}
/* QMessageBox styles */
QMessageBox {
    background-color: #f0f0f0;
}
'''
