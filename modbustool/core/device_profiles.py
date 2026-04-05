"""Device profile management — loads register maps from JSON files."""

import json
import os
from dataclasses import dataclass, field


@dataclass
class RegisterDef:
    address: int
    name: str
    description: str = ""
    unit: str = ""
    scale: float = 1.0
    data_type: str = "uint16"
    access: str = "read"
    function_code: int = 3
    function_code_read: int = 3
    function_code_write: int = 6
    min_value: int | None = None
    max_value: int | None = None
    value_map: dict[str, int] | None = None

    def display_value(self, raw: int) -> str:
        """Format raw register value for display."""
        if self.value_map:
            for key, mapped in self.value_map.items():
                if int(key) == raw:
                    return f"{mapped}"
            return f"{raw} (unknown)"

        if self.data_type == "int16" and raw > 32767:
            raw = raw - 65536

        val = raw * self.scale
        if self.scale != 1.0:
            return f"{val:.1f}"
        return str(int(val))

    def reverse_value_map(self, desired: int) -> int | None:
        """Given a human value (e.g. 9600), return the register key."""
        if not self.value_map:
            return desired
        for key, mapped in self.value_map.items():
            if mapped == desired:
                return int(key)
        return None


@dataclass
class DeviceProfile:
    name: str
    manufacturer: str = ""
    description: str = ""
    default_address: int = 1
    default_baudrate: int = 9600
    default_parity: str = "N"
    default_stopbits: int = 1
    default_databits: int = 8
    data_registers: list[RegisterDef] = field(default_factory=list)
    config_registers: list[RegisterDef] = field(default_factory=list)
    file_path: str = ""

    @property
    def all_registers(self) -> list[RegisterDef]:
        return self.data_registers + self.config_registers

    def get_register_by_name(self, name: str) -> RegisterDef | None:
        for reg in self.all_registers:
            if reg.name.lower() == name.lower():
                return reg
        return None

    def get_register_by_address(self, address: int) -> RegisterDef | None:
        for reg in self.all_registers:
            if reg.address == address:
                return reg
        return None

    def get_address_register(self) -> RegisterDef | None:
        """Find the register that controls device address."""
        for reg in self.config_registers:
            if "address" in reg.name.lower() and "humidity" not in reg.name.lower():
                return reg
        return None

    def get_baudrate_register(self) -> RegisterDef | None:
        """Find the register that controls baud rate."""
        for reg in self.config_registers:
            if "baud" in reg.name.lower():
                return reg
        return None


def _parse_address(addr_str: str) -> int:
    """Parse a register address from string (hex or decimal)."""
    if isinstance(addr_str, int):
        return addr_str
    addr_str = addr_str.strip()
    if addr_str.startswith("0x") or addr_str.startswith("0X"):
        return int(addr_str, 16)
    return int(addr_str)


def _parse_register(data: dict) -> RegisterDef:
    """Parse a register definition from JSON dict."""
    reg = RegisterDef(
        address=_parse_address(data["address"]),
        name=data["name"],
        description=data.get("description", ""),
        unit=data.get("unit", ""),
        scale=data.get("scale", 1.0),
        data_type=data.get("data_type", "uint16"),
        access=data.get("access", "read"),
        function_code=data.get("function_code", 3),
        function_code_read=data.get("function_code_read", data.get("function_code", 3)),
        function_code_write=data.get("function_code_write", 6),
        min_value=data.get("min"),
        max_value=data.get("max"),
    )
    if "value_map" in data:
        reg.value_map = {str(k): int(v) for k, v in data["value_map"].items()}
    return reg


def load_profile(filepath: str) -> DeviceProfile:
    """Load a device profile from a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    profile = DeviceProfile(
        name=data.get("name", os.path.basename(filepath)),
        manufacturer=data.get("manufacturer", ""),
        description=data.get("description", ""),
        default_address=data.get("default_address", 1),
        default_baudrate=data.get("default_baudrate", 9600),
        default_parity=data.get("default_parity", "N"),
        default_stopbits=data.get("default_stopbits", 1),
        default_databits=data.get("default_databits", 8),
        file_path=filepath,
    )

    for reg_data in data.get("data_registers", []):
        profile.data_registers.append(_parse_register(reg_data))

    for reg_data in data.get("config_registers", []):
        profile.config_registers.append(_parse_register(reg_data))

    return profile


def save_profile(profile: DeviceProfile, filepath: str):
    """Save a device profile to JSON."""
    def reg_to_dict(reg: RegisterDef) -> dict:
        d = {
            "address": f"0x{reg.address:04X}",
            "name": reg.name,
            "description": reg.description,
            "data_type": reg.data_type,
            "access": reg.access,
            "function_code_read": reg.function_code_read,
            "function_code_write": reg.function_code_write,
        }
        if reg.unit:
            d["unit"] = reg.unit
        if reg.scale != 1.0:
            d["scale"] = reg.scale
        if reg.min_value is not None:
            d["min"] = reg.min_value
        if reg.max_value is not None:
            d["max"] = reg.max_value
        if reg.value_map:
            d["value_map"] = reg.value_map
        return d

    data = {
        "name": profile.name,
        "manufacturer": profile.manufacturer,
        "description": profile.description,
        "default_address": profile.default_address,
        "default_baudrate": profile.default_baudrate,
        "default_parity": profile.default_parity,
        "default_stopbits": profile.default_stopbits,
        "default_databits": profile.default_databits,
        "data_registers": [reg_to_dict(r) for r in profile.data_registers],
        "config_registers": [reg_to_dict(r) for r in profile.config_registers],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class ProfileManager:
    """Manages loading profiles from a directory."""

    def __init__(self, profiles_dir: str = None):
        if profiles_dir is None:
            profiles_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiles")
        self.profiles_dir = profiles_dir
        self.profiles: dict[str, DeviceProfile] = {}
        self.reload()

    def reload(self):
        """Reload all profiles from the profiles directory."""
        self.profiles.clear()
        if not os.path.isdir(self.profiles_dir):
            os.makedirs(self.profiles_dir, exist_ok=True)
            return
        for filename in sorted(os.listdir(self.profiles_dir)):
            if filename.endswith(".json"):
                filepath = os.path.join(self.profiles_dir, filename)
                try:
                    profile = load_profile(filepath)
                    self.profiles[profile.name] = profile
                except Exception as e:
                    print(f"Error loading profile {filename}: {e}")

    def get_profile(self, name: str) -> DeviceProfile | None:
        return self.profiles.get(name)

    def list_profiles(self) -> list[str]:
        return list(self.profiles.keys())

    def add_profile(self, profile: DeviceProfile, filename: str = None):
        if filename is None:
            filename = profile.name.lower().replace(" ", "_").replace("/", "_") + ".json"
        filepath = os.path.join(self.profiles_dir, filename)
        save_profile(profile, filepath)
        profile.file_path = filepath
        self.profiles[profile.name] = profile
