# energy_mode_control/energy_mode_controller.py

# Standard Libraries
import logging
import time
from typing import Any, Final

# Custom Modules
from config import (
    ENABLE_AUTO_SWITCH,
    ENABLE_SOLAR_AUTO_SWITCH,
    AUTO_SWITCH_TARGET_MODE,
    AUTO_SWITCH_TARGET_TIME,
    ENABLE_GRID_OUTAGE_AUTO_SWITCH,
    ENABLE_INVERTER_CONTROL,
    GRID_OUTAGE_TARGET_MODE,
    SOLAR_AUTO_SWITCH_END_TIME,
    SOLAR_AUTO_SWITCH_START_TIME,
    SOLAR_AUTO_SWITCH_TARGET_MODE,
    EnergyMode
)
from energy_mode_control.solar_auto_switch import (
    should_switch_to_solar_priority,
)
from energy_mode_control.time_utils import is_time_in_window, is_time_reached
from energy_mode_control.energy_mode_switcher import (
    switch_energy_mode,
)


# Grid availability
GRID_OUTAGE_VOLTAGE_THRESHOLD: Final[float] = 10.0
ENERGY_MODE_COMMAND_COOLDOWN_SECONDS: Final[int] = 300
GRID_OUTAGE_SWITCH_RULE: Final[str] = "grid_outage"
SCHEDULED_SWITCH_RULE: Final[str] = "scheduled"
SOLAR_SWITCH_RULE: Final[str] = "solar"

logger = logging.getLogger(__name__)

_last_command_timestamps: dict[tuple[str, EnergyMode], float] = {}


def handle_energy_mode_control(
    must_data: dict[str, Any] | None,
    solar_history: list[dict[str, Any]] | None = None,
) -> bool:
    try:
        return _handle_energy_mode_control(must_data, solar_history)
    except Exception as e:
        logger.exception("Failed to handle energy mode control: %s", e)
        return False


def _handle_energy_mode_control(
    must_data: dict[str, Any] | None,
    solar_history: list[dict[str, Any]] | None = None,
) -> bool:
    if not ENABLE_INVERTER_CONTROL:
        logger.info(
            "Inverter control is disabled; running in read-only mode."
        )
        return False

    if (
        not ENABLE_AUTO_SWITCH
        and not ENABLE_GRID_OUTAGE_AUTO_SWITCH
        and not ENABLE_SOLAR_AUTO_SWITCH
    ):
        logger.info(
            "All automatic energy mode control features are disabled, exiting."
        )
        return False

    if must_data is None:
        logger.warning("must_data is None - cannot control energy mode.")
        return False

    # Further business logic will be here.
    if not isinstance(must_data, dict):
        logger.warning("must_data has invalid type.")
        return False

    current_energy_mode_raw = must_data.get("EnergyUseMode")
    grid_voltage_raw = must_data.get("GridVoltage")

    if current_energy_mode_raw is None:
        logger.warning("EnergyUseMode is missing from must_data.")
        return False

    if grid_voltage_raw is None:
        logger.warning("GridVoltage is missing from must_data.")
        return False

    try:
        current_energy_mode = EnergyMode(
            int(current_energy_mode_raw)
        )
        grid_voltage = float(grid_voltage_raw)
    except (TypeError, ValueError) as error:
        logger.warning(
            "EnergyUseMode or GridVoltage contains "
            "an invalid value: %s",
            error,
        )
        return False

    is_grid_available = (
        grid_voltage >= GRID_OUTAGE_VOLTAGE_THRESHOLD
    )

    target_mode: EnergyMode | None = None
    switch_reason: str | None = None
    switch_rule: str | None = None

    # Grid outage rule has the highest priority.
    if (
            ENABLE_GRID_OUTAGE_AUTO_SWITCH
            and not is_grid_available
    ):
        target_mode = GRID_OUTAGE_TARGET_MODE
        switch_reason = "electrical grid is unavailable"
        switch_rule = GRID_OUTAGE_SWITCH_RULE

    # Time-based rule is checked when the grid is available.
    elif (
        ENABLE_AUTO_SWITCH
        and is_grid_available
        and is_time_reached(AUTO_SWITCH_TARGET_TIME)
        and (
            not ENABLE_SOLAR_AUTO_SWITCH
            or not is_time_in_window(
                start_time=SOLAR_AUTO_SWITCH_START_TIME,
                end_time=SOLAR_AUTO_SWITCH_END_TIME,
            )
        )
    ):
        target_mode = AUTO_SWITCH_TARGET_MODE
        switch_reason = "auto-switch target time has been reached"
        switch_rule = SCHEDULED_SWITCH_RULE

    # Solar rule only switches from SUB while the grid is available.
    elif (
        ENABLE_SOLAR_AUTO_SWITCH
        and is_grid_available
        and current_energy_mode == EnergyMode.SUB
        and should_switch_to_solar_priority(solar_history)
    ):
        target_mode = SOLAR_AUTO_SWITCH_TARGET_MODE
        switch_reason = "solar, battery, and load conditions are suitable"
        switch_rule = SOLAR_SWITCH_RULE

    if target_mode is None or switch_rule is None:
        logger.info("No energy mode switch is currently required.")
        return False

    if current_energy_mode == target_mode:
        logger.info(
            "Inverter is already operating in %s mode.",
            target_mode.name,
        )
        return False

    cooldown_key = (switch_rule, target_mode)
    current_timestamp = time.monotonic()
    last_command_timestamp = _last_command_timestamps.get(cooldown_key)

    if (
        last_command_timestamp is not None
        and current_timestamp - last_command_timestamp
        < ENERGY_MODE_COMMAND_COOLDOWN_SECONDS
    ):
        logger.info(
            "Skipping repeated %s command during the %s-second cooldown.",
            target_mode.name,
            ENERGY_MODE_COMMAND_COOLDOWN_SECONDS,
        )
        return False

    logger.info(
        "Energy mode switch required: %s -> %s. Reason: %s.",
        current_energy_mode.name,
        target_mode.name,
        switch_reason,
    )

    command_response = switch_energy_mode(
        target_mode=target_mode,
    )

    if command_response is False:
        return False

    _last_command_timestamps[cooldown_key] = time.monotonic()
    return True
