"""Connection panel — serial/TCP configuration, port detection, profiles."""

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QComboBox,
    QPushButton, QLineEdit, QSpinBox, QTabWidget, QFormLayout, QFrame,
    QDoubleSpinBox, QMessageBox,
)
from PyQt6.QtGui import QFont, QIcon, QPainter, QPixmap, QPen, QColor
from PyQt6.QtCore import QRect, QPoint

from core.modbus_client import ModbusClient, SerialConfig, TcpConfig
from core.device_profiles import ProfileManager, DeviceProfile
from core.i18n import tr


class StatusIndicator(QWidget):
    """LED-like connection status indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self._connected = False

    def set_connected(self, connected: bool):
        self._connected = connected
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(0, 200, 0) if self._connected else QColor(200, 0, 0)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()


class ConnectionPanel(QWidget):
    """Left panel for connection management."""

    connection_changed = pyqtSignal(bool)  # connected/disconnected
    profile_changed = pyqtSignal(object)   # DeviceProfile or None
    status_message = pyqtSignal(str)
    profiles_reloaded = pyqtSignal()       # request main window to reload profiles

    def __init__(self, client: ModbusClient, profile_manager: ProfileManager, parent=None):
        super().__init__(parent)
        self.client = client
        self.profile_manager = profile_manager
        self._current_profile: DeviceProfile | None = None
        self._setup_ui()
        self._refresh_ports()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # --- Status ---
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 4, 8, 4)
        self.status_led = StatusIndicator()
        self.status_label = QLabel(tr("Disconnected"))
        self.status_label.setFont(QFont("", -1, QFont.Weight.Bold))
        status_layout.addWidget(self.status_led)
        status_layout.addWidget(self.status_label, 1)
        layout.addWidget(status_frame)

        # --- Connection Type Tabs ---
        self.conn_tabs = QTabWidget()
        self.conn_tabs.setMaximumHeight(280)

        # Serial tab
        serial_widget = QWidget()
        serial_layout = QFormLayout(serial_widget)
        serial_layout.setContentsMargins(6, 6, 6, 6)

        port_row = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(140)
        self.refresh_btn = QPushButton()
        self.refresh_btn.setToolTip(tr("Refresh"))
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setIcon(self._make_refresh_icon())
        self.refresh_btn.setIconSize(self.refresh_btn.size() - self.refresh_btn.size() / 4)
        self.refresh_btn.clicked.connect(self._refresh_ports)
        port_row.addWidget(self.port_combo, 1)
        port_row.addWidget(self.refresh_btn)
        serial_layout.addRow(tr("Port:"), port_row)

        self.baud_combo = QComboBox()
        self.baud_combo.setEditable(True)
        for b in [1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200]:
            self.baud_combo.addItem(str(b))
        self.baud_combo.setCurrentText("9600")
        serial_layout.addRow(tr("Baud Rate:"), self.baud_combo)

        self.parity_combo = QComboBox()
        self.parity_combo.addItems([tr("None (N)"), tr("Even (E)"), tr("Odd (O)")])
        serial_layout.addRow(tr("Parity:"), self.parity_combo)

        self.databits_combo = QComboBox()
        self.databits_combo.addItems(["8", "7", "6", "5"])
        serial_layout.addRow(tr("Data Bits:"), self.databits_combo)

        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        serial_layout.addRow(tr("Stop Bits:"), self.stopbits_combo)

        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.1, 30.0)
        self.timeout_spin.setValue(1.0)
        self.timeout_spin.setSuffix(" s")
        self.timeout_spin.setSingleStep(0.1)
        serial_layout.addRow(tr("Timeout:"), self.timeout_spin)

        self.conn_tabs.addTab(serial_widget, tr("Serial RTU"))

        # TCP tab
        tcp_widget = QWidget()
        tcp_layout = QFormLayout(tcp_widget)
        tcp_layout.setContentsMargins(6, 6, 6, 6)

        self.tcp_host = QLineEdit("192.168.1.1")
        tcp_layout.addRow(tr("Host/IP:"), self.tcp_host)

        self.tcp_port = QSpinBox()
        self.tcp_port.setRange(1, 65535)
        self.tcp_port.setValue(502)
        tcp_layout.addRow(tr("Port:"), self.tcp_port)

        self.tcp_timeout = QDoubleSpinBox()
        self.tcp_timeout.setRange(0.1, 30.0)
        self.tcp_timeout.setValue(3.0)
        self.tcp_timeout.setSuffix(" s")
        tcp_layout.addRow(tr("Timeout:"), self.tcp_timeout)

        self.conn_tabs.addTab(tcp_widget, tr("Modbus TCP"))
        layout.addWidget(self.conn_tabs)

        # --- Connect/Disconnect buttons ---
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton(tr("Connect"))
        self.connect_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 6px; }")
        self.connect_btn.clicked.connect(self._connect)
        self.disconnect_btn = QPushButton(tr("Disconnect"))
        self.disconnect_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 6px; }")
        self.disconnect_btn.clicked.connect(self._disconnect)
        self.disconnect_btn.setEnabled(False)
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        layout.addLayout(btn_layout)

        # --- Device Profile ---
        profile_group = QGroupBox(tr("Device Profile"))
        profile_layout = QVBoxLayout(profile_group)
        profile_layout.setContentsMargins(6, 6, 6, 6)

        self.profile_combo = QComboBox()
        self.profile_combo.addItem(tr("(No profile - Generic)"))
        for name in self.profile_manager.list_profiles():
            self.profile_combo.addItem(name)
        self.profile_combo.currentTextChanged.connect(self._on_profile_changed)
        profile_layout.addWidget(self.profile_combo)

        self.profile_info = QLabel(tr("Select a profile to auto-configure parameters"))
        self.profile_info.setWordWrap(True)
        self.profile_info.setStyleSheet("color: #666; font-size: 11px;")
        profile_layout.addWidget(self.profile_info)

        profile_btn_layout = QHBoxLayout()
        self.apply_profile_btn = QPushButton(tr("Apply Defaults"))
        self.apply_profile_btn.clicked.connect(self._apply_profile_defaults)
        self.apply_profile_btn.setEnabled(False)
        profile_btn_layout.addWidget(self.apply_profile_btn)

        self.new_profile_btn = QPushButton(tr("New Profile..."))
        self.new_profile_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
        self.new_profile_btn.clicked.connect(self._open_wizard)
        profile_btn_layout.addWidget(self.new_profile_btn)
        profile_layout.addLayout(profile_btn_layout)

        layout.addWidget(profile_group)

        # --- Slave Address ---
        slave_group = QGroupBox(tr("Target Device"))
        slave_layout = QFormLayout(slave_group)
        slave_layout.setContentsMargins(6, 6, 6, 6)
        self.slave_spin = QSpinBox()
        self.slave_spin.setRange(1, 247)
        self.slave_spin.setValue(1)
        slave_layout.addRow(tr("Slave Address:"), self.slave_spin)
        layout.addWidget(slave_group)

        layout.addStretch()

        # Auto-refresh timer for ports
        self._port_timer = QTimer()
        self._port_timer.timeout.connect(self._refresh_ports_silent)
        self._port_timer.start(5000)

    @staticmethod
    def _make_refresh_icon() -> QIcon:
        """Draw a circular-arrows refresh icon."""
        size = 48
        pm = QPixmap(size, size)
        pm.fill(QColor(0, 0, 0, 0))
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#546E7A"), 3.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        # Draw arc (270 degrees, leaving a gap for the arrowhead)
        margin = 8
        rect = QRect(margin, margin, size - 2 * margin, size - 2 * margin)
        # Qt uses 1/16th of a degree; start at top-right, sweep 270 deg CCW
        p.drawArc(rect, 45 * 16, 270 * 16)
        # Arrowhead at the top-right end of the arc
        import math
        cx, cy = size / 2, size / 2
        r = (size - 2 * margin) / 2
        angle = math.radians(45)
        ax = cx + r * math.cos(angle)
        ay = cy - r * math.sin(angle)
        arrow_pen = QPen(QColor("#546E7A"), 2.5)
        arrow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(arrow_pen)
        p.setBrush(QColor("#546E7A"))
        from PyQt6.QtGui import QPolygonF
        from PyQt6.QtCore import QPointF
        # Arrow points along the arc tangent
        p.drawPolygon(QPolygonF([
            QPointF(ax, ay),
            QPointF(ax - 7, ay - 3),
            QPointF(ax - 2, ay + 6),
        ]))
        p.end()
        return QIcon(pm)

    def _refresh_ports(self):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        ports = ModbusClient.detect_serial_ports()
        for p in ports:
            self.port_combo.addItem(p["display"], p["device"])
        # Restore selection
        for i in range(self.port_combo.count()):
            if self.port_combo.itemText(i) == current:
                self.port_combo.setCurrentIndex(i)
                break
        if not ports:
            self.port_combo.addItem(tr("(No ports found)"))

    def _refresh_ports_silent(self):
        """Refresh ports without resetting selection if nothing changed."""
        current_count = self.port_combo.count()
        ports = ModbusClient.detect_serial_ports()
        if len(ports) != current_count or (current_count > 0 and
                self.port_combo.itemText(0) == "(No ports found)" and ports):
            self._refresh_ports()

    def _get_parity(self) -> str:
        text = self.parity_combo.currentText()
        if "E" in text:
            return "E"
        elif "O" in text:
            return "O"
        return "N"

    def _get_stopbits(self) -> float:
        return float(self.stopbits_combo.currentText())

    def _connect(self):
        if self.conn_tabs.currentIndex() == 0:
            # Serial
            port_data = self.port_combo.currentData()
            if not port_data:
                self.status_message.emit(tr("No port selected"))
                return
            config = SerialConfig(
                port=port_data,
                baudrate=int(self.baud_combo.currentText()),
                parity=self._get_parity(),
                stopbits=int(self._get_stopbits()),
                databits=int(self.databits_combo.currentText()),
                timeout=self.timeout_spin.value(),
            )
            ok, msg = self.client.connect_serial(config)
        else:
            # TCP
            config = TcpConfig(
                host=self.tcp_host.text(),
                port=self.tcp_port.value(),
                timeout=self.tcp_timeout.value(),
            )
            ok, msg = self.client.connect_tcp(config)

        if ok:
            self.status_led.set_connected(True)
            self.status_label.setText(tr("Connected"))
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.connection_changed.emit(True)
        else:
            QMessageBox.warning(self, tr("Connection Failed"), msg)

        self.status_message.emit(msg)

    def _disconnect(self):
        self.client.disconnect()
        self.status_led.set_connected(False)
        self.status_label.setText(tr("Disconnected"))
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.connection_changed.emit(False)
        self.status_message.emit(tr("Disconnected"))

    def _on_profile_changed(self, name: str):
        if name.startswith("("):
            self._current_profile = None
            self.profile_info.setText(tr("Select a profile to auto-configure parameters"))
            self.apply_profile_btn.setEnabled(False)
            self.profile_changed.emit(None)
        else:
            profile = self.profile_manager.get_profile(name)
            if profile:
                self._current_profile = profile
                self.profile_info.setText(
                    f"{profile.manufacturer}\n{profile.description}\n"
                    f"Default: addr={profile.default_address}, "
                    f"{profile.default_baudrate} baud, "
                    f"{profile.default_databits}{profile.default_parity}{profile.default_stopbits}"
                )
                self.apply_profile_btn.setEnabled(True)
                self.profile_changed.emit(profile)

    def _apply_profile_defaults(self):
        if not self._current_profile:
            return
        p = self._current_profile
        # Set baud rate
        self.baud_combo.setCurrentText(str(p.default_baudrate))
        # Set parity
        parity_map = {"N": 0, "E": 1, "O": 2}
        self.parity_combo.setCurrentIndex(parity_map.get(p.default_parity, 0))
        # Set databits
        databits_map = {"8": 0, "7": 1, "6": 2, "5": 3}
        self.databits_combo.setCurrentIndex(databits_map.get(str(p.default_databits), 0))
        # Set stopbits
        self.stopbits_combo.setCurrentIndex(0 if p.default_stopbits == 1 else 2)
        # Set slave address
        self.slave_spin.setValue(p.default_address)
        self.status_message.emit(f"Applied defaults from profile: {p.name}")

    @property
    def current_profile(self) -> DeviceProfile | None:
        return self._current_profile

    @property
    def slave_address(self) -> int:
        return self.slave_spin.value()

    def get_serial_port(self) -> str:
        return self.port_combo.currentData() or ""

    def get_baudrate(self) -> int:
        try:
            return int(self.baud_combo.currentText())
        except ValueError:
            return 9600

    def _open_wizard(self):
        from ui.profile_wizard import ProfileWizard
        wizard = ProfileWizard(self.profile_manager.profiles_dir, self)
        if wizard.exec():
            self.profiles_reloaded.emit()
