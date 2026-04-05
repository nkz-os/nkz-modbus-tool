"""Modbus bus scanner — threaded address discovery and baud rate auto-detection."""

from PyQt6.QtCore import QThread, pyqtSignal
from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.framer import FramerType


COMMON_BAUDRATES = [1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200]
COMMON_PARITIES = ["N", "E", "O"]


class BusScanWorker(QThread):
    """Scan a range of Modbus addresses to find responding devices."""

    device_found = pyqtSignal(int, int, str)  # address, baudrate, parity
    progress = pyqtSignal(int, int, str)       # current, total, status_text
    scan_complete = pyqtSignal(list)            # list of found devices
    error = pyqtSignal(str)

    def __init__(self, connection_type: str, serial_port: str = "",
                 baudrates: list[int] = None, parities: list[str] = None,
                 tcp_host: str = "", tcp_port: int = 502,
                 addr_start: int = 1, addr_end: int = 247,
                 timeout: float = 0.3, stopbits: int = 1, databits: int = 8):
        super().__init__()
        self.connection_type = connection_type
        self.serial_port = serial_port
        self.baudrates = baudrates or [9600]
        self.parities = parities or ["N"]
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.addr_start = addr_start
        self.addr_end = addr_end
        self.timeout = timeout
        self.stopbits = stopbits
        self.databits = databits
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        found_devices = []
        addr_range = range(self.addr_start, self.addr_end + 1)

        try:
            if self.connection_type == "tcp":
                found_devices = self._scan_tcp(addr_range)
            else:
                found_devices = self._scan_serial(addr_range)
        except Exception as e:
            self.error.emit(f"Scan failed: {e}")
            return

        self.scan_complete.emit(found_devices)

    def _scan_tcp(self, addr_range):
        found_devices = []
        total = len(addr_range)
        client = None
        try:
            client = ModbusTcpClient(
                host=self.tcp_host, port=self.tcp_port,
                timeout=self.timeout, framer=FramerType.SOCKET,
            )
            if not client.connect():
                self.error.emit(f"Cannot connect to {self.tcp_host}:{self.tcp_port}")
                return found_devices

            for i, addr in enumerate(addr_range):
                if self._abort:
                    break
                self.progress.emit(i + 1, total, f"TCP scanning address {addr}...")
                try:
                    result = client.read_holding_registers(address=0, count=1, slave=addr)
                    if not result.isError():
                        device_info = {"address": addr, "baudrate": 0, "parity": "N/A", "type": "TCP"}
                        found_devices.append(device_info)
                        self.device_found.emit(addr, 0, "TCP")
                except Exception:
                    pass
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass
        return found_devices

    def _scan_serial(self, addr_range):
        found_devices = []

        if not self.serial_port:
            self.error.emit("No serial port specified")
            return found_devices

        combos = [(b, p) for b in self.baudrates for p in self.parities]
        total = len(combos) * len(addr_range)
        step = 0

        for baudrate, parity in combos:
            if self._abort:
                break
            client = None
            try:
                client = ModbusSerialClient(
                    port=self.serial_port,
                    baudrate=baudrate,
                    parity=parity,
                    stopbits=self.stopbits,
                    bytesize=self.databits,
                    timeout=self.timeout,
                    framer=FramerType.RTU,
                )
                if not client.connect():
                    self.progress.emit(step + len(addr_range), total,
                                       f"Cannot open port at {baudrate} baud, parity={parity}")
                    step += len(addr_range)
                    continue

                for addr in addr_range:
                    if self._abort:
                        break
                    step += 1
                    self.progress.emit(step, total,
                                       f"Scanning addr {addr} @ {baudrate} baud, parity={parity}")
                    try:
                        result = client.read_holding_registers(address=0, count=1, slave=addr)
                        if not result.isError():
                            already = any(d["address"] == addr for d in found_devices)
                            if not already:
                                device_info = {
                                    "address": addr,
                                    "baudrate": baudrate,
                                    "parity": parity,
                                    "type": "RTU",
                                }
                                found_devices.append(device_info)
                                self.device_found.emit(addr, baudrate, parity)
                    except Exception:
                        pass
            except Exception as e:
                self.progress.emit(step + len(addr_range), total,
                                   f"Error at {baudrate}/{parity}: {e}")
                step += len(addr_range)
            finally:
                if client:
                    try:
                        client.close()
                    except Exception:
                        pass

        return found_devices


class BaudDetectWorker(QThread):
    """Auto-detect baud rate and parity for a specific slave address."""

    result = pyqtSignal(dict)        # {baudrate, parity, success, values}
    progress = pyqtSignal(str)       # status message
    finished_signal = pyqtSignal()

    def __init__(self, serial_port: str, slave_address: int = 1,
                 baudrates: list[int] = None, parities: list[str] = None,
                 timeout: float = 0.5, stopbits: int = 1, databits: int = 8):
        super().__init__()
        self.serial_port = serial_port
        self.slave_address = slave_address
        self.baudrates = baudrates or COMMON_BAUDRATES
        self.parities = parities or ["N", "E", "O"]
        self.timeout = timeout
        self.stopbits = stopbits
        self.databits = databits
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        if not self.serial_port:
            self.result.emit({"success": False, "message": "No serial port specified"})
            self.finished_signal.emit()
            return

        for baudrate in self.baudrates:
            for parity in self.parities:
                if self._abort:
                    self.result.emit({"success": False, "message": "Aborted"})
                    self.finished_signal.emit()
                    return

                self.progress.emit(f"Trying {baudrate} baud, parity={parity}...")
                client = None
                try:
                    client = ModbusSerialClient(
                        port=self.serial_port,
                        baudrate=baudrate,
                        parity=parity,
                        stopbits=self.stopbits,
                        bytesize=self.databits,
                        timeout=self.timeout,
                        framer=FramerType.RTU,
                    )
                    if not client.connect():
                        continue

                    result = client.read_holding_registers(
                        address=0, count=1, slave=self.slave_address
                    )
                    if not result.isError():
                        values = list(result.registers)
                        client.close()
                        client = None
                        self.result.emit({
                            "success": True,
                            "baudrate": baudrate,
                            "parity": parity,
                            "values": values,
                            "message": f"Found! {baudrate} baud, parity={parity}",
                        })
                        self.finished_signal.emit()
                        return
                except Exception:
                    pass
                finally:
                    if client:
                        try:
                            client.close()
                        except Exception:
                            pass

        self.result.emit({"success": False, "message": "No device responded at any baud rate/parity combination"})
        self.finished_signal.emit()
