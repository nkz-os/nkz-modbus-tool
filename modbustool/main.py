#!/usr/bin/env python3
"""ModbusTool — Universal Modbus RTU/TCP Configuration & Monitoring Tool."""

import logging
import sys
import os

# Ensure the package root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Silence noisy serial port enumeration warnings from pymodbus/pyserial
logging.getLogger("pymodbus").setLevel(logging.WARNING)
logging.getLogger("pyserial").setLevel(logging.WARNING)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ModbusTool")
    app.setOrganizationName("ModbusTool")

    # Set a clean default font
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    # Apply a modern stylesheet
    app.setStyleSheet("""
        QMainWindow { background-color: #f5f5f5; }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 16px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
        }
        QTabWidget::pane { border: 1px solid #ccc; }
        QTabBar::tab {
            padding: 6px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #2196F3;
            color: white;
            border-radius: 4px 4px 0 0;
        }
        QTableWidget {
            gridline-color: #ddd;
            selection-background-color: #BBDEFB;
        }
        QTableWidget::item { padding: 4px; }
        QHeaderView::section {
            background-color: #e0e0e0;
            padding: 4px;
            border: 1px solid #ccc;
            font-weight: bold;
        }
        QStatusBar { background-color: #e0e0e0; }
        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #2196F3;
            border-radius: 4px;
        }
        QSplitter::handle { background-color: #ddd; }
        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
            padding: 4px;
            border: 1px solid #ccc;
            border-radius: 3px;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
