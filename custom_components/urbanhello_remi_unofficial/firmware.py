"""Interpret the firmware target assigned to a particular REMI."""
from typing import Any


def firmware_version(value: Any) -> int | None:
    """Accept positive integer firmware versions, including numeric strings."""
    if isinstance(value, bool):
        return None
    if isinstance(value, str) and value.isascii() and value.isdigit():
        value = int(value)
    return value if isinstance(value, int) and value > 0 else None


def firmware_update_requested(remi: dict[str, Any]) -> bool | None:
    """Return the device's explicit update flag without coercing arbitrary values."""
    value = remi.get("firmware_need_update")
    if isinstance(value, (bool, int)) and value in (0, 1):
        return bool(value)
    if value in ("0", "1"):
        return value == "1"
    return None


def firmware_update_available(remi: dict[str, Any], _server_default=None) -> bool | None:
    """Use the assigned target, never the server-wide default, for this device.

    For example a device at 332 can still be assigned 332 while the global
    default is 333. The global version alone does not establish eligibility.
    An explicit flag also covers a requested reinstall of the same version.
    """
    requested = firmware_update_requested(remi)
    if requested is not None:
        return requested
    current = firmware_version(remi.get("current_firmware_version"))
    target = firmware_version(remi.get("update_firmware_version"))
    if current is None or target is None:
        return None
    return target > current
