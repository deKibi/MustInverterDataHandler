# energy_mode_control/energy_mode_controller.py

# Standard Libraries
from typing import Any, Final

# Custom Modules
from config import (
    ENABLE_AUTO_SWITCH,
    AUTO_SWITCH_TARGET_MODE,
    AUTO_SWITCH_TARGET_TIME,
    ENABLE_GRID_OUTAGE_AUTO_SWITCH,
    GRID_OUTAGE_TARGET_MODE,
    EnergyMode
)
from energy_mode_control.time_utils import is_time_reached
from energy_mode_control.energy_mode_switcher import (
    switch_energy_mode,
)


# Grid availability
GRID_OUTAGE_VOLTAGE_THRESHOLD: Final[float] = 10.0


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
    if not isinstance(must_data, dict):
        print("must_data has invalid type.")
        return False

    current_energy_mode_raw = must_data.get("EnergyUseMode")
    grid_voltage_raw = must_data.get("GridVoltage")

    if current_energy_mode_raw is None:
        print("EnergyUseMode is missing from must_data.")
        return False

    if grid_voltage_raw is None:
        print("GridVoltage is missing from must_data.")
        return False

    try:
        current_energy_mode = EnergyMode(
            int(current_energy_mode_raw)
        )
        grid_voltage = float(grid_voltage_raw)
    except (TypeError, ValueError) as error:
        print(
            "EnergyUseMode or GridVoltage contains "
            f"an invalid value: {error}"
        )
        return False

    is_grid_available = (
        grid_voltage >= GRID_OUTAGE_VOLTAGE_THRESHOLD
    )

    target_mode: EnergyMode | None = None
    switch_reason: str | None = None

    # Grid outage rule has the highest priority.
    if (
            ENABLE_GRID_OUTAGE_AUTO_SWITCH
            and not is_grid_available
    ):
        target_mode = GRID_OUTAGE_TARGET_MODE
        switch_reason = "electrical grid is unavailable"

    # Time-based rule is checked when the grid is available.
    elif (
        ENABLE_AUTO_SWITCH
        and is_grid_available
        and is_time_reached(AUTO_SWITCH_TARGET_TIME)
    ):
        target_mode = AUTO_SWITCH_TARGET_MODE
        switch_reason = "auto-switch target time has been reached"

    if target_mode is None:
        print("No energy mode switch is currently required.")
        return False

    if current_energy_mode == target_mode:
        print(
            f"Inverter is already operating in "
            f"{target_mode.name} mode."
        )
        return False

    print(
        f"Energy mode switch required: "
        f"{current_energy_mode.name} -> {target_mode.name}. "
        f"Reason: {switch_reason}."
    )

    # The real inverter command will be added here:
    switch_energy_mode(
        target_mode=target_mode,
    )
    return True
