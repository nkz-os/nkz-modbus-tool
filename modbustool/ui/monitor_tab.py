"""Monitor tab — register reading, continuous polling, data log, raw frames."""

import csv
import time
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QSpinBox, QComboBox, QTableWidget, QTableWidgetItem, QSplitter,
    QHeaderView, QCheckBox, QTextEdit, QFileDialog, QTabWidget,
    QFormLayout, QDoubleSpinBox, QMessageBox, QFrame,
)
from PyQt6.QtGui import QFont, QColor, QTextCharFormat

from core.modbus_client import ModbusClient
from core.device_profiles import DeviceProfile, RegisterDef


class MonitorTab(QWidget):
    """Register monitoring and data logging tab."""

    def __init__(self, client: ModbusClient, connection_panel, parent=None):
        super().__init__(parent)
        self.client = client
        self.connection_panel = connection_panel
        self._current_profile: DeviceProfile | None = None
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_tick)
        self._data_log: list[dict] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # === Top: Read controls + Results ===
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Read controls
        controls_group = QGroupBox("Register Read")
        controls_layout = QVBoxLayout(controls_group)

        row1 = QHBoxLayout()

        form = QFormLayout()
        self.fc_combo = QComboBox()
        self.fc_combo.addItems([
            "FC03 - Holding Registers",
            "FC04 - Input Registers",
            "FC01 - Coils",
            "FC02 - Discrete Inputs",
        ])
        form.addRow("Function:", self.fc_combo)
        row1.addLayout(form)

        form2 = QFormLayout()
        self.reg_address = QSpinBox()
        self.reg_address.setRange(0, 65535)
        self.reg_address.setValue(0)
        self.reg_address.setPrefix("0x")
        self.reg_address.setDisplayIntegerBase(16)
        form2.addRow("Start Addr:", self.reg_address)
        row1.addLayout(form2)

        form3 = QFormLayout()
        self.reg_count = QSpinBox()
        self.reg_count.setRange(1, 125)
        self.reg_count.setValue(1)
        form3.addRow("Count:", self.reg_count)
        row1.addLayout(form3)

        form4 = QFormLayout()
        self.data_format = QComboBox()
        self.data_format.addItems(["Unsigned 16-bit", "Signed 16-bit", "Hex", "Binary",
                                    "Float32 (2 reg)", "Unsigned 32-bit (2 reg)", "Signed 32-bit (2 reg)"])
        form4.addRow("Format:", self.data_format)
        row1.addLayout(form4)

        controls_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.read_btn = QPushButton("Read Once")
        self.read_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 6px 16px; }")
        self.read_btn.clicked.connect(self._read_once)
        row2.addWidget(self.read_btn)

        row2.addWidget(QLabel("Poll interval:"))
        self.poll_interval = QDoubleSpinBox()
        self.poll_interval.setRange(0.1, 60.0)
        self.poll_interval.setValue(1.0)
        self.poll_interval.setSuffix(" s")
        self.poll_interval.setSingleStep(0.1)
        row2.addWidget(self.poll_interval)

        self.poll_btn = QPushButton("Start Polling")
        self.poll_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 6px 16px; }")
        self.poll_btn.setCheckable(True)
        self.poll_btn.clicked.connect(self._toggle_polling)
        row2.addWidget(self.poll_btn)

        row2.addStretch()

        self.read_profile_btn = QPushButton("Read Profile Registers")
        self.read_profile_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; padding: 6px 12px; }")
        self.read_profile_btn.clicked.connect(self._read_profile_registers)
        self.read_profile_btn.setEnabled(False)
        row2.addWidget(self.read_profile_btn)

        controls_layout.addLayout(row2)
        top_layout.addWidget(controls_group)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Register", "Name", "Raw (dec)", "Raw (hex)", "Formatted", "Unit", "Timestamp"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.results_table.setAlternatingRowColors(True)
        top_layout.addWidget(self.results_table)

        main_splitter.addWidget(top_widget)

        # === Bottom: Data Log + Raw Frames ===
        bottom_tabs = QTabWidget()

        # Data log tab
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(4, 4, 4, 4)

        log_btn_layout = QHBoxLayout()
        self.log_count_label = QLabel("Log entries: 0")
        log_btn_layout.addWidget(self.log_count_label)
        log_btn_layout.addStretch()

        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.clicked.connect(self._export_csv)
        log_btn_layout.addWidget(self.export_csv_btn)

        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self._clear_log)
        log_btn_layout.addWidget(self.clear_log_btn)

        log_layout.addLayout(log_btn_layout)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(["Time", "Register", "Name", "Raw", "Value"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.setAlternatingRowColors(True)
        log_layout.addWidget(self.log_table)

        bottom_tabs.addTab(log_widget, "Data Log")

        # Raw frames tab
        raw_widget = QWidget()
        raw_layout = QVBoxLayout(raw_widget)
        raw_layout.setContentsMargins(4, 4, 4, 4)

        raw_btn_layout = QHBoxLayout()
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        raw_btn_layout.addWidget(self.auto_scroll_check)
        raw_btn_layout.addStretch()
        self.clear_raw_btn = QPushButton("Clear")
        self.clear_raw_btn.clicked.connect(self._clear_raw)
        raw_btn_layout.addWidget(self.clear_raw_btn)
        raw_layout.addLayout(raw_btn_layout)

        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setFont(QFont("Monospace", 10))
        self.raw_text.setStyleSheet("QTextEdit { background-color: #1e1e1e; color: #d4d4d4; }")
        raw_layout.addWidget(self.raw_text)

        bottom_tabs.addTab(raw_widget, "Raw Frames (TX/RX)")

        main_splitter.addWidget(bottom_tabs)
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 1)

        layout.addWidget(main_splitter)

    def set_profile(self, profile: DeviceProfile | None):
        self._current_profile = profile
        self.read_profile_btn.setEnabled(profile is not None)

    def _get_slave(self) -> int:
        return self.connection_panel.slave_address

    def _format_value(self, raw: int, fmt_idx: int) -> str:
        if fmt_idx == 0:  # Unsigned 16
            return str(raw)
        elif fmt_idx == 1:  # Signed 16
            return str(raw - 65536 if raw > 32767 else raw)
        elif fmt_idx == 2:  # Hex
            return f"0x{raw:04X}"
        elif fmt_idx == 3:  # Binary
            return f"0b{raw:016b}"
        return str(raw)

    def _format_32bit(self, vals: list[int], start: int, fmt_idx: int) -> list[tuple[str, int]]:
        """Format pairs of registers as 32-bit values."""
        results = []
        i = 0
        while i < len(vals) - 1:
            high, low = vals[i], vals[i + 1]
            combined = (high << 16) | low
            if fmt_idx == 4:  # Float32
                import struct
                packed = struct.pack(">I", combined)
                fval = struct.unpack(">f", packed)[0]
                results.append((f"{fval:.4f}", 2))
            elif fmt_idx == 5:  # Unsigned 32
                results.append((str(combined), 2))
            elif fmt_idx == 6:  # Signed 32
                if combined > 2147483647:
                    combined -= 4294967296
                results.append((str(combined), 2))
            i += 2
        if i < len(vals):
            results.append((str(vals[i]), 1))
        return results

    def _read_once(self):
        if not self.client.connected:
            return

        fc_idx = self.fc_combo.currentIndex()
        addr = self.reg_address.value()
        count = self.reg_count.value()
        slave = self._get_slave()

        if fc_idx == 0:
            ok, result = self.client.read_holding_registers(addr, count, slave)
        elif fc_idx == 1:
            ok, result = self.client.read_input_registers(addr, count, slave)
        elif fc_idx == 2:
            ok, result = self.client.read_coils(addr, count, slave)
        elif fc_idx == 3:
            ok, result = self.client.read_discrete_inputs(addr, count, slave)
        else:
            return

        self._update_raw_display()

        if not ok:
            self._show_error_in_table(str(result))
            return

        self._display_results(addr, result)

    def _display_results(self, start_addr: int, values: list):
        fmt_idx = self.data_format.currentIndex()
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        is_32bit = fmt_idx >= 4

        if is_32bit and isinstance(values[0], int):
            formatted_pairs = self._format_32bit(values, start_addr, fmt_idx)
            self.results_table.setRowCount(len(formatted_pairs))
            reg_offset = 0
            for row, (fmt_val, span) in enumerate(formatted_pairs):
                reg_addr = start_addr + reg_offset
                raw_combined = (values[reg_offset] << 16 | values[reg_offset + 1]) if span == 2 and reg_offset + 1 < len(values) else values[reg_offset]
                self._set_result_row(row, reg_addr, raw_combined, fmt_val, now, span)
                reg_offset += span
        else:
            self.results_table.setRowCount(len(values))
            for i, val in enumerate(values):
                reg_addr = start_addr + i
                if isinstance(val, bool):
                    fmt_val = "ON" if val else "OFF"
                    raw = 1 if val else 0
                else:
                    raw = val
                    fmt_val = self._format_value(val, fmt_idx)
                self._set_result_row(i, reg_addr, raw, fmt_val, now)

    def _set_result_row(self, row: int, reg_addr: int, raw: int, fmt_val: str,
                        timestamp: str, span: int = 1):
        # Check profile for register name/unit
        name = ""
        unit = ""
        profile_fmt = None
        if self._current_profile:
            reg_def = self._current_profile.get_register_by_address(reg_addr)
            if reg_def:
                name = reg_def.name
                unit = reg_def.unit
                profile_fmt = reg_def.display_value(raw)

        display_val = profile_fmt if profile_fmt else fmt_val

        addr_text = f"0x{reg_addr:04X}" + (f" (+{span})" if span > 1 else "")
        self.results_table.setItem(row, 0, QTableWidgetItem(addr_text))
        self.results_table.setItem(row, 1, QTableWidgetItem(name))
        self.results_table.setItem(row, 2, QTableWidgetItem(str(raw)))
        self.results_table.setItem(row, 3, QTableWidgetItem(f"0x{raw:04X}" if raw < 65536 else f"0x{raw:08X}"))
        self.results_table.setItem(row, 4, QTableWidgetItem(display_val))
        self.results_table.setItem(row, 5, QTableWidgetItem(unit))
        self.results_table.setItem(row, 6, QTableWidgetItem(timestamp))

        # Add to data log
        log_entry = {
            "time": timestamp,
            "register": f"0x{reg_addr:04X}",
            "name": name,
            "raw": raw,
            "value": display_val,
            "unit": unit,
        }
        self._data_log.append(log_entry)
        log_row = self.log_table.rowCount()
        self.log_table.insertRow(log_row)
        self.log_table.setItem(log_row, 0, QTableWidgetItem(timestamp))
        self.log_table.setItem(log_row, 1, QTableWidgetItem(f"0x{reg_addr:04X}"))
        self.log_table.setItem(log_row, 2, QTableWidgetItem(name))
        self.log_table.setItem(log_row, 3, QTableWidgetItem(str(raw)))
        self.log_table.setItem(log_row, 4, QTableWidgetItem(display_val))
        self.log_count_label.setText(f"Log entries: {len(self._data_log)}")

    def _show_error_in_table(self, error: str):
        self.results_table.setRowCount(1)
        item = QTableWidgetItem(f"ERROR: {error}")
        item.setForeground(QColor(255, 0, 0))
        self.results_table.setItem(0, 0, item)
        for col in range(1, 7):
            self.results_table.setItem(0, col, QTableWidgetItem(""))

    def _toggle_polling(self, checked):
        if checked:
            if not self.client.connected:
                self.poll_btn.setChecked(False)
                return
            interval_ms = int(self.poll_interval.value() * 1000)
            self._poll_timer.start(interval_ms)
            self.poll_btn.setText("Stop Polling")
            self.poll_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 6px 16px; }")
        else:
            self._poll_timer.stop()
            self.poll_btn.setText("Start Polling")
            self.poll_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 6px 16px; }")

    def _poll_tick(self):
        if not self.client.connected:
            self._toggle_polling(False)
            self.poll_btn.setChecked(False)
            return
        self._read_once()

    def _read_profile_registers(self):
        if not self._current_profile or not self.client.connected:
            return

        all_regs = self._current_profile.all_registers
        if not all_regs:
            return

        results = []
        slave = self._get_slave()
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        for reg in all_regs:
            fc = reg.function_code_read
            if fc == 3:
                ok, vals = self.client.read_holding_registers(reg.address, 1, slave)
            elif fc == 4:
                ok, vals = self.client.read_input_registers(reg.address, 1, slave)
            else:
                ok, vals = self.client.read_holding_registers(reg.address, 1, slave)

            if ok and vals:
                results.append((reg, vals[0]))
            else:
                results.append((reg, None))

        self._update_raw_display()

        # Display in table
        self.results_table.setRowCount(len(results))
        for row, (reg, val) in enumerate(results):
            addr_text = f"0x{reg.address:04X}"
            self.results_table.setItem(row, 0, QTableWidgetItem(addr_text))
            self.results_table.setItem(row, 1, QTableWidgetItem(reg.name))
            if val is not None:
                self.results_table.setItem(row, 2, QTableWidgetItem(str(val)))
                self.results_table.setItem(row, 3, QTableWidgetItem(f"0x{val:04X}"))
                display = reg.display_value(val)
                self.results_table.setItem(row, 4, QTableWidgetItem(display))
                self.results_table.setItem(row, 5, QTableWidgetItem(reg.unit))

                log_entry = {
                    "time": now, "register": addr_text, "name": reg.name,
                    "raw": val, "value": display, "unit": reg.unit,
                }
                self._data_log.append(log_entry)
            else:
                err_item = QTableWidgetItem("READ ERROR")
                err_item.setForeground(QColor(255, 0, 0))
                self.results_table.setItem(row, 4, err_item)
            self.results_table.setItem(row, 6, QTableWidgetItem(now))

        self.log_count_label.setText(f"Log entries: {len(self._data_log)}")

    def _update_raw_display(self):
        """Update the raw frames text from the client's frame log."""
        # Get last entries not yet displayed
        log = self.client.frame_log
        if not log:
            return
        # Show last 20 entries
        recent = log[-20:]
        lines = []
        for entry in recent:
            ts = datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S.%f")[:-3]
            color = "#569CD6" if entry.direction == "TX" else "#4EC9B0" if entry.direction == "RX" else "#DCDCAA"
            lines.append(
                f'<span style="color:{color}">[{ts}] {entry.direction}</span> '
                f'<span style="color:#CE9178">{entry.raw_hex}</span> '
                f'<span style="color:#6A9955">// {entry.description}</span>'
            )
        self.raw_text.setHtml("<br>".join(lines))
        if self.auto_scroll_check.isChecked():
            scrollbar = self.raw_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def _export_csv(self):
        if not self._data_log:
            QMessageBox.information(self, "Export", "No data to export")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["time", "register", "name", "raw", "value", "unit"])
            writer.writeheader()
            writer.writerows(self._data_log)
        QMessageBox.information(self, "Export", f"Exported {len(self._data_log)} entries to {path}")

    def _clear_log(self):
        self._data_log.clear()
        self.log_table.setRowCount(0)
        self.log_count_label.setText("Log entries: 0")

    def _clear_raw(self):
        self.raw_text.clear()
        self.client.clear_log()
