"""Unified Modbus client supporting RTU (serial) and TCP connections."""

import struct
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import serial.tools.list_ports
from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.framer import FramerType


class ConnectionType(Enum):
    SERIAL_RTU = "serial_rtu"
    TCP = "tcp"


class Parity(Enum):
    NONE = "N"
    EVEN = "E"
    ODD = "O"


@dataclass
class SerialConfig:
    port: str = ""
    baudrate: int = 9600
    parity: str = "N"
    stopbits: int = 1
    databits: int = 8
    timeout: float = 1.0


@dataclass
class TcpConfig:
    host: str = "192.168.1.1"
    port: int = 502
    timeout: float = 3.0


@dataclass
class FrameLog:
    timestamp: float
    direction: str  # "TX" or "RX"
    raw_hex: str
    description: str = ""


class ModbusClient:
    """Unified Modbus client wrapper around pymodbus."""

    def __init__(self):
        self._client = None
        self._connection_type: Optional[ConnectionType] = None
        self._serial_config: Optional[SerialConfig] = None
        self._tcp_config: Optional[TcpConfig] = None
        self._connected = False
        self._frame_log: list[FrameLog] = []
        self._max_log_size = 5000

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def connection_type(self) -> Optional[ConnectionType]:
        return self._connection_type

    @property
    def frame_log(self) -> list[FrameLog]:
        return self._frame_log

    def clear_log(self):
        self._frame_log.clear()

    def _log_frame(self, direction: str, data: bytes | str, description: str = ""):
        if isinstance(data, bytes):
            hex_str = " ".join(f"{b:02X}" for b in data)
        else:
            hex_str = data
        entry = FrameLog(
            timestamp=time.time(),
            direction=direction,
            raw_hex=hex_str,
            description=description,
        )
        self._frame_log.append(entry)
        if len(self._frame_log) > self._max_log_size:
            self._frame_log = self._frame_log[-self._max_log_size:]

    @staticmethod
    def detect_serial_ports(include_all: bool = False) -> list[dict]:
        """Detect available serial ports with metadata.

        By default filters out built-in ttyS* ports that have no real hardware
        (vid/pid is None, no manufacturer, hwid is just 'PNP*' or similar).
        Set include_all=True to list everything.
        """
        ports = []
        for port in serial.tools.list_ports.comports():
            # Filter phantom ttyS ports: no USB vid/pid and generic hwid
            if not include_all:
                is_usb = port.vid is not None
                is_real_serial = (port.manufacturer or port.product or
                                  port.serial_number)
                if not is_usb and not is_real_serial:
                    continue
            ports.append({
                "device": port.device,
                "description": port.description,
                "hwid": port.hwid,
                "manufacturer": port.manufacturer or "",
                "product": port.product or "",
                "serial_number": port.serial_number or "",
                "vid": port.vid,
                "pid": port.pid,
                "display": f"{port.device} - {port.description}",
            })
        ports.sort(key=lambda p: p["device"])
        return ports

    def connect_serial(self, config: SerialConfig) -> tuple[bool, str]:
        """Connect via Modbus RTU over serial."""
        self.disconnect()
        self._serial_config = config
        self._connection_type = ConnectionType.SERIAL_RTU
        try:
            self._client = ModbusSerialClient(
                port=config.port,
                baudrate=config.baudrate,
                parity=config.parity,
                stopbits=config.stopbits,
                bytesize=config.databits,
                timeout=config.timeout,
                framer=FramerType.RTU,
            )
            result = self._client.connect()
            if result:
                self._connected = True
                self._log_frame("SYS", "CONNECTED",
                                f"Serial {config.port} @ {config.baudrate} {config.databits}{config.parity}{config.stopbits}")
                return True, f"Connected to {config.port}"
            else:
                return False, f"Failed to open {config.port}"
        except Exception as e:
            self._client = None
            return False, f"Connection error: {e}"

    def connect_tcp(self, config: TcpConfig) -> tuple[bool, str]:
        """Connect via Modbus TCP."""
        self.disconnect()
        self._tcp_config = config
        self._connection_type = ConnectionType.TCP
        try:
            self._client = ModbusTcpClient(
                host=config.host,
                port=config.port,
                timeout=config.timeout,
                framer=FramerType.SOCKET,
            )
            result = self._client.connect()
            if result:
                self._connected = True
                self._log_frame("SYS", "CONNECTED",
                                f"TCP {config.host}:{config.port}")
                return True, f"Connected to {config.host}:{config.port}"
            else:
                return False, f"Failed to connect to {config.host}:{config.port}"
        except Exception as e:
            self._client = None
            return False, f"Connection error: {e}"

    def disconnect(self):
        """Disconnect current client."""
        if self._client:
            try:
                self._client.close()
                self._log_frame("SYS", "DISCONNECTED", "")
            except Exception:
                pass
            self._client = None
        self._connected = False

    def _build_request_hex(self, slave: int, fc: int, address: int, count_or_value: int) -> str:
        """Build a human-readable hex representation of the request frame."""
        frame = struct.pack(">BBHH", slave, fc, address, count_or_value)
        return " ".join(f"{b:02X}" for b in frame)

    def read_holding_registers(self, address: int, count: int = 1, slave: int = 1) -> tuple[bool, list[int] | str]:
        """Read holding registers (FC 0x03)."""
        if not self._connected or not self._client:
            return False, "Not connected"
        req_hex = self._build_request_hex(slave, 0x03, address, count)
        self._log_frame("TX", req_hex, f"FC03 Read Holding addr={address} count={count} slave={slave}")
        try:
            result = self._client.read_holding_registers(address=address, count=count, slave=slave)
            if result.isError():
                err = str(result)
                self._log_frame("RX", "ERROR", err)
                return False, err
            values = list(result.registers)
            resp_bytes = struct.pack(">BB B" + "H" * len(values), slave, 0x03, len(values) * 2, *values)
            self._log_frame("RX", resp_bytes, f"FC03 Response: {values}")
            return True, values
        except ModbusException as e:
            self._log_frame("RX", "ERROR", str(e))
            return False, str(e)
        except Exception as e:
            self._log_frame("RX", "ERROR", str(e))
            return False, str(e)

    def read_input_registers(self, address: int, count: int = 1, slave: int = 1) -> tuple[bool, list[int] | str]:
        """Read input registers (FC 0x04)."""
        if not self._connected or not self._client:
            return False, "Not connected"
        req_hex = self._build_request_hex(slave, 0x04, address, count)
        self._log_frame("TX", req_hex, f"FC04 Read Input addr={address} count={count} slave={slave}")
        try:
            result = self._client.read_input_registers(address=address, count=count, slave=slave)
            if result.isError():
                err = str(result)
                self._log_frame("RX", "ERROR", err)
                return False, err
            values = list(result.registers)
            resp_bytes = struct.pack(">BB B" + "H" * len(values), slave, 0x04, len(values) * 2, *values)
            self._log_frame("RX", resp_bytes, f"FC04 Response: {values}")
            return True, values
        except ModbusException as e:
            self._log_frame("RX", "ERROR", str(e))
            return False, str(e)
        except Exception as e:
            self._log_frame("RX", "ERROR", str(e))
            return False, str(e)

    def write_single_register(self, address: int, value: int, slave: int = 1) -> tuple[bool, str]:
        """Write single register (FC 0x06)."""
        if not self._connected or not self._client:
            return False, "Not connected"
        req_hex = self._build_request_hex(slave, 0x06, address, value)
        self._log_frame("TX", req_hex, f"FC06 Write Single addr={address} value={value} slave={slave}")
        try:
            result = self._client.write_register(address=address, value=value, slave=slave)
            if result.isError():
                err = str(result)
                self._log_frame("RX", "ERROR", err)
                return False, err
            resp_bytes = struct.pack(">BBHH", slave, 0x06, address, value)
            self._log_frame("RX", resp_bytes, f"FC06 OK: addr={address} value={value}")
            return True, f"Written {value} to register {address}"
        except ModbusException as e:
            self._log_frame("RX", "ERROR", str(e))
            return False, str(e)
        except Exception as e:
            self._log_frame("RX", "ERROR", str(e))
            return False, str(e)

    def write_multiple_registers(self, address: int, values: list[int], slave: int = 1) -> tuple[bool, str]:
        """Write multiple registers (FC 0x10)."""
        if not self._connected or not self._client:
            return False, "Not connected"
        frame_data = struct.pack(">BBHH", slave, 0x10, address, len(values))
        self._log_frame("TX", frame_data, f"FC16 Write Multiple addr={address} values={values} slave={slave}")
        try:
            result = self._client.write_registers(address=address, values=values, slave=slave)
            if result.isError():
                err = str(result)
                self._log_frame("RX", "ERROR", err)
                return False, err
            self._log_frame("RX", frame_data, f"FC16 OK: addr={address} count={len(values)}")
            return True, f"Written {len(values)} registers starting at {address}"
        except ModbusException as e:
            self._log_frame("RX", "ERROR", str(e))
            return False, str(e)
        except Exception as e:
            self._log_frame("RX", "ERROR", str(e))
            return False, str(e)

    def read_coils(self, address: int, count: int = 1, slave: int = 1) -> tuple[bool, list[bool] | str]:
        """Read coils (FC 0x01)."""
        if not self._connected or not self._client:
            return False, "Not connected"
        self._log_frame("TX", self._build_request_hex(slave, 0x01, address, count),
                        f"FC01 Read Coils addr={address} count={count} slave={slave}")
        try:
            result = self._client.read_coils(address=address, count=count, slave=slave)
            if result.isError():
                err = str(result)
                self._log_frame("RX", "ERROR", err)
                return False, err
            bits = list(result.bits[:count])
            self._log_frame("RX", str(bits), f"FC01 Response: {bits}")
            return True, bits
        except Exception as e:
            self._log_frame("RX", "ERROR", str(e))
            return False, str(e)

    def read_discrete_inputs(self, address: int, count: int = 1, slave: int = 1) -> tuple[bool, list[bool] | str]:
        """Read discrete inputs (FC 0x02)."""
        if not self._connected or not self._client:
            return False, "Not connected"
        self._log_frame("TX", self._build_request_hex(slave, 0x02, address, count),
                        f"FC02 Read Discrete addr={address} count={count} slave={slave}")
        try:
            result = self._client.read_discrete_inputs(address=address, count=count, slave=slave)
            if result.isError():
                err = str(result)
                self._log_frame("RX", "ERROR", err)
                return False, err
            bits = list(result.bits[:count])
            self._log_frame("RX", str(bits), f"FC02 Response: {bits}")
            return True, bits
        except Exception as e:
            self._log_frame("RX", "ERROR", str(e))
            return False, str(e)

    def write_single_coil(self, address: int, value: bool, slave: int = 1) -> tuple[bool, str]:
        """Write single coil (FC 0x05)."""
        if not self._connected or not self._client:
            return False, "Not connected"
        self._log_frame("TX", self._build_request_hex(slave, 0x05, address, 0xFF00 if value else 0x0000),
                        f"FC05 Write Coil addr={address} value={value} slave={slave}")
        try:
            result = self._client.write_coil(address=address, value=value, slave=slave)
            if result.isError():
                err = str(result)
                self._log_frame("RX", "ERROR", err)
                return False, err
            self._log_frame("RX", "OK", f"FC05 OK")
            return True, f"Coil {address} set to {value}"
        except Exception as e:
            self._log_frame("RX", "ERROR", str(e))
            return False, str(e)

    def write_multiple_coils(self, address: int, values: list[bool], slave: int = 1) -> tuple[bool, str]:
        """Write multiple coils (FC 0x0F)."""
        if not self._connected or not self._client:
            return False, "Not connected"
        self._log_frame("TX", f"FC15 addr={address} count={len(values)}",
                        f"FC15 Write Coils addr={address} values={values} slave={slave}")
        try:
            result = self._client.write_coils(address=address, values=values, slave=slave)
            if result.isError():
                err = str(result)
                self._log_frame("RX", "ERROR", err)
                return False, err
            self._log_frame("RX", "OK", f"FC15 OK count={len(values)}")
            return True, f"Written {len(values)} coils starting at {address}"
        except Exception as e:
            self._log_frame("RX", "ERROR", str(e))
            return False, str(e)

    def update_serial_params(self, baudrate: int = None, parity: str = None,
                             stopbits: int = None, timeout: float = None) -> tuple[bool, str]:
        """Update serial connection parameters (reconnects)."""
        if self._connection_type != ConnectionType.SERIAL_RTU or not self._serial_config:
            return False, "Not a serial connection"
        config = self._serial_config
        if baudrate is not None:
            config.baudrate = baudrate
        if parity is not None:
            config.parity = parity
        if stopbits is not None:
            config.stopbits = stopbits
        if timeout is not None:
            config.timeout = timeout
        return self.connect_serial(config)

    @staticmethod
    def interpret_value(raw: int, data_type: str, scale: float = 1.0) -> float:
        """Interpret a raw register value according to data type and scale."""
        if data_type == "int16":
            if raw > 32767:
                raw = raw - 65536
        elif data_type == "uint16":
            pass
        elif data_type == "int32":
            if raw > 2147483647:
                raw = raw - 4294967296
        return raw * scale

    @staticmethod
    def combine_registers_32bit(high: int, low: int, data_type: str = "uint32") -> int:
        """Combine two 16-bit registers into a 32-bit value."""
        combined = (high << 16) | low
        if data_type in ("int32", "float32"):
            if data_type == "float32":
                packed = struct.pack(">I", combined)
                return struct.unpack(">f", packed)[0]
            if combined > 2147483647:
                combined = combined - 4294967296
        return combined
