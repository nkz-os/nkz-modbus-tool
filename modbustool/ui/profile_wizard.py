"""Profile creation wizard — step-by-step GUI to create device JSON profiles."""

import os
import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QComboBox, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTextEdit, QCheckBox, QDoubleSpinBox, QFrame, QFileDialog,
    QWidget, QGridLayout, QDialog, QDialogButtonBox,
)
from PyQt6.QtGui import QFont

from core.device_profiles import DeviceProfile, RegisterDef, save_profile
from core.i18n import tr


# ─── Step 1: Device Info ─────────────────────────────────────────────────────

class DeviceInfoPage(QWizardPage):
    """Step 1: Basic device information and communication defaults."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(tr("Device Information"))
        self.setSubTitle(tr(
            "Enter the basic information about the device. "
            "Check the device manual or datasheet."
        ))

        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Soil Moisture & Temperature Sensor")
        layout.addRow(tr("Device Name:"), self.name_edit)
        self.registerField("device_name*", self.name_edit)

        self.manufacturer_edit = QLineEdit()
        self.manufacturer_edit.setPlaceholderText("e.g. Shandong Renke")
        layout.addRow(tr("Manufacturer:"), self.manufacturer_edit)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("e.g. RS485 Modbus RTU soil sensor, 3 channels")
        layout.addRow(tr("Description:"), self.description_edit)

        # Communication defaults
        layout.addRow(QLabel(""))
        header = QLabel(tr("Communication Defaults"))
        header.setFont(QFont("", 11, QFont.Weight.Bold))
        layout.addRow(header)

        info = QLabel(tr("Factory default values for new devices."))
        info.setStyleSheet("color: #666; font-size: 11px;")
        layout.addRow(info)

        self.default_addr = QSpinBox()
        self.default_addr.setRange(1, 247)
        self.default_addr.setValue(1)
        layout.addRow(tr("Default Address:"), self.default_addr)

        self.default_baud = QComboBox()
        self.default_baud.addItems(["1200", "2400", "4800", "9600", "14400", "19200", "38400", "57600", "115200"])
        self.default_baud.setCurrentText("9600")
        layout.addRow(tr("Default Baud Rate:"), self.default_baud)

        self.default_parity = QComboBox()
        self.default_parity.addItems([tr("None (N)"), tr("Even (E)"), tr("Odd (O)")])
        layout.addRow(tr("Default Parity:"), self.default_parity)

        self.default_databits = QComboBox()
        self.default_databits.addItems(["8", "7"])
        layout.addRow(tr("Data Bits:"), self.default_databits)

        self.default_stopbits = QComboBox()
        self.default_stopbits.addItems(["1", "2"])
        layout.addRow(tr("Stop Bits:"), self.default_stopbits)


# ─── Register Editor Dialog ───────────────────────────────────────────────────

class RegisterEditorDialog(QDialog):
    """Dialog for adding/editing a single register."""

    def __init__(self, register: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Add Register") if not register else tr("Edit Register"))
        self.setMinimumWidth(500)
        self._result = None

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(8)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Temperature, Humidity, Device Address...")
        form.addRow(tr("Name:"), self.name_edit)

        # Address
        addr_layout = QHBoxLayout()
        self.addr_spin = QSpinBox()
        self.addr_spin.setRange(0, 65535)
        self.addr_spin.setPrefix("0x")
        self.addr_spin.setDisplayIntegerBase(16)
        addr_layout.addWidget(self.addr_spin)
        self.addr_decimal = QLabel("= 0 decimal")
        self.addr_spin.valueChanged.connect(
            lambda v: self.addr_decimal.setText(f"= {v} decimal")
        )
        addr_layout.addWidget(self.addr_decimal)
        addr_layout.addStretch()
        form.addRow(tr("Register Address:"), addr_layout)

        # Description
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("e.g. Ambient temperature (value / 10)")
        form.addRow(tr("Description:"), self.desc_edit)

        # Unit
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g. \u00b0C, %RH, \u00b5mol/m\u00b2\u00b7s, ppm")
        form.addRow(tr("Unit:"), self.unit_edit)

        # Data type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["uint16", "int16", "uint32", "int32", "float32"])
        form.addRow(tr("Data type:"), self.type_combo)

        # Scale
        scale_layout = QHBoxLayout()
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.0001, 10000)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setDecimals(4)
        scale_layout.addWidget(self.scale_spin)
        scale_info = QLabel(tr("e.g. 0.1 means raw 235 = 23.5"))
        scale_info.setStyleSheet("color: #666; font-size: 11px;")
        scale_layout.addWidget(scale_info)
        form.addRow(tr("Scale factor:"), scale_layout)

        # Access
        self.access_combo = QComboBox()
        self.access_combo.addItems(["read", "readwrite"])
        form.addRow(tr("Access:"), self.access_combo)

        # Function codes
        self.fc_read_combo = QComboBox()
        self.fc_read_combo.addItems(["03 - Holding Registers", "04 - Input Registers"])
        form.addRow(tr("Read function:"), self.fc_read_combo)

        self.fc_write_combo = QComboBox()
        self.fc_write_combo.addItems(["06 - Write Single Register", "16 - Write Multiple Registers"])
        form.addRow(tr("Write function:"), self.fc_write_combo)

        # Min/Max
        range_layout = QHBoxLayout()
        self.has_range = QCheckBox(tr("Limit values"))
        range_layout.addWidget(self.has_range)
        self.min_spin = QSpinBox()
        self.min_spin.setRange(-32768, 65535)
        self.min_spin.setValue(0)
        self.min_spin.setPrefix("min: ")
        self.min_spin.setEnabled(False)
        range_layout.addWidget(self.min_spin)
        self.max_spin = QSpinBox()
        self.max_spin.setRange(-32768, 65535)
        self.max_spin.setValue(65535)
        self.max_spin.setPrefix("max: ")
        self.max_spin.setEnabled(False)
        range_layout.addWidget(self.max_spin)
        self.has_range.toggled.connect(self.min_spin.setEnabled)
        self.has_range.toggled.connect(self.max_spin.setEnabled)
        form.addRow(tr("Value range:"), range_layout)

        # Value map
        map_layout = QVBoxLayout()
        self.has_map = QCheckBox(
            tr("Has value mapping (e.g. 1=1200 baud, 2=2400...)")
        )
        map_layout.addWidget(self.has_map)

        self.map_table = QTableWidget(0, 2)
        self.map_table.setHorizontalHeaderLabels([tr("Register Value"), tr("Meaning")])
        self.map_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.map_table.setMaximumHeight(150)
        self.map_table.setEnabled(False)
        map_layout.addWidget(self.map_table)

        map_btn_layout = QHBoxLayout()
        self.add_map_btn = QPushButton(tr("Add Mapping"))
        self.add_map_btn.setEnabled(False)
        self.add_map_btn.clicked.connect(self._add_map_row)
        self.remove_map_btn = QPushButton(tr("Remove Selected"))
        self.remove_map_btn.setEnabled(False)
        self.remove_map_btn.clicked.connect(self._remove_map_row)
        map_btn_layout.addWidget(self.add_map_btn)
        map_btn_layout.addWidget(self.remove_map_btn)
        map_btn_layout.addStretch()
        map_layout.addLayout(map_btn_layout)

        self.has_map.toggled.connect(self.map_table.setEnabled)
        self.has_map.toggled.connect(self.add_map_btn.setEnabled)
        self.has_map.toggled.connect(self.remove_map_btn.setEnabled)

        form.addRow(tr("Value mapping:"), map_layout)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Pre-fill if editing
        if register:
            self._load(register)

    def _add_map_row(self):
        row = self.map_table.rowCount()
        self.map_table.insertRow(row)
        self.map_table.setItem(row, 0, QTableWidgetItem(""))
        self.map_table.setItem(row, 1, QTableWidgetItem(""))

    def _remove_map_row(self):
        row = self.map_table.currentRow()
        if row >= 0:
            self.map_table.removeRow(row)

    def _load(self, reg: dict):
        self.name_edit.setText(reg.get("name", ""))
        self.addr_spin.setValue(reg.get("address", 0))
        self.desc_edit.setText(reg.get("description", ""))
        self.unit_edit.setText(reg.get("unit", ""))
        dt = reg.get("data_type", "uint16")
        idx = self.type_combo.findText(dt)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.scale_spin.setValue(reg.get("scale", 1.0))
        self.access_combo.setCurrentText(reg.get("access", "read"))

        fc_read = reg.get("function_code_read", reg.get("function_code", 3))
        self.fc_read_combo.setCurrentIndex(0 if fc_read == 3 else 1)
        fc_write = reg.get("function_code_write", 6)
        self.fc_write_combo.setCurrentIndex(0 if fc_write == 6 else 1)

        if reg.get("min") is not None or reg.get("max") is not None:
            self.has_range.setChecked(True)
            if reg.get("min") is not None:
                self.min_spin.setValue(reg["min"])
            if reg.get("max") is not None:
                self.max_spin.setValue(reg["max"])

        if reg.get("value_map"):
            self.has_map.setChecked(True)
            for key, val in reg["value_map"].items():
                row = self.map_table.rowCount()
                self.map_table.insertRow(row)
                self.map_table.setItem(row, 0, QTableWidgetItem(str(key)))
                self.map_table.setItem(row, 1, QTableWidgetItem(str(val)))

    def _accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, tr("Error"), tr("Enter a register name."))
            return

        reg = {
            "name": name,
            "address": self.addr_spin.value(),
            "description": self.desc_edit.text().strip(),
            "unit": self.unit_edit.text().strip(),
            "data_type": self.type_combo.currentText(),
            "scale": self.scale_spin.value(),
            "access": self.access_combo.currentText(),
            "function_code_read": 3 if self.fc_read_combo.currentIndex() == 0 else 4,
            "function_code_write": 6 if self.fc_write_combo.currentIndex() == 0 else 16,
        }

        if self.has_range.isChecked():
            reg["min"] = self.min_spin.value()
            reg["max"] = self.max_spin.value()

        if self.has_map.isChecked():
            value_map = {}
            for row in range(self.map_table.rowCount()):
                key_item = self.map_table.item(row, 0)
                val_item = self.map_table.item(row, 1)
                if key_item and val_item and key_item.text().strip() and val_item.text().strip():
                    try:
                        value_map[key_item.text().strip()] = int(val_item.text().strip())
                    except ValueError:
                        value_map[key_item.text().strip()] = val_item.text().strip()
            if value_map:
                reg["value_map"] = value_map

        self._result = reg
        self.accept()

    def get_result(self) -> dict | None:
        return self._result


# ─── Step 2: Data Registers ──────────────────────────────────────────────────

class RegisterListPage(QWizardPage):
    """Step for adding registers (data or config) with a table and add/edit/remove buttons."""

    def __init__(self, title: str, subtitle: str, reg_type: str, parent=None):
        super().__init__(parent)
        self.setTitle(title)
        self.setSubTitle(subtitle)
        self.reg_type = reg_type
        self._registers: list[dict] = []

        layout = QVBoxLayout(self)

        # Helpful tips
        if reg_type == "data":
            tip = QLabel(tr(
                "Data registers contain the sensor measurements.\n"
                "Check the manual for register addresses."
            ))
        else:
            tip = QLabel(tr(
                "Config registers control device settings.\n"
                "The most common are device address and baud rate."
            ))
        tip.setStyleSheet("color: #555; background-color: #FFF8E1; padding: 8px; border-radius: 4px;")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        # Quick-add buttons for common registers
        if reg_type == "config":
            quick_group = QGroupBox(tr("Quick Add Common Registers"))
            quick_layout = QHBoxLayout(quick_group)

            addr_btn = QPushButton("+ " + tr("Device Address"))
            addr_btn.setStyleSheet("QPushButton { background-color: #E3F2FD; padding: 6px 12px; border-radius: 3px; }")
            addr_btn.clicked.connect(self._quick_add_address)
            quick_layout.addWidget(addr_btn)

            baud_btn = QPushButton("+ " + tr("Baud Rate"))
            baud_btn.setStyleSheet("QPushButton { background-color: #E3F2FD; padding: 6px 12px; border-radius: 3px; }")
            baud_btn.clicked.connect(self._quick_add_baudrate)
            quick_layout.addWidget(baud_btn)

            quick_layout.addStretch()
            layout.addWidget(quick_group)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            tr("Name"), tr("Address"), tr("Type"), tr("Scale"), tr("Access")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton(tr("Add Register"))
        add_btn.setStyleSheet("QPushButton { background-color: #2E7D32; color: white; font-weight: bold; padding: 6px 16px; border-radius: 4px; }")
        add_btn.clicked.connect(self._add_register)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton(tr("Edit"))
        edit_btn.clicked.connect(self._edit_register)
        btn_layout.addWidget(edit_btn)

        dup_btn = QPushButton(tr("Duplicate"))
        dup_btn.clicked.connect(self._duplicate_register)
        btn_layout.addWidget(dup_btn)

        remove_btn = QPushButton(tr("Remove"))
        remove_btn.setStyleSheet("QPushButton { background-color: #C62828; color: white; padding: 6px 12px; border-radius: 4px; }")
        remove_btn.clicked.connect(self._remove_register)
        btn_layout.addWidget(remove_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _refresh_table(self):
        self.table.setRowCount(len(self._registers))
        for i, reg in enumerate(self._registers):
            self.table.setItem(i, 0, QTableWidgetItem(reg["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(f"0x{reg['address']:04X}"))
            self.table.setItem(i, 2, QTableWidgetItem(reg.get("data_type", "uint16")))
            scale = reg.get("scale", 1.0)
            self.table.setItem(i, 3, QTableWidgetItem(f"x{scale}" if scale != 1.0 else "1:1"))
            self.table.setItem(i, 4, QTableWidgetItem(reg.get("access", "read")))

    def _add_register(self):
        dlg = RegisterEditorDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            reg = dlg.get_result()
            if reg:
                self._registers.append(reg)
                self._refresh_table()

    def _edit_register(self):
        row = self.table.currentRow()
        if row < 0:
            return
        dlg = RegisterEditorDialog(register=self._registers[row], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            reg = dlg.get_result()
            if reg:
                self._registers[row] = reg
                self._refresh_table()

    def _duplicate_register(self):
        row = self.table.currentRow()
        if row < 0:
            return
        dup = dict(self._registers[row])
        dup["name"] = dup["name"] + " (copy)"
        dup["address"] = dup["address"] + 1
        self._registers.append(dup)
        self._refresh_table()

    def _remove_register(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self._registers[row]["name"]
        reply = QMessageBox.question(
            self, tr("Remove Register"),
            f"{tr('Remove')} '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._registers.pop(row)
            self._refresh_table()

    def _quick_add_address(self):
        reg = {
            "name": "Device Address",
            "address": 0x0100,
            "description": "Modbus slave address",
            "data_type": "uint16",
            "access": "readwrite",
            "function_code_read": 3,
            "function_code_write": 6,
            "min": 1,
            "max": 247,
        }
        dlg = RegisterEditorDialog(register=reg, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            result = dlg.get_result()
            if result:
                self._registers.append(result)
                self._refresh_table()

    def _quick_add_baudrate(self):
        reg = {
            "name": "Baud Rate",
            "address": 0x0101,
            "description": "Communication baud rate",
            "data_type": "uint16",
            "access": "readwrite",
            "function_code_read": 3,
            "function_code_write": 6,
            "value_map": {
                "1": 1200, "2": 2400, "3": 4800,
                "4": 9600, "5": 14400, "6": 19200,
            },
        }
        dlg = RegisterEditorDialog(register=reg, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            result = dlg.get_result()
            if result:
                self._registers.append(result)
                self._refresh_table()

    def get_registers(self) -> list[dict]:
        return self._registers


# ─── Step 4: Review & Save ────────────────────────────────────────────────────

class ReviewPage(QWizardPage):
    """Step 4: Review generated JSON and save."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(tr("Review & Save"))
        self.setSubTitle(tr(
            "Review the generated profile. "
            "Click 'Finish' to save."
        ))

        layout = QVBoxLayout(self)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFont(QFont("Monospace", 10))
        self.preview.setStyleSheet("QTextEdit { background-color: #1a1d23; color: #EEFFFF; border-radius: 4px; }")
        layout.addWidget(self.preview)

        # Save location
        loc_layout = QHBoxLayout()
        loc_layout.addWidget(QLabel(tr("Save as") + ":"))
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText(tr("auto-generated from device name"))
        loc_layout.addWidget(self.filename_edit)
        layout.addLayout(loc_layout)

    def set_json(self, data: dict, default_filename: str):
        self.preview.setPlainText(json.dumps(data, indent=4, ensure_ascii=False))
        self.filename_edit.setText(default_filename)

    def get_filename(self) -> str:
        return self.filename_edit.text().strip()

    def get_json_text(self) -> str:
        return self.preview.toPlainText()


