"""Dashboard tab — human-friendly sensor monitoring and quick actions."""

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QGridLayout, QFrame, QScrollArea, QSplitter, QTextEdit, QSpinBox,
    QComboBox, QFormLayout, QMessageBox, QDoubleSpinBox,
)
from PyQt6.QtGui import QFont, QColor

from core.modbus_client import ModbusClient
from core.device_profiles import DeviceProfile, RegisterDef
from core.i18n import tr


class SensorValueCard(QFrame):
    """Big, readable card showing a single sensor value."""

    def __init__(self, name: str, unit: str = "", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            SensorValueCard {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        self.setMinimumSize(200, 120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Name
        self._name_label = QLabel(name)
        self._name_label.setFont(QFont("", 11))
        self._name_label.setStyleSheet("color: #666; border: none;")
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._name_label)

        # Value
        self._value_label = QLabel("—")
        self._value_label.setFont(QFont("", 28, QFont.Weight.Bold))
        self._value_label.setStyleSheet("color: #333; border: none;")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._value_label)

        # Unit
        self._unit_label = QLabel(unit)
        self._unit_label.setFont(QFont("", 10))
        self._unit_label.setStyleSheet("color: #999; border: none;")
        self._unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._unit_label)

        # Timestamp
        self._time_label = QLabel("")
        self._time_label.setFont(QFont("", 8))
        self._time_label.setStyleSheet("color: #bbb; border: none;")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._time_label)

    def set_value(self, value: str, unit: str = None):
        self._value_label.setText(value)
        self._value_label.setStyleSheet("color: #1565C0; border: none;")
        self._time_label.setText(datetime.now().strftime("%H:%M:%S"))
        self.setStyleSheet("""
            SensorValueCard {
                background-color: white;
                border: 2px solid #42A5F5;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        if unit is not None:
            self._unit_label.setText(unit)

    def set_error(self, msg: str = "Error"):
        self._value_label.setText(msg)
        self._value_label.setStyleSheet("color: #D32F2F; border: none;")
        self._time_label.setText(datetime.now().strftime("%H:%M:%S"))
        self.setStyleSheet("""
            SensorValueCard {
                background-color: #FFEBEE;
                border: 2px solid #EF5350;
                border-radius: 8px;
                padding: 12px;
            }
        """)

    def set_waiting(self):
        self._value_label.setText("...")
        self._value_label.setStyleSheet("color: #FF9800; border: none;")


class DeviceInfoCard(QFrame):
    """Card showing current device configuration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            DeviceInfoCard {
                background-color: #F3E5F5;
                border: 2px solid #CE93D8;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        title = QLabel("Device Configuration")
        title.setFont(QFont("", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: #6A1B9A; border: none;")
        layout.addWidget(title)

        self._info_label = QLabel("Not read yet")
        self._info_label.setFont(QFont("", 10))
        self._info_label.setStyleSheet("color: #333; border: none;")
        self._info_label.setWordWrap(True)
        layout.addWidget(self._info_label)

    def set_info(self, lines: list[str]):
        self._info_label.setText("\n".join(lines))


class DashboardTab(QWidget):
    """Human-friendly sensor dashboard."""

    def __init__(self, client: ModbusClient, connection_panel, parent=None):
        super().__init__(parent)
        self.client = client
        self.connection_panel = connection_panel
        self._profile: DeviceProfile | None = None
        self._value_cards: dict[str, SensorValueCard] = {}
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._auto_read_data)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Top: status + quick actions
        top_bar = QHBoxLayout()

        self._status_label = QLabel("Select a device profile and connect to start")
        self._status_label.setFont(QFont("", 11))
        self._status_label.setStyleSheet("color: #666; padding: 4px;")
        top_bar.addWidget(self._status_label, 1)

        layout.addLayout(top_bar)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # --- Upper: sensor values + actions ---
        upper_widget = QWidget()
        upper_layout = QVBoxLayout(upper_widget)
        upper_layout.setContentsMargins(0, 0, 0, 0)

        # Value cards area
        self._cards_area = QWidget()
        self._cards_layout = QGridLayout(self._cards_area)
        self._cards_layout.setSpacing(12)
        upper_layout.addWidget(self._cards_area)

        # Action buttons
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.setSpacing(8)

        self._read_data_btn = QPushButton(tr("Read Sensor Data"))
        self._read_data_btn.setFont(QFont("", 11, QFont.Weight.Bold))
        self._read_data_btn.setMinimumHeight(44)
        self._read_data_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2; color: white;
                border-radius: 6px; padding: 8px 20px;
            }
            QPushButton:hover { background-color: #1565C0; }
            QPushButton:disabled { background-color: #BDBDBD; }
        """)
        self._read_data_btn.clicked.connect(self._read_data)
        actions_layout.addWidget(self._read_data_btn)

        self._read_config_btn = QPushButton(tr("Read Device Config"))
        self._read_config_btn.setFont(QFont("", 11, QFont.Weight.Bold))
        self._read_config_btn.setMinimumHeight(44)
        self._read_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #7B1FA2; color: white;
                border-radius: 6px; padding: 8px 20px;
            }
            QPushButton:hover { background-color: #6A1B9A; }
            QPushButton:disabled { background-color: #BDBDBD; }
        """)
        self._read_config_btn.clicked.connect(self._read_config)
        actions_layout.addWidget(self._read_config_btn)

        # Auto-read toggle
        auto_frame = QVBoxLayout()
        auto_row = QHBoxLayout()
        self._auto_btn = QPushButton(tr("Auto-Read"))
        self._auto_btn.setCheckable(True)
        self._auto_btn.setMinimumHeight(44)
        self._auto_btn.setFont(QFont("", 11, QFont.Weight.Bold))
        self._auto_btn.setStyleSheet("""
            QPushButton {
                background-color: #388E3C; color: white;
                border-radius: 6px; padding: 8px 20px;
            }
            QPushButton:checked {
                background-color: #D32F2F;
            }
            QPushButton:hover { background-color: #2E7D32; }
            QPushButton:checked:hover { background-color: #C62828; }
            QPushButton:disabled { background-color: #BDBDBD; }
        """)
        self._auto_btn.clicked.connect(self._toggle_auto_read)
        auto_row.addWidget(self._auto_btn)

        auto_row.addWidget(QLabel("every"))
        self._auto_interval = QDoubleSpinBox()
        self._auto_interval.setRange(0.5, 60)
        self._auto_interval.setValue(2.0)
        self._auto_interval.setSuffix(" s")
        self._auto_interval.setMinimumHeight(36)
        auto_row.addWidget(self._auto_interval)
        auto_frame.addLayout(auto_row)

        actions_layout.addLayout(auto_frame)

        upper_layout.addWidget(actions_group)

        # Device info card
        self._device_info = DeviceInfoCard()
        upper_layout.addWidget(self._device_info)

        splitter.addWidget(upper_widget)

        # --- Lower: activity log (plain language) ---
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)

        log_header = QHBoxLayout()
        log_header.addWidget(QLabel(tr("Activity Log")))
        log_header.addStretch()
        clear_log_btn = QPushButton(tr("Clear"))
        clear_log_btn.setFixedWidth(60)
        clear_log_btn.clicked.connect(lambda: self._log_text.clear())
        log_header.addWidget(clear_log_btn)
        log_layout.addLayout(log_header)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFont(QFont("", 10))
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        log_layout.addWidget(self._log_text)

        splitter.addWidget(log_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # No-profile placeholder
        self._no_profile_label = QLabel(
            tr("Select a device profile to see sensor values")
        )
        self._no_profile_label.setFont(QFont("", 14))
        self._no_profile_label.setStyleSheet("color: #999;")
        self._no_profile_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cards_layout.addWidget(self._no_profile_label, 0, 0)

    def set_profile(self, profile: DeviceProfile | None):
        self._profile = profile
        self._stop_auto()
        self._rebuild_cards()

    def _rebuild_cards(self):
        # Remove old cards
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._value_cards.clear()

        if not self._profile:
            self._no_profile_label = QLabel(
                tr("Select a device profile to see sensor values")
            )
            self._no_profile_label.setFont(QFont("", 14))
            self._no_profile_label.setStyleSheet("color: #999;")
            self._no_profile_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._cards_layout.addWidget(self._no_profile_label, 0, 0)
            self._status_label.setText(tr("No profile selected"))
            return

        self._status_label.setText(
            f"<b>{self._profile.name}</b> — "
            f"Default: address {self._profile.default_address}, "
            f"{self._profile.default_baudrate} baud"
        )

        # Create cards for data registers
        col = 0
        row = 0
        max_cols = 3

        if self._profile.data_registers:
            for reg in self._profile.data_registers:
                card = SensorValueCard(reg.name, reg.unit)
                self._cards_layout.addWidget(card, row, col)
                self._value_cards[f"data_{reg.address}"] = card
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

        # Config registers as smaller cards
        if col > 0:
            row += 1
            col = 0

        for reg in self._profile.config_registers:
            unit = reg.unit
            if reg.value_map:
                unit = "baud" if "baud" in reg.name.lower() else ""
            card = SensorValueCard(reg.name, unit)
            self._cards_layout.addWidget(card, row, col)
            self._value_cards[f"config_{reg.address}"] = card
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _log(self, msg: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        colors = {
            "info": "#333",
            "success": "#2E7D32",
            "error": "#D32F2F",
            "warning": "#F57F17",
            "data": "#1565C0",
        }
        color = colors.get(level, "#333")
        self._log_text.append(
            f'<span style="color:#999">{ts}</span> '
            f'<span style="color:{color}">{msg}</span>'
        )
        scrollbar = self._log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _read_data(self):
        if not self.client.connected:
            self._log("Not connected. Connect first using the left panel.", "error")
            return
        if not self._profile:
            self._log("No profile selected.", "error")
            return
        if not self._profile.data_registers:
            self._log("This profile has no data registers defined.", "warning")
            return

        slave = self.connection_panel.slave_address
        self._log(f"Reading sensor data from device {slave}...")

        for reg in self._profile.data_registers:
            key = f"data_{reg.address}"
            card = self._value_cards.get(key)
            if card:
                card.set_waiting()

            fc = reg.function_code_read
            if fc == 4:
                ok, vals = self.client.read_input_registers(reg.address, 1, slave)
            else:
                ok, vals = self.client.read_holding_registers(reg.address, 1, slave)

            if ok and vals:
                display = reg.display_value(vals[0])
                if card:
                    card.set_value(display)
                self._log(
                    f"<b>{reg.name}</b>: {display} {reg.unit}",
                    "data"
                )
            else:
                error_msg = vals if isinstance(vals, str) else "No response"
                if card:
                    card.set_error("No response")
                self._log(
                    f"<b>{reg.name}</b>: failed to read — {error_msg}",
                    "error"
                )

    def _read_config(self):
        if not self.client.connected:
            self._log("Not connected. Connect first using the left panel.", "error")
            return
        if not self._profile:
            self._log("No profile selected.", "error")
            return

        slave = self.connection_panel.slave_address
        self._log(f"Reading configuration from device {slave}...")

        info_lines = []

        for reg in self._profile.config_registers:
            key = f"config_{reg.address}"
            card = self._value_cards.get(key)
            if card:
                card.set_waiting()

            ok, vals = self.client.read_holding_registers(reg.address, 1, slave)

            if ok and vals:
                raw = vals[0]
                display = reg.display_value(raw)

                if card:
                    card.set_value(display)

                # Human-readable description
                if "baud" in reg.name.lower():
                    self._log(
                        f"<b>{reg.name}</b>: {display} baud",
                        "data"
                    )
                    info_lines.append(f"Baud rate: {display}")
                elif "address" in reg.name.lower():
                    self._log(
                        f"<b>{reg.name}</b>: {display}",
                        "data"
                    )
                    info_lines.append(f"Address: {display}")
                elif "calibr" in reg.name.lower() or "correct" in reg.name.lower():
                    self._log(
                        f"<b>{reg.name}</b>: {display} {reg.unit}",
                        "data"
                    )
                    info_lines.append(f"{reg.name}: {display} {reg.unit}")
                else:
                    self._log(
                        f"<b>{reg.name}</b>: {display} {reg.unit}",
                        "data"
                    )
                    info_lines.append(f"{reg.name}: {display} {reg.unit}")
            else:
                error_msg = vals if isinstance(vals, str) else "No response"
                if card:
                    card.set_error("No response")
                self._log(f"<b>{reg.name}</b>: failed — {error_msg}", "error")
                info_lines.append(f"{reg.name}: ERROR")

        if info_lines:
            self._device_info.set_info(info_lines)

    def _toggle_auto_read(self, checked):
        if checked:
            if not self.client.connected or not self._profile:
                self._auto_btn.setChecked(False)
                self._log("Connect and select a profile first.", "error")
                return
            interval = int(self._auto_interval.value() * 1000)
            self._poll_timer.start(interval)
            self._auto_btn.setText(tr("Stop Auto-Read"))
            self._log(
                f"Auto-read started (every {self._auto_interval.value():.1f}s)",
                "success"
            )
        else:
            self._stop_auto()

    def _stop_auto(self):
        self._poll_timer.stop()
        self._auto_btn.setChecked(False)
        self._auto_btn.setText(tr("Auto-Read"))

    def _auto_read_data(self):
        if not self.client.connected:
            self._stop_auto()
            self._log("Connection lost — auto-read stopped.", "error")
            return
        self._read_data()
