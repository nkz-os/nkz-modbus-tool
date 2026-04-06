"""Device configuration tab — read/write parameters, batch operations, profile editor."""

from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QSpinBox, QComboBox, QTableWidget, QTableWidgetItem, QSplitter,
    QHeaderView, QFormLayout, QMessageBox, QLineEdit, QTabWidget,
    QTextEdit, QFrame, QDialog, QDialogButtonBox, QGridLayout,
    QScrollArea,
)
from PyQt6.QtGui import QFont, QColor

from core.modbus_client import ModbusClient
from core.device_profiles import DeviceProfile, RegisterDef
from core.i18n import tr


class WriteConfirmDialog(QDialog):
    """Confirmation dialog before writing to a register."""

    def __init__(self, register_name: str, address: int, old_value, new_value, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Confirm Write"))
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        warning = QLabel(tr("You are about to write to a device register."))
        warning.setStyleSheet("color: #E65100; font-weight: bold; padding: 8px;")
        layout.addWidget(warning)

        info = QGridLayout()
        info.addWidget(QLabel(tr("Register") + ":"), 0, 0)
        info.addWidget(QLabel(f"{register_name} (0x{address:04X})"), 0, 1)
        if old_value is not None:
            info.addWidget(QLabel(tr("Current value") + ":"), 1, 0)
            info.addWidget(QLabel(str(old_value)), 1, 1)
        info.addWidget(QLabel(tr("New value") + ":"), 2, 0)
        new_label = QLabel(str(new_value))
        new_label.setStyleSheet("font-weight: bold; color: #1976D2;")
        info.addWidget(new_label, 2, 1)
        layout.addLayout(info)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class ProfileConfigWidget(QWidget):
    """Shows profile-specific registers with read/write controls."""

    def __init__(self, client: ModbusClient, connection_panel, parent=None):
        super().__init__(parent)
        self.client = client
        self.connection_panel = connection_panel
        self._profile: DeviceProfile | None = None
        self._register_widgets: list[dict] = []
        self._setup_ui()

    def _setup_ui(self):
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)

        self._no_profile_label = QLabel(
            tr("No profile selected") + "\n\n"
            + tr("Select a profile to auto-configure parameters") + "\n\n"
            + tr("Generic Read/Write")
        )
        self._no_profile_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_profile_label.setStyleSheet("color: #888; font-size: 13px; padding: 40px;")
        self._main_layout.addWidget(self._no_profile_label)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_content = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_area.setWidget(self._scroll_content)
        self._scroll_area.hide()
        self._main_layout.addWidget(self._scroll_area)

    def set_profile(self, profile: DeviceProfile | None):
        self._profile = profile
        self._rebuild_ui()

    def _rebuild_ui(self):
        # Clear old widgets
        while self._scroll_layout.count():
            item = self._scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._register_widgets.clear()

        if not self._profile:
            self._no_profile_label.show()
            self._scroll_area.hide()
            return

        self._no_profile_label.hide()
        self._scroll_area.show()

        # Profile header
        header = QLabel(f"<b>{self._profile.name}</b><br>{self._profile.description}")
        header.setStyleSheet("padding: 8px; background-color: #e3f2fd; border-radius: 4px;")
        self._scroll_layout.addWidget(header)

        # Read All button
        read_all_btn = QPushButton(tr("Read All Configuration"))
        read_all_btn.setStyleSheet("QPushButton { background-color: #7B1FA2; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }")
        read_all_btn.clicked.connect(self._read_all)
        self._scroll_layout.addWidget(read_all_btn)

        # Data registers group
        if self._profile.data_registers:
            data_group = QGroupBox(tr("Data Registers") + " (" + tr("Read") + ")")
            data_layout = QVBoxLayout(data_group)
            for reg in self._profile.data_registers:
                widget = self._create_register_row(reg, data_layout, readonly=True)
                self._register_widgets.append(widget)
            self._scroll_layout.addWidget(data_group)

        # Config registers group
        if self._profile.config_registers:
            config_group = QGroupBox(tr("Configuration Registers") + " (" + tr("Read") + "/" + tr("Write") + ")")
            config_layout = QVBoxLayout(config_group)
            for reg in self._profile.config_registers:
                widget = self._create_register_row(reg, config_layout, readonly=False)
                self._register_widgets.append(widget)
            self._scroll_layout.addWidget(config_group)

        self._scroll_layout.addStretch()

    def _create_register_row(self, reg: RegisterDef, parent_layout: QVBoxLayout, readonly: bool) -> dict:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("QFrame { padding: 4px; margin: 2px; }")
        row_layout = QHBoxLayout(frame)
        row_layout.setContentsMargins(8, 4, 8, 4)

        # Info
        info_layout = QVBoxLayout()
        name_label = QLabel(f"<b>{reg.name}</b> <span style='color:#888'>0x{reg.address:04X}</span>")
        info_layout.addWidget(name_label)
        desc_label = QLabel(reg.description)
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(desc_label)
        row_layout.addLayout(info_layout, 2)

        # Current value
        value_label = QLabel("—")
        value_label.setFont(QFont("Monospace", 12, QFont.Weight.Bold))
        value_label.setMinimumWidth(100)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_layout.addWidget(value_label)

        unit_label = QLabel(reg.unit)
        unit_label.setStyleSheet("color: #888;")
        row_layout.addWidget(unit_label)

        # Read button
        read_btn = QPushButton(tr("Read"))
        read_btn.setFixedWidth(60)
        read_btn.clicked.connect(lambda: self._read_register(reg, value_label))
        row_layout.addWidget(read_btn)

        # Write controls (if not readonly)
        write_spin = None
        write_combo = None
        write_btn = None
        if not readonly and "write" in reg.access:
            if reg.value_map:
                write_combo = QComboBox()
                for key, mapped in sorted(reg.value_map.items(), key=lambda x: int(x[0])):
                    write_combo.addItem(str(mapped), int(key))
                write_combo.setMinimumWidth(80)
                row_layout.addWidget(write_combo)
            else:
                write_spin = QSpinBox()
                write_spin.setRange(
                    reg.min_value if reg.min_value is not None else 0,
                    reg.max_value if reg.max_value is not None else 65535
                )
                write_spin.setMinimumWidth(80)
                row_layout.addWidget(write_spin)

            write_btn = QPushButton(tr("Write"))
            write_btn.setFixedWidth(60)
            write_btn.setStyleSheet("QPushButton { background-color: #E65100; color: white; border-radius: 3px; }")
            write_btn.clicked.connect(
                lambda checked, r=reg, vl=value_label, ws=write_spin, wc=write_combo:
                self._write_register(r, vl, ws, wc)
            )
            row_layout.addWidget(write_btn)

        parent_layout.addWidget(frame)

        return {
            "reg": reg,
            "value_label": value_label,
            "write_spin": write_spin,
            "write_combo": write_combo,
            "frame": frame,
        }

    def _read_register(self, reg: RegisterDef, value_label: QLabel):
        if not self.client.connected:
            value_label.setText("N/C")
            value_label.setStyleSheet("color: red;")
            return

        slave = self.connection_panel.slave_address
        fc = reg.function_code_read
        if fc == 3:
            ok, vals = self.client.read_holding_registers(reg.address, 1, slave)
        elif fc == 4:
            ok, vals = self.client.read_input_registers(reg.address, 1, slave)
        else:
            ok, vals = self.client.read_holding_registers(reg.address, 1, slave)

        if ok and vals:
            display = reg.display_value(vals[0])
            value_label.setText(display)
            value_label.setStyleSheet("color: #1976D2; font-weight: bold;")
        else:
            value_label.setText("ERR")
            value_label.setStyleSheet("color: red;")

    def _write_register(self, reg: RegisterDef, value_label: QLabel,
                        write_spin: QSpinBox | None, write_combo: QComboBox | None):
        if not self.client.connected:
            return

        if write_combo:
            raw_value = write_combo.currentData()
            display_value = write_combo.currentText()
        elif write_spin:
            raw_value = write_spin.value()
            display_value = str(raw_value)
        else:
            return

        # Read current value first
        slave = self.connection_panel.slave_address
        ok, vals = self.client.read_holding_registers(reg.address, 1, slave)
        old_value = reg.display_value(vals[0]) if ok and vals else "unknown"

        # Confirm dialog
        dlg = WriteConfirmDialog(reg.name, reg.address, old_value, display_value, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        # Write
        ok, msg = self.client.write_single_register(reg.address, raw_value, slave)
        if ok:
            value_label.setText(display_value)
            value_label.setStyleSheet("color: #2E7D32; font-weight: bold;")

            # Auto-reconnect if baud rate or address was changed
            is_baud = "baud" in reg.name.lower()
            is_addr = ("address" in reg.name.lower() and
                       "humidity" not in reg.name.lower())

            if is_baud:
                new_baud = int(display_value)
                self.connection_panel.baud_combo.setCurrentText(str(new_baud))
                ok_r, msg_r = self.client.update_serial_params(baudrate=new_baud)
                if ok_r:
                    QMessageBox.information(
                        self, tr("Success"),
                        f"{tr('Baud rate changed')} → {new_baud}.\n"
                        f"{tr('Serial port reconnected automatically.')}")
                else:
                    QMessageBox.warning(
                        self, tr("Partial Success"),
                        f"{tr('Baud rate written, but reconnect failed')}:\n{msg_r}")
            elif is_addr:
                self.connection_panel.slave_spin.setValue(raw_value)
                QMessageBox.information(
                    self, tr("Success"),
                    f"{tr('Device address changed')} → {raw_value}.")
            else:
                QMessageBox.information(self, tr("Success"), msg)
        else:
            QMessageBox.warning(self, tr("Write Failed"), msg)

    def _read_all(self):
        for w in self._register_widgets:
            self._read_register(w["reg"], w["value_label"])


class GenericRegisterWidget(QWidget):
    """Generic register read/write for any Modbus device."""

    def __init__(self, client: ModbusClient, connection_panel, parent=None):
        super().__init__(parent)
        self.client = client
        self.connection_panel = connection_panel
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        # --- Write Single Register ---
        write_group = QGroupBox(tr("Write Single Register (FC06)"))
        write_layout = QFormLayout(write_group)

        self.write_addr = QSpinBox()
        self.write_addr.setRange(0, 65535)
        self.write_addr.setPrefix("0x")
        self.write_addr.setDisplayIntegerBase(16)
        write_layout.addRow(tr("Register Address:"), self.write_addr)

        self.write_value = QSpinBox()
        self.write_value.setRange(0, 65535)
        write_layout.addRow(tr("Value (dec):"), self.write_value)

        self.write_hex_label = QLabel("= 0x0000")
        self.write_value.valueChanged.connect(
            lambda v: self.write_hex_label.setText(f"= 0x{v:04X}")
        )
        write_layout.addRow(tr("Value (hex):"), self.write_hex_label)

        write_btn = QPushButton(tr("Write Register"))
        write_btn.setStyleSheet("QPushButton { background-color: #E65100; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }")
        write_btn.clicked.connect(self._write_single)
        write_layout.addRow(write_btn)

        layout.addWidget(write_group)

        # --- Write Multiple Registers ---
        multi_group = QGroupBox(tr("Write Multiple Registers (FC16)"))
        multi_layout = QFormLayout(multi_group)

        self.multi_addr = QSpinBox()
        self.multi_addr.setRange(0, 65535)
        self.multi_addr.setPrefix("0x")
        self.multi_addr.setDisplayIntegerBase(16)
        multi_layout.addRow(tr("Start Address:"), self.multi_addr)

        self.multi_values = QLineEdit()
        self.multi_values.setPlaceholderText("100, 200, 300  /  0x64, 0xC8")
        multi_layout.addRow(tr("Values:"), self.multi_values)

        multi_btn = QPushButton(tr("Write Registers"))
        multi_btn.setStyleSheet("QPushButton { background-color: #E65100; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }")
        multi_btn.clicked.connect(self._write_multiple)
        multi_layout.addRow(multi_btn)

        layout.addWidget(multi_group)

        # --- Write Coil ---
        coil_group = QGroupBox(tr("Write Coil (FC05)"))
        coil_layout = QFormLayout(coil_group)

        self.coil_addr = QSpinBox()
        self.coil_addr.setRange(0, 65535)
        self.coil_addr.setPrefix("0x")
        self.coil_addr.setDisplayIntegerBase(16)
        coil_layout.addRow(tr("Coil Address:"), self.coil_addr)

        self.coil_value = QComboBox()
        self.coil_value.addItems(["OFF (0)", "ON (1)"])
        coil_layout.addRow(tr("Value:"), self.coil_value)

        coil_btn = QPushButton(tr("Write Coil"))
        coil_btn.setStyleSheet("QPushButton { background-color: #E65100; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }")
        coil_btn.clicked.connect(self._write_coil)
        coil_layout.addRow(coil_btn)

        layout.addWidget(coil_group)

        # --- Write Log ---
        self.write_log = QTextEdit()
        self.write_log.setReadOnly(True)
        self.write_log.setMaximumHeight(150)
        self.write_log.setFont(QFont("Monospace", 9))
        layout.addWidget(QLabel(tr("Write Log") + ":"))
        layout.addWidget(self.write_log)

        layout.addStretch()

    def _write_single(self):
        if not self.client.connected:
            self._log("ERROR: " + tr("Not connected"))
            return

        addr = self.write_addr.value()
        value = self.write_value.value()
        slave = self.connection_panel.slave_address

        dlg = WriteConfirmDialog(tr("Register"), addr, None, value, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        ok, msg = self.client.write_single_register(addr, value, slave)
        self._log(f"FC06 Write 0x{addr:04X} = {value} (0x{value:04X}) slave={slave} -> {msg}")

    def _write_multiple(self):
        if not self.client.connected:
            self._log("ERROR: " + tr("Not connected"))
            return

        addr = self.multi_addr.value()
        text = self.multi_values.text().strip()
        if not text:
            self._log("ERROR: No values")
            return

        try:
            values = []
            for part in text.split(","):
                part = part.strip()
                if part.startswith("0x") or part.startswith("0X"):
                    values.append(int(part, 16))
                else:
                    values.append(int(part))
        except ValueError as e:
            self._log(f"ERROR: {e}")
            return

        slave = self.connection_panel.slave_address
        dlg = WriteConfirmDialog(tr("Register"), addr, None, values, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        ok, msg = self.client.write_multiple_registers(addr, values, slave)
        self._log(f"FC16 Write 0x{addr:04X} values={values} slave={slave} -> {msg}")

    def _write_coil(self):
        if not self.client.connected:
            self._log("ERROR: " + tr("Not connected"))
            return

        addr = self.coil_addr.value()
        value = self.coil_value.currentIndex() == 1
        slave = self.connection_panel.slave_address

        ok, msg = self.client.write_single_coil(addr, value, slave)
        self._log(f"FC05 Write Coil 0x{addr:04X} = {value} slave={slave} -> {msg}")

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.write_log.append(f"[{ts}] {msg}")


class BatchOperationsWidget(QWidget):
    """Batch operations for changing parameters on multiple devices."""

    def __init__(self, client: ModbusClient, connection_panel, parent=None):
        super().__init__(parent)
        self.client = client
        self.connection_panel = connection_panel
        self._profile: DeviceProfile | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        # Instructions
        info = QLabel(
            f"<b>{tr('Batch Address Assignment')}</b><br><br>"
            f"{tr('Assign unique addresses to multiple identical devices.')}<br>"
            f"{tr('Connect one device at a time.')}<br>"
        )
        info.setWordWrap(True)
        info.setStyleSheet("padding: 12px; background-color: #FFF3E0; border-radius: 4px; margin-bottom: 8px;")
        layout.addWidget(info)

        # Config
        config_group = QGroupBox(tr("Batch Configuration"))
        config_layout = QFormLayout(config_group)

        self.current_addr = QSpinBox()
        self.current_addr.setRange(1, 247)
        self.current_addr.setValue(1)
        config_layout.addRow(tr("Current Address:"), self.current_addr)

        self.next_addr = QSpinBox()
        self.next_addr.setRange(1, 247)
        self.next_addr.setValue(2)
        config_layout.addRow(tr("Next Address:"), self.next_addr)

        self.target_baud = QComboBox()
        self.target_baud.addItems([tr("Keep current"), "1200", "2400", "4800", "9600", "14400", "19200", "38400"])
        self.target_baud.setCurrentIndex(0)
        config_layout.addRow(tr("Target baud rate:"), self.target_baud)

        layout.addWidget(config_group)

        # Actions
        btn_layout = QHBoxLayout()

        read_btn = QPushButton(tr("Read Current Config"))
        read_btn.setStyleSheet("QPushButton { background-color: #1976D2; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }")
        read_btn.clicked.connect(self._read_current)
        btn_layout.addWidget(read_btn)

        self.assign_btn = QPushButton(tr("Assign Next Address"))
        self.assign_btn.setStyleSheet("QPushButton { background-color: #2E7D32; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }")
        self.assign_btn.clicked.connect(self._assign_next)
        btn_layout.addWidget(self.assign_btn)

        layout.addLayout(btn_layout)

        # Status / Log
        self.batch_log = QTextEdit()
        self.batch_log.setReadOnly(True)
        self.batch_log.setFont(QFont("Monospace", 10))
        layout.addWidget(QLabel(tr("Operation Log") + ":"))
        layout.addWidget(self.batch_log)

    def set_profile(self, profile: DeviceProfile | None):
        self._profile = profile

    def _log(self, msg: str, color: str = "black"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.batch_log.append(f'<span style="color:{color}">[{ts}] {msg}</span>')

    def _read_current(self):
        if not self.client.connected:
            self._log(tr("Not connected") + "!", "red")
            return

        slave = self.current_addr.value()
        self._log(f"{tr('Reading configuration from device')} {slave}...")

        if self._profile:
            addr_reg = self._profile.get_address_register()
            baud_reg = self._profile.get_baudrate_register()

            if addr_reg:
                ok, vals = self.client.read_holding_registers(addr_reg.address, 1, slave)
                if ok:
                    self._log(f"  {tr('Address')} (0x{addr_reg.address:04X}): {vals[0]}", "#1976D2")
                else:
                    self._log(f"  {tr('Address')} read failed: {vals}", "red")

            if baud_reg:
                ok, vals = self.client.read_holding_registers(baud_reg.address, 1, slave)
                if ok:
                    display = baud_reg.display_value(vals[0])
                    self._log(f"  {tr('Baud Rate')} (0x{baud_reg.address:04X}): {display}", "#1976D2")
                else:
                    self._log(f"  {tr('Baud Rate')} read failed: {vals}", "red")
        else:
            # Generic: try reading register 0
            ok, vals = self.client.read_holding_registers(0, 1, slave)
            if ok:
                self._log(f"  Register 0: {vals[0]}", "#1976D2")
            else:
                self._log(f"  Read failed: {vals}", "red")

    def _assign_next(self):
        if not self.client.connected:
            self._log(tr("Not connected") + "!", "red")
            return

        slave = self.current_addr.value()
        new_addr = self.next_addr.value()

        if slave == new_addr:
            self._log(tr("Current and new address are the same!"), "red")
            return

        reply = QMessageBox.question(
            self, tr("Confirm Address Change"),
            f"{tr('Change device address from')} {slave} → {new_addr}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self._profile:
            addr_reg = self._profile.get_address_register()
            if addr_reg:
                ok, msg = self.client.write_single_register(addr_reg.address, new_addr, slave)
                if ok:
                    self._log(f"{tr('Address changed')}: {slave} → {new_addr}", "#2E7D32")

                    # Change baud if requested
                    target = self.target_baud.currentText()
                    if target != tr("Keep current"):
                        baud_reg = self._profile.get_baudrate_register()
                        if baud_reg:
                            raw = baud_reg.reverse_value_map(int(target))
                            if raw is not None:
                                ok2, msg2 = self.client.write_single_register(
                                    baud_reg.address, raw, new_addr
                                )
                                if ok2:
                                    self._log(f"{tr('Baud Rate')} → {target}", "#2E7D32")
                                else:
                                    self._log(f"{tr('Baud Rate')} write failed: {msg2}", "red")

                    # Increment next address
                    self.next_addr.setValue(new_addr + 1)
                    self.current_addr.setValue(1)  # Reset to default for next device
                    self._log(tr("Ready for next device."), "#E65100")
                else:
                    self._log(f"{tr('Address')} write failed: {msg}", "red")
                return

        # Generic fallback — try common address registers
        self._log(tr("No profile selected") + ". Trying common registers...", "#E65100")
        for reg_addr in [0x07D0, 0x0100, 0x0000]:
            ok, msg = self.client.write_single_register(reg_addr, new_addr, slave)
            if ok:
                self._log(f"Written 0x{reg_addr:04X}: {slave} → {new_addr}", "#2E7D32")
                self.next_addr.setValue(new_addr + 1)
                return
        self._log(tr("All attempts failed. Load a device profile."), "red")


class ConfigTab(QWidget):
    """Device configuration tab — combines profile config, generic, and batch."""

    def __init__(self, client: ModbusClient, connection_panel, parent=None):
        super().__init__(parent)
        self.client = client
        self.connection_panel = connection_panel
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        tabs = QTabWidget()

        self.profile_config = ProfileConfigWidget(self.client, self.connection_panel)
        tabs.addTab(self.profile_config, tr("Profile Registers"))

        self.generic_config = GenericRegisterWidget(self.client, self.connection_panel)
        tabs.addTab(self.generic_config, tr("Generic Read/Write"))

        self.batch_ops = BatchOperationsWidget(self.client, self.connection_panel)
        tabs.addTab(self.batch_ops, tr("Batch Operations"))

        layout.addWidget(tabs)

    def set_profile(self, profile: DeviceProfile | None):
        self.profile_config.set_profile(profile)
        self.batch_ops.set_profile(profile)
