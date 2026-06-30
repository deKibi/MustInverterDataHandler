# energy_mode_control/energy_mode_controller.py

# Standard Libraries
from typing import Any

# Custom Modules
from config import (
    ENABLE_AUTO_SWITCH,
    AUTO_SWITCH_TARGET_MODE,
    AUTO_SWITCH_TARGET_TIME,
    ENABLE_GRID_OUTAGE_AUTO_SWITCH,
    GRID_OUTAGE_TARGET_MODE,
    EnergyMode
)

def handle_energy_mode_control(must_data: dict[str, Any] | None) -> bool:
    try:
        return _handle_energy_mode_control(must_data)
    except Exception as e:
        print("Failed to handle energy mode control:", e)
        return False


def _handle_energy_mode_control(must_data: dict[str, Any] | None) -> bool:
    if not ENABLE_AUTO_SWITCH and not ENABLE_GRID_OUTAGE_AUTO_SWITCH:
        print("All automatic energy mode control features are disabled, exiting.")
        return False

    if must_data is None:
        print("must_data is None - cannot control energy mode.")
        return False

    # Further business logic will be here.

    return True
