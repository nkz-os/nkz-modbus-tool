"""Main application window."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget,
    QStatusBar, QSplitter, QMenuBar, QMenu, QFileDialog, QMessageBox,
    QApplication,
)
from PyQt6.QtGui import QAction, QActionGroup, QFont

from core.modbus_client import ModbusClient
from core.device_profiles import ProfileManager, DeviceProfile
from core.i18n import tr, LANGUAGES, get_language, set_language, save_language
from ui.connection_panel import ConnectionPanel
from ui.dashboard_tab import DashboardTab
from ui.scanner_tab import ScannerTab
from ui.monitor_tab import MonitorTab
from ui.config_tab import ConfigTab
from ui.profile_wizard import ProfileWizard


class MainWindow(QMainWindow):
    """ModbusTool main window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("ModbusTool — Universal Modbus Configuration & Monitor"))
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        # Core objects
        self.client = ModbusClient()
        self.profile_manager = ProfileManager()

        self._setup_menubar()
        self._setup_ui()
        self._setup_statusbar()
        self._connect_signals()

    def _setup_menubar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu(tr("File"))

        new_profile_action = QAction(tr("New Profile Wizard..."), self)
        new_profile_action.setShortcut("Ctrl+N")
        new_profile_action.triggered.connect(self._open_profile_wizard)
        file_menu.addAction(new_profile_action)

        load_profile_action = QAction(tr("Load Profile..."), self)
        load_profile_action.triggered.connect(self._load_profile_file)
        file_menu.addAction(load_profile_action)

        reload_profiles_action = QAction(tr("Reload Profiles"), self)
        reload_profiles_action.triggered.connect(self._reload_profiles)
        file_menu.addAction(reload_profiles_action)

        file_menu.addSeparator()

        quit_action = QAction(tr("Quit"), self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Connection menu
        conn_menu = menubar.addMenu(tr("Connection"))

        self.connect_action = QAction(tr("Connect"), self)
        self.connect_action.setShortcut("Ctrl+Shift+C")
        self.connect_action.triggered.connect(lambda: self.connection_panel._connect())
        conn_menu.addAction(self.connect_action)

        self.disconnect_action = QAction(tr("Disconnect"), self)
        self.disconnect_action.setShortcut("Ctrl+Shift+D")
        self.disconnect_action.triggered.connect(lambda: self.connection_panel._disconnect())
        self.disconnect_action.setEnabled(False)
        conn_menu.addAction(self.disconnect_action)

        # Settings menu
        settings_menu = menubar.addMenu(tr("Settings"))
        lang_menu = settings_menu.addMenu(tr("Language"))
        lang_group = QActionGroup(self)
        current_lang = get_language()
        for code, name in LANGUAGES.items():
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(code == current_lang)
            action.setData(code)
            action.triggered.connect(lambda checked, c=code: self._change_language(c))
            lang_group.addAction(action)
            lang_menu.addAction(action)

        # Help menu
        help_menu = menubar.addMenu(tr("Help"))

        about_action = QAction(tr("About"), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Connection panel
        self.connection_panel = ConnectionPanel(self.client, self.profile_manager)
        self.connection_panel.setMaximumWidth(350)
        self.connection_panel.setMinimumWidth(250)
        splitter.addWidget(self.connection_panel)

        # Right: Tab widget
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("", 10))

        self.dashboard_tab = DashboardTab(self.client, self.connection_panel)
        self.tabs.addTab(self.dashboard_tab, tr("Dashboard"))

        self.monitor_tab = MonitorTab(self.client, self.connection_panel)
        self.tabs.addTab(self.monitor_tab, tr("Monitor"))

        self.scanner_tab = ScannerTab(self.client, self.connection_panel)
        self.tabs.addTab(self.scanner_tab, tr("Scanner"))

        self.config_tab = ConfigTab(self.client, self.connection_panel)
        self.tabs.addTab(self.config_tab, tr("Configuration"))

        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def _setup_statusbar(self):
        self.statusBar().showMessage(tr("Ready — Select a port and connect to start"))

    def _connect_signals(self):
        self.connection_panel.connection_changed.connect(self._on_connection_changed)
        self.connection_panel.profile_changed.connect(self._on_profile_changed)
        self.connection_panel.status_message.connect(self.statusBar().showMessage)
        self.connection_panel.profiles_reloaded.connect(self._reload_profiles)

    def _on_connection_changed(self, connected: bool):
        self.connect_action.setEnabled(not connected)
        self.disconnect_action.setEnabled(connected)
        status = tr("Connected") if connected else tr("Disconnected")
        self.statusBar().showMessage(status)

    def _on_profile_changed(self, profile: DeviceProfile | None):
        self.dashboard_tab.set_profile(profile)
        self.monitor_tab.set_profile(profile)
        self.config_tab.set_profile(profile)
        if profile:
            self.statusBar().showMessage(f"Profile loaded: {profile.name}")

    def _open_profile_wizard(self):
        wizard = ProfileWizard(self.profile_manager.profiles_dir, self)
        if wizard.exec():
            self._reload_profiles()
            self.statusBar().showMessage(tr("New profile created and loaded"))

    def _load_profile_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Device Profile", "", "JSON Files (*.json)"
        )
        if path:
            try:
                from core.device_profiles import load_profile
                profile = load_profile(path)
                self.profile_manager.profiles[profile.name] = profile
                # Update combo
                combo = self.connection_panel.profile_combo
                if combo.findText(profile.name) == -1:
                    combo.addItem(profile.name)
                combo.setCurrentText(profile.name)
                self.statusBar().showMessage(f"Profile loaded: {profile.name}")
            except Exception as e:
                QMessageBox.warning(self, tr("Error"), f"Failed to load profile:\n{e}")

    def _reload_profiles(self):
        self.profile_manager.reload()
        combo = self.connection_panel.profile_combo
        current = combo.currentText()
        combo.clear()
        combo.addItem(tr("(No profile - Generic)"))
        for name in self.profile_manager.list_profiles():
            combo.addItem(name)
        idx = combo.findText(current)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        self.statusBar().showMessage(tr("Profiles reloaded"))

    def _change_language(self, lang_code: str):
        set_language(lang_code)
        save_language(lang_code)
        QMessageBox.information(
            self, tr("Restart Required"),
            tr("Language changed. Restart the application to apply.")
        )

    def _show_about(self):
        QMessageBox.about(
            self, "About ModbusTool",
            "<h2>ModbusTool</h2>"
            "<p>Universal Modbus RTU / TCP Configuration & Monitoring Tool for Linux</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Serial RTU and TCP/IP connections</li>"
            "<li>Bus scanning and device discovery</li>"
            "<li>Auto baud rate detection</li>"
            "<li>Register monitoring with continuous polling</li>"
            "<li>Device configuration with profile support</li>"
            "<li>Batch address assignment</li>"
            "<li>Raw TX/RX frame viewer</li>"
            "<li>Data logging with CSV export</li>"
            "</ul>"
            "<p>All function codes supported: FC01-FC06, FC15, FC16</p>"
            "<hr>"
            "<p>Developed by <a href='https://robotika.cloud/'>Robotika.cloud</a><br>"
            "Contact: <a href='mailto:kate@robotika.cloud'>kate@robotika.cloud</a></p>"
            "<p>Part of the <a href='https://nkz-os.org'>nkz-os.org</a> project</p>"
            "<p>License: <b>AGPL-3.0</b></p>"
        )

    def closeEvent(self, event):
        if self.client.connected:
            self.client.disconnect()
        event.accept()