# ─── Main Wizard ──────────────────────────────────────────────────────────────

class ProfileWizard(QWizard):
    """Step-by-step wizard for creating a new device profile."""

    def __init__(self, profiles_dir: str, parent=None):
        super().__init__(parent)
        self.profiles_dir = profiles_dir
        self.setWindowTitle(tr("New Device Profile Wizard"))
        self.setMinimumSize(700, 600)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        # Pages
        self.info_page = DeviceInfoPage()
        self.addPage(self.info_page)

        self.data_page = RegisterListPage(
            tr("Data Registers"),
            tr("Add the registers that contain sensor measurements."),
            "data"
        )
        self.addPage(self.data_page)

        self.config_page = RegisterListPage(
            tr("Configuration Registers"),
            tr("Add the registers used to configure the device."),
            "config"
        )
        self.addPage(self.config_page)

        self.review_page = ReviewPage()
        self.addPage(self.review_page)

        self.currentIdChanged.connect(self._on_page_changed)

    def _get_parity_char(self) -> str:
        text = self.info_page.default_parity.currentText()
        if "E" in text:
            return "E"
        elif "O" in text:
            return "O"
        return "N"

    def _build_profile_dict(self) -> dict:
        def reg_to_dict(reg: dict) -> dict:
            d = {
                "address": f"0x{reg['address']:04X}",
                "name": reg["name"],
                "description": reg.get("description", ""),
                "data_type": reg.get("data_type", "uint16"),
                "access": reg.get("access", "read"),
                "function_code_read": reg.get("function_code_read", 3),
                "function_code_write": reg.get("function_code_write", 6),
            }
            if reg.get("unit"):
                d["unit"] = reg["unit"]
            if reg.get("scale", 1.0) != 1.0:
                d["scale"] = reg["scale"]
            if reg.get("min") is not None:
                d["min"] = reg["min"]
            if reg.get("max") is not None:
                d["max"] = reg["max"]
            if reg.get("value_map"):
                d["value_map"] = reg["value_map"]
            return d

        return {
            "name": self.info_page.name_edit.text().strip(),
            "manufacturer": self.info_page.manufacturer_edit.text().strip(),
            "description": self.info_page.description_edit.text().strip(),
            "default_address": self.info_page.default_addr.value(),
            "default_baudrate": int(self.info_page.default_baud.currentText()),
            "default_parity": self._get_parity_char(),
            "default_databits": int(self.info_page.default_databits.currentText()),
            "default_stopbits": int(self.info_page.default_stopbits.currentText()),
            "data_registers": [reg_to_dict(r) for r in self.data_page.get_registers()],
            "config_registers": [reg_to_dict(r) for r in self.config_page.get_registers()],
        }

    def _on_page_changed(self, page_id):
        # When arriving at review page, generate the JSON
        if page_id == 3:
            data = self._build_profile_dict()
            name = data["name"]
            filename = name.lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "") + ".json"
            self.review_page.set_json(data, filename)

    def accept(self):
        filename = self.review_page.get_filename()
        if not filename:
            QMessageBox.warning(self, tr("Error"), tr("Enter a filename."))
            return
        if not filename.endswith(".json"):
            filename += ".json"

        filepath = os.path.join(self.profiles_dir, filename)

        if os.path.exists(filepath):
            reply = QMessageBox.question(
                self, tr("File Exists"),
                f"'{filename}' {tr('already exists. Overwrite?')}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            json_text = self.review_page.get_json_text()
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json_text)
            QMessageBox.information(
                self, tr("Profile Saved"),
                f"{tr('Profile saved to')}:\n{filepath}"
            )
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"{tr('Save failed')}:\n{e}")
