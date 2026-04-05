"""Scanner tab — bus scan and baud rate auto-detection."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QSpinBox, QProgressBar, QTableWidget, QTableWidgetItem, QCheckBox,
    QFormLayout, QComboBox, QTextEdit, QSplitter, QHeaderView, QMessageBox,
)

from core.modbus_client import ModbusClient
from core.scanner import BusScanWorker, BaudDetectWorker, COMMON_BAUDRATES


class ScannerTab(QWidget):
    """Bus scanning and device discovery tab."""

    def __init__(self, client: ModbusClient, connection_panel, parent=None):
        super().__init__(parent)
        self.client = client
        self.connection_panel = connection_panel
        self._scan_worker = None
        self._baud_worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # --- Top: Scan Controls ---
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Bus Scan section
        scan_group = QGroupBox("Bus Scan — Find Devices")
        scan_layout = QVBoxLayout(scan_group)

        params_layout = QHBoxLayout()

        form1 = QFormLayout()
        self.addr_start = QSpinBox()
        self.addr_start.setRange(1, 247)
        self.addr_start.setValue(1)
        form1.addRow("From addr:", self.addr_start)

        self.addr_end = QSpinBox()
        self.addr_end.setRange(1, 247)
        self.addr_end.setValue(50)
        form1.addRow("To addr:", self.addr_end)
        params_layout.addLayout(form1)

        form2 = QFormLayout()
        self.scan_timeout = QSpinBox()
        self.scan_timeout.setRange(100, 5000)
        self.scan_timeout.setValue(300)
        self.scan_timeout.setSuffix(" ms")
        form2.addRow("Timeout:", self.scan_timeout)
        params_layout.addLayout(form2)

        scan_layout.addLayout(params_layout)

        # Baud rates to scan
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Baud rates:"))
        self.baud_checks = {}
        for baud in COMMON_BAUDRATES:
            cb = QCheckBox(str(baud))
            if baud in (4800, 9600):
                cb.setChecked(True)
            self.baud_checks[baud] = cb
            baud_layout.addWidget(cb)
        baud_layout.addStretch()
        scan_layout.addLayout(baud_layout)

        # Parity options
        parity_layout = QHBoxLayout()
        parity_layout.addWidget(QLabel("Parity:"))
        self.parity_n = QCheckBox("None")
        self.parity_n.setChecked(True)
        self.parity_e = QCheckBox("Even")
        self.parity_o = QCheckBox("Odd")
        parity_layout.addWidget(self.parity_n)
        parity_layout.addWidget(self.parity_e)
        parity_layout.addWidget(self.parity_o)
        parity_layout.addStretch()
        scan_layout.addLayout(parity_layout)

        # Progress
        self.scan_progress = QProgressBar()
        self.scan_progress.setTextVisible(True)
        self.scan_progress.setFormat("%v / %m — %p%")
        scan_layout.addWidget(self.scan_progress)

        self.scan_status = QLabel("Ready to scan")
        self.scan_status.setStyleSheet("color: #666;")
        scan_layout.addWidget(self.scan_status)

        # Buttons
        btn_layout = QHBoxLayout()
        self.scan_btn = QPushButton("Start Scan")
        self.scan_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 6px 16px; }")
        self.scan_btn.clicked.connect(self._start_scan)
        self.stop_scan_btn = QPushButton("Stop")
        self.stop_scan_btn.setEnabled(False)
        self.stop_scan_btn.clicked.connect(self._stop_scan)
        self.clear_btn = QPushButton("Clear Results")
        self.clear_btn.clicked.connect(self._clear_results)
        btn_layout.addWidget(self.scan_btn)
        btn_layout.addWidget(self.stop_scan_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.clear_btn)
        scan_layout.addLayout(btn_layout)

        top_layout.addWidget(scan_group)

        # Baud Rate Detection
        detect_group = QGroupBox("Auto-Detect Baud Rate")
        detect_layout = QHBoxLayout(detect_group)

        detect_form = QFormLayout()
        self.detect_addr = QSpinBox()
        self.detect_addr.setRange(1, 247)
        self.detect_addr.setValue(1)
        detect_form.addRow("Slave address:", self.detect_addr)
        detect_layout.addLayout(detect_form)

        self.detect_btn = QPushButton("Auto-Detect")
        self.detect_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 6px 16px; }")
        self.detect_btn.clicked.connect(self._start_baud_detect)
        detect_layout.addWidget(self.detect_btn)

        self.detect_status = QLabel("")
        self.detect_status.setWordWrap(True)
        detect_layout.addWidget(self.detect_status, 1)

        top_layout.addWidget(detect_group)
        splitter.addWidget(top_widget)

        # --- Bottom: Results Table ---
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 0, 0, 0)

        results_layout.addWidget(QLabel("Discovered Devices:"))

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Address", "Baud Rate", "Parity", "Type", "Register 0 Value"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        results_layout.addWidget(self.results_table)

        splitter.addWidget(results_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    def _get_selected_baudrates(self) -> list[int]:
        return [b for b, cb in self.baud_checks.items() if cb.isChecked()]

    def _get_selected_parities(self) -> list[str]:
        parities = []
        if self.parity_n.isChecked():
            parities.append("N")
        if self.parity_e.isChecked():
            parities.append("E")
        if self.parity_o.isChecked():
            parities.append("O")
        return parities or ["N"]

    def _cleanup_scan_worker(self):
        """Safely clean up scan worker after thread finishes."""
        if self._scan_worker:
            self._scan_worker.wait()
            self._scan_worker.deleteLater()
            self._scan_worker = None

    def _cleanup_baud_worker(self):
        """Safely clean up baud detect worker after thread finishes."""
        if self._baud_worker:
            self._baud_worker.wait()
            self._baud_worker.deleteLater()
            self._baud_worker = None

    def _start_scan(self):
        bauds = self._get_selected_baudrates()
        if not bauds:
            self.scan_status.setText("Select at least one baud rate!")
            return

        conn_tab = self.connection_panel.conn_tabs.currentIndex()

        if conn_tab == 0:
            # Serial mode — need a valid port
            port = self.connection_panel.get_serial_port()
            if not port:
                QMessageBox.warning(self, "No Port", "Select a serial port before scanning.")
                return
        else:
            port = ""

        # Disconnect main client during scan (serial port exclusive access)
        if self.client.connected:
            self.client.disconnect()
            self.connection_panel._disconnect()

        self.scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(True)
        self.scan_status.setText("Scanning...")

        self._scan_worker = BusScanWorker(
            connection_type="tcp" if conn_tab == 1 else "serial",
            serial_port=port,
            baudrates=bauds,
            parities=self._get_selected_parities(),
            tcp_host=self.connection_panel.tcp_host.text(),
            tcp_port=self.connection_panel.tcp_port.value(),
            addr_start=self.addr_start.value(),
            addr_end=self.addr_end.value(),
            timeout=self.scan_timeout.value() / 1000.0,
        )
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.device_found.connect(self._on_device_found)
        self._scan_worker.scan_complete.connect(self._on_scan_complete)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.finished.connect(self._cleanup_scan_worker)
        self._scan_worker.start()

    def _stop_scan(self):
        if self._scan_worker:
            self._scan_worker.abort()
            self.scan_status.setText("Stopping...")

    def _on_scan_progress(self, current, total, text):
        self.scan_progress.setMaximum(total)
        self.scan_progress.setValue(current)
        self.scan_status.setText(text)

    def _on_device_found(self, address, baudrate, parity):
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(str(address)))
        self.results_table.setItem(row, 1, QTableWidgetItem(str(baudrate) if baudrate else "N/A"))
        self.results_table.setItem(row, 2, QTableWidgetItem(parity))
        self.results_table.setItem(row, 3, QTableWidgetItem("RTU" if baudrate else "TCP"))
        self.results_table.setItem(row, 4, QTableWidgetItem("—"))

    def _on_scan_complete(self, devices):
        count = len(devices)
        self.scan_status.setText(f"Scan complete. Found {count} device(s).")
        self.scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)

    def _on_scan_error(self, error):
        self.scan_status.setText(f"Error: {error}")
        self.scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)

    def _clear_results(self):
        self.results_table.setRowCount(0)
        self.scan_progress.setValue(0)
        self.scan_status.setText("Ready to scan")

    def _start_baud_detect(self):
        port = self.connection_panel.get_serial_port()
        if not port:
            self.detect_status.setText("No serial port selected!")
            self.detect_status.setStyleSheet("color: #f44336;")
            return

        if self.client.connected:
            self.client.disconnect()
            self.connection_panel._disconnect()

        self.detect_btn.setEnabled(False)
        self.detect_status.setText("Detecting...")
        self.detect_status.setStyleSheet("color: #FF9800;")

        self._baud_worker = BaudDetectWorker(
            serial_port=port,
            slave_address=self.detect_addr.value(),
            timeout=0.5,
        )
        self._baud_worker.progress.connect(lambda msg: self.detect_status.setText(msg))
        self._baud_worker.result.connect(self._on_baud_detected)
        self._baud_worker.finished.connect(self._on_baud_finished)
        self._baud_worker.start()

    def _on_baud_detected(self, result):
        if result["success"]:
            self.detect_status.setText(
                f"Found: {result['baudrate']} baud, parity={result['parity']}, "
                f"reg[0]={result['values']}"
            )
            self.detect_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
            # Auto-fill connection panel
            self.connection_panel.baud_combo.setCurrentText(str(result["baudrate"]))
            parity_map = {"N": 0, "E": 1, "O": 2}
            self.connection_panel.parity_combo.setCurrentIndex(parity_map.get(result["parity"], 0))
        else:
            self.detect_status.setText(result["message"])
            self.detect_status.setStyleSheet("color: #f44336;")

    def _on_baud_finished(self):
        """Called when the baud detect QThread actually finishes."""
        self.detect_btn.setEnabled(True)
        self._cleanup_baud_worker()
