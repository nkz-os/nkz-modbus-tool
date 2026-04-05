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


class WriteConfirmDialog(QDialog):
    """Confirmation dialog before writing to a register."""

    def __init__(self, register_name: str, address: int, old_value, new_value, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Write")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        warning = QLabel("You are about to write to a device register.\nThis may change device behavior.")
        warning.setStyleSheet("color: #FF9800; font-weight: bold; padding: 8px;")
        layout.addWidget(warning)

        info = QGridLayout()
        info.addWidget(QLabel("Register:"), 0, 0)
        info.addWidget(QLabel(f"{register_name} (0x{address:04X})"), 0, 1)
        if old_value is not None:
            info.addWidget(QLabel("Current value:"), 1, 0)
            info.addWidget(QLabel(str(old_value)), 1, 1)
        info.addWidget(QLabel("New value:"), 2, 0)
        new_label = QLabel(str(new_value))
        new_label.setStyleSheet("font-weight: bold; color: #2196F3;")
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
            "No device profile selected.\n\n"
            "Select a profile from the connection panel to see\n"
            "device-specific configuration options.\n\n"
            "You can still use the Generic Register Read/Write tab below."
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
        read_all_btn = QPushButton("Read All Configuration")
        read_all_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; font-weight: bold; padding: 8px; }")
        read_all_btn.clicked.connect(self._read_all)
        self._scroll_layout.addWidget(read_all_btn)

        # Data registers group
        if self._profile.data_registers:
            data_group = QGroupBox("Data Registers (Read Only)")
            data_layout = QVBoxLayout(data_group)
            for reg in self._profile.data_registers:
                widget = self._create_register_row(reg, data_layout, readonly=True)
                self._register_widgets.append(widget)
            self._scroll_layout.addWidget(data_group)

        # Config registers group
        if self._profile.config_registers:
            config_group = QGroupBox("Configuration Registers (Read/Write)")
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
        read_btn = QPushButton("Read")
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

            write_btn = QPushButton("Write")
            write_btn.setFixedWidth(60)
            write_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
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
            value_label.setStyleSheet("color: #2196F3; font-weight: bold;")
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
            value_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

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
                        self, "Success",
                        f"Baud rate changed to {new_baud}.\n"
                        f"Serial port reconnected automatically.")
                else:
                    QMessageBox.warning(
                        self, "Partial Success",
                        f"Baud rate written to device, but reconnect failed:\n{msg_r}\n"
                        f"Reconnect manually at {new_baud} baud.")
            elif is_addr:
                self.connection_panel.slave_spin.setValue(raw_value)
                QMessageBox.information(
                    self, "Success",
                    f"Device address changed to {raw_value}.\n"
                    f"Slave address updated automatically.")
            else:
                QMessageBox.information(self, "Success",
                                        f"Written successfully.\n{msg}")
        else:
            QMessageBox.warning(self, "Write Failed", msg)

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
        write_group = QGroupBox("Write Single Register (FC 0x06)")
        write_layout = QFormLayout(write_group)

        self.write_addr = QSpinBox()
        self.write_addr.setRange(0, 65535)
        self.write_addr.setPrefix("0x")
        self.write_addr.setDisplayIntegerBase(16)
        write_layout.addRow("Register Address:", self.write_addr)

        self.write_value = QSpinBox()
        self.write_value.setRange(0, 65535)
        write_layout.addRow("Value (dec):", self.write_value)

        self.write_hex_label = QLabel("= 0x0000")
        self.write_value.valueChanged.connect(
            lambda v: self.write_hex_label.setText(f"= 0x{v:04X}")
        )
        write_layout.addRow("Value (hex):", self.write_hex_label)

        write_btn = QPushButton("Write Register")
        write_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 8px; }")
        write_btn.clicked.connect(self._write_single)
        write_layout.addRow(write_btn)

        layout.addWidget(write_group)

        # --- Write Multiple Registers ---
        multi_group = QGroupBox("Write Multiple Registers (FC 0x10)")
        multi_layout = QFormLayout(multi_group)

        self.multi_addr = QSpinBox()
        self.multi_addr.setRange(0, 65535)
        self.multi_addr.setPrefix("0x")
        self.multi_addr.setDisplayIntegerBase(16)
        multi_layout.addRow("Start Address:", self.multi_addr)

        self.multi_values = QLineEdit()
        self.multi_values.setPlaceholderText("Comma-separated: 100, 200, 300  or hex: 0x64, 0xC8")
        multi_layout.addRow("Values:", self.multi_values)

        multi_btn = QPushButton("Write Registers")
        multi_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 8px; }")
        multi_btn.clicked.connect(self._write_multiple)
        multi_layout.addRow(multi_btn)

        layout.addWidget(multi_group)

        # --- Write Coil ---
        coil_group = QGroupBox("Write Coil (FC 0x05)")
        coil_layout = QFormLayout(coil_group)

        self.coil_addr = QSpinBox()
        self.coil_addr.setRange(0, 65535)
        self.coil_addr.setPrefix("0x")
        self.coil_addr.setDisplayIntegerBase(16)
        coil_layout.addRow("Coil Address:", self.coil_addr)

        self.coil_value = QComboBox()
        self.coil_value.addItems(["OFF (0)", "ON (1)"])
        coil_layout.addRow("Value:", self.coil_value)

        coil_btn = QPushButton("Write Coil")
        coil_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 8px; }")
        coil_btn.clicked.connect(self._write_coil)
        coil_layout.addRow(coil_btn)

        layout.addWidget(coil_group)

        # --- Write Log ---
        self.write_log = QTextEdit()
        self.write_log.setReadOnly(True)
        self.write_log.setMaximumHeight(150)
        self.write_log.setFont(QFont("Monospace", 9))
        layout.addWidget(QLabel("Write Log:"))
        layout.addWidget(self.write_log)

        layout.addStretch()

    def _write_single(self):
        if not self.client.connected:
            self._log("ERROR: Not connected")
            return

        addr = self.write_addr.value()
        value = self.write_value.value()
        slave = self.connection_panel.slave_address

        dlg = WriteConfirmDialog("Register", addr, None, value, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        ok, msg = self.client.write_single_register(addr, value, slave)
        self._log(f"FC06 Write 0x{addr:04X} = {value} (0x{value:04X}) slave={slave} -> {msg}")

    def _write_multiple(self):
        if not self.client.connected:
            self._log("ERROR: Not connected")
            return

        addr = self.multi_addr.value()
        text = self.multi_values.text().strip()
        if not text:
            self._log("ERROR: No values specified")
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
            self._log(f"ERROR: Invalid values: {e}")
            return

        slave = self.connection_panel.slave_address
        dlg = WriteConfirmDialog("Registers", addr, None, values, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        ok, msg = self.client.write_multiple_registers(addr, values, slave)
        self._log(f"FC16 Write 0x{addr:04X} values={values} slave={slave} -> {msg}")

    def _write_coil(self):
        if not self.client.connected:
            self._log("ERROR: Not connected")
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
            "<b>Batch Address Assignment Wizard</b><br><br>"
            "This tool helps you assign unique addresses to multiple identical devices.<br>"
            "Connect one device at a time, and click 'Assign Next Address' to set it.<br><br>"
            "<b>Steps:</b><br>"
            "1. Set the starting address and baud rate below<br>"
            "2. Connect the first device (only one on the bus)<br>"
            "3. Click 'Read Current Config' to verify communication<br>"
            "4. Click 'Assign Next Address' to program the device<br>"
            "5. Disconnect, connect next device, repeat"
        )
        info.setWordWrap(True)
        info.setStyleSheet("padding: 12px; background-color: #FFF3E0; border-radius: 4px; margin-bottom: 8px;")
        layout.addWidget(info)

        # Config
        config_group = QGroupBox("Batch Configuration")
        config_layout = QFormLayout(config_group)

        self.current_addr = QSpinBox()
        self.current_addr.setRange(1, 247)
        self.current_addr.setValue(1)
        config_layout.addRow("Current device address:", self.current_addr)

        self.next_addr = QSpinBox()
        self.next_addr.setRange(1, 247)
        self.next_addr.setValue(2)
        config_layout.addRow("Next address to assign:", self.next_addr)

        self.target_baud = QComboBox()
        self.target_baud.addItems(["Keep current", "1200", "2400", "4800", "9600", "14400", "19200", "38400"])
        self.target_baud.setCurrentText("Keep current")
        config_layout.addRow("Target baud rate:", self.target_baud)

        layout.addWidget(config_group)

        # Actions
        btn_layout = QHBoxLayout()

        read_btn = QPushButton("Read Current Config")
        read_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px; }")
        read_btn.clicked.connect(self._read_current)
        btn_layout.addWidget(read_btn)

        self.assign_btn = QPushButton("Assign Next Address")
        self.assign_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        self.assign_btn.clicked.connect(self._assign_next)
        btn_layout.addWidget(self.assign_btn)

        layout.addLayout(btn_layout)

        # Status / Log
        self.batch_log = QTextEdit()
        self.batch_log.setReadOnly(True)
        self.batch_log.setFont(QFont("Monospace", 10))
        layout.addWidget(QLabel("Operation Log:"))
        layout.addWidget(self.batch_log)

    def set_profile(self, profile: DeviceProfile | None):
        self._profile = profile

    def _log(self, msg: str, color: str = "black"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.batch_log.append(f'<span style="color:{color}">[{ts}] {msg}</span>')

    def _read_current(self):
        if not self.client.connected:
            self._log("Not connected!", "red")
            return

        slave = self.current_addr.value()
        self._log(f"Reading config from slave {slave}...")

        if self._profile:
            addr_reg = self._profile.get_address_register()
            baud_reg = self._profile.get_baudrate_register()

            if addr_reg:
                ok, vals = self.client.read_holding_registers(addr_reg.address, 1, slave)
                if ok:
                    self._log(f"  Address register (0x{addr_reg.address:04X}): {vals[0]}", "#2196F3")
                else:
                    self._log(f"  Address register read failed: {vals}", "red")

            if baud_reg:
                ok, vals = self.client.read_holding_registers(baud_reg.address, 1, slave)
                if ok:
                    display = baud_reg.display_value(vals[0])
                    self._log(f"  Baud rate register (0x{baud_reg.address:04X}): {display}", "#2196F3")
                else:
                    self._log(f"  Baud rate register read failed: {vals}", "red")
        else:
            # Generic: try reading register 0
            ok, vals = self.client.read_holding_registers(0, 1, slave)
            if ok:
                self._log(f"  Register 0: {vals[0]}", "#2196F3")
            else:
                self._log(f"  Read failed: {vals}", "red")

    def _assign_next(self):
        if not self.client.connected:
            self._log("Not connected!", "red")
            return

        slave = self.current_addr.value()
        new_addr = self.next_addr.value()

        if slave == new_addr:
            self._log("Current and new address are the same!", "red")
            return

        reply = QMessageBox.question(
            self, "Confirm Address Change",
            f"Change device address from {slave} to {new_addr}?\n\n"
            "Make sure only ONE device is connected to the bus.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self._profile:
            addr_reg = self._profile.get_address_register()
            if addr_reg:
                ok, msg = self.client.write_single_register(addr_reg.address, new_addr, slave)
                if ok:
                    self._log(f"Address changed: {slave} -> {new_addr}", "#4CAF50")

                    # Change baud if requested
                    target = self.target_baud.currentText()
                    if target != "Keep current":
                        baud_reg = self._profile.get_baudrate_register()
                        if baud_reg:
                            raw = baud_reg.reverse_value_map(int(target))
                            if raw is not None:
                                ok2, msg2 = self.client.write_single_register(
                                    baud_reg.address, raw, new_addr
                                )
                                if ok2:
                                    self._log(f"Baud rate set to {target}", "#4CAF50")
                                else:
                                    self._log(f"Baud rate write failed: {msg2}", "red")

                    # Increment next address
                    self.next_addr.setValue(new_addr + 1)
                    self.current_addr.setValue(1)  # Reset to default for next device
                    self._log("Ready for next device. Connect it and click 'Read Current Config'.", "#FF9800")
                else:
                    self._log(f"Address write failed: {msg}", "red")
                return

        # Generic fallback — try common address registers
        self._log("No profile loaded. Trying common address registers...", "#FF9800")
        for reg_addr in [0x07D0, 0x0100, 0x0000]:
            ok, msg = self.client.write_single_register(reg_addr, new_addr, slave)
            if ok:
                self._log(f"Written to 0x{reg_addr:04X}: {slave} -> {new_addr}", "#4CAF50")
                self.next_addr.setValue(new_addr + 1)
                return
        self._log("All attempts failed. Load a device profile for reliable operation.", "red")


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
        tabs.addTab(self.profile_config, "Profile Registers")

        self.generic_config = GenericRegisterWidget(self.client, self.connection_panel)
        tabs.addTab(self.generic_config, "Generic Read/Write")

        self.batch_ops = BatchOperationsWidget(self.client, self.connection_panel)
        tabs.addTab(self.batch_ops, "Batch Operations")

        layout.addWidget(tabs)

    def set_profile(self, profile: DeviceProfile | None):
        self.profile_config.set_profile(profile)
        self.batch_ops.set_profile(profile)
