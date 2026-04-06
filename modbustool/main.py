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

from core.i18n import load_language


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ModbusTool")
    app.setOrganizationName("ModbusTool")

    # Load language preference before building any UI
    load_language()

    # Set a clean default font
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    # Apply a polished stylesheet
    app.setStyleSheet("""
        /* ── Base ─────────────────────────────────── */
        QMainWindow {
            background-color: #f0f2f5;
        }

        /* ── Group Boxes ──────────────────────────── */
        QGroupBox {
            font-weight: bold;
            font-size: 10pt;
            color: #37474F;
            border: 1px solid #CFD8DC;
            border-radius: 6px;
            margin-top: 12px;
            padding: 18px 8px 8px 8px;
            background-color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #37474F;
        }

        /* ── Tabs ─────────────────────────────────── */
        QTabWidget::pane {
            border: 1px solid #CFD8DC;
            border-radius: 0 0 6px 6px;
            background-color: #ffffff;
            top: -1px;
        }
        QTabBar {
            qproperty-drawBase: 0;
        }
        QTabBar::tab {
            padding: 8px 20px;
            margin-right: 2px;
            border: 1px solid #CFD8DC;
            border-bottom: none;
            border-radius: 6px 6px 0 0;
            background-color: #ECEFF1;
            color: #546E7A;
            font-weight: bold;
            font-size: 10pt;
            min-width: 80px;
        }
        QTabBar::tab:hover {
            background-color: #CFD8DC;
            color: #263238;
        }
        QTabBar::tab:selected {
            background-color: #1976D2;
            color: white;
            border-color: #1565C0;
        }

        /* ── Tables ───────────────────────────────── */
        QTableWidget {
            gridline-color: #E0E0E0;
            selection-background-color: #BBDEFB;
            selection-color: #212121;
            alternate-background-color: #F5F7FA;
            background-color: white;
            border: 1px solid #CFD8DC;
            border-radius: 4px;
        }
        QTableWidget::item {
            padding: 4px 6px;
        }
        QHeaderView::section {
            background-color: #37474F;
            color: white;
            padding: 6px 8px;
            border: none;
            border-right: 1px solid #455A64;
            font-weight: bold;
            font-size: 9pt;
        }
        QHeaderView::section:first {
            border-top-left-radius: 4px;
        }
        QHeaderView::section:last {
            border-top-right-radius: 4px;
            border-right: none;
        }

        /* ── Status Bar ───────────────────────────── */
        QStatusBar {
            background-color: #37474F;
            color: #B0BEC5;
            font-size: 9pt;
            padding: 2px 8px;
        }

        /* ── Progress Bar ─────────────────────────── */
        QProgressBar {
            border: 1px solid #CFD8DC;
            border-radius: 6px;
            text-align: center;
            background-color: #ECEFF1;
            color: #37474F;
            font-weight: bold;
            height: 20px;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1976D2, stop:1 #42A5F5);
            border-radius: 6px;
        }

        /* ── Splitter ─────────────────────────────── */
        QSplitter::handle {
            background-color: #CFD8DC;
            height: 3px;
            width: 3px;
        }
        QSplitter::handle:hover {
            background-color: #90A4AE;
        }

        /* ── Inputs ───────────────────────────────── */
        QComboBox, QLineEdit {
            padding: 5px 8px;
            border: 1px solid #CFD8DC;
            border-radius: 4px;
            background-color: white;
            selection-background-color: #BBDEFB;
            min-height: 20px;
        }
        QSpinBox, QDoubleSpinBox {
            padding: 5px 8px;
            padding-right: 24px;
            border: 1px solid #CFD8DC;
            border-radius: 4px;
            background-color: white;
            selection-background-color: #BBDEFB;
            min-height: 20px;
        }
        QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
            border-color: #1976D2;
        }
        QComboBox::drop-down {
            border: none;
            padding-right: 6px;
        }
        QSpinBox::up-button, QDoubleSpinBox::up-button {
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #CFD8DC;
            border-bottom: 1px solid #CFD8DC;
            border-top-right-radius: 4px;
            background-color: #ECEFF1;
        }
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
            background-color: #CFD8DC;
        }
        QSpinBox::down-button, QDoubleSpinBox::down-button {
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 20px;
            border-left: 1px solid #CFD8DC;
            border-bottom-right-radius: 4px;
            background-color: #ECEFF1;
        }
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
            background-color: #CFD8DC;
        }
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid #546E7A;
        }
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #546E7A;
        }
        QSpinBox::up-arrow:hover, QDoubleSpinBox::up-arrow:hover {
            border-bottom-color: #1976D2;
        }
        QSpinBox::down-arrow:hover, QDoubleSpinBox::down-arrow:hover {
            border-top-color: #1976D2;
        }

        /* ── Buttons (default) ────────────────────── */
        QPushButton {
            padding: 5px 14px;
            border: 1px solid #CFD8DC;
            border-radius: 4px;
            background-color: #ECEFF1;
            color: #37474F;
            font-weight: bold;
            min-height: 22px;
        }
        QPushButton:hover {
            background-color: #CFD8DC;
            border-color: #90A4AE;
        }
        QPushButton:pressed {
            background-color: #B0BEC5;
        }
        QPushButton:disabled {
            background-color: #F5F5F5;
            color: #BDBDBD;
            border-color: #E0E0E0;
        }

        /* ── Checkboxes ───────────────────────────── */
        QCheckBox {
            spacing: 6px;
            color: #37474F;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid #90A4AE;
            border-radius: 3px;
            background-color: white;
        }
        QCheckBox::indicator:checked {
            background-color: #1976D2;
            border-color: #1565C0;
        }

        /* ── Labels ───────────────────────────────── */
        QLabel {
            color: #37474F;
        }

        /* ── Menu Bar ─────────────────────────────── */
        QMenuBar {
            background-color: #37474F;
            color: #ECEFF1;
            padding: 2px;
            font-size: 10pt;
        }
        QMenuBar::item {
            padding: 4px 12px;
            border-radius: 3px;
        }
        QMenuBar::item:selected {
            background-color: #455A64;
        }
        QMenu {
            background-color: #ffffff;
            border: 1px solid #CFD8DC;
            border-radius: 4px;
            padding: 4px;
        }
        QMenu::item {
            padding: 6px 24px 6px 12px;
            border-radius: 3px;
        }
        QMenu::item:selected {
            background-color: #E3F2FD;
            color: #1565C0;
        }
        QMenu::separator {
            height: 1px;
            background-color: #E0E0E0;
            margin: 4px 8px;
        }

        /* ── Scroll Area ──────────────────────────── */
        QScrollArea {
            border: none;
        }
        QScrollBar:vertical {
            width: 10px;
            background: transparent;
            margin: 0;
        }
        QScrollBar::handle:vertical {
            background: #B0BEC5;
            border-radius: 5px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover {
            background: #78909C;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }

        /* ── Wizard ───────────────────────────────── */
        QWizard {
            background-color: #f0f2f5;
        }
    """)

    # Show splash screen, then main window
    from ui.splash_screen import SplashScreen

    def show_main():
        from ui.main_window import MainWindow
        window = MainWindow()
        window.show()
        # Keep reference so it doesn't get garbage collected
        app._main_window = window

    splash = SplashScreen(on_finished=show_main)
    splash.show()
    app._splash = splash  # prevent GC

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
