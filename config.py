# config.py

# Standard Libraries
import logging
import os
from datetime import datetime, time
from enum import IntEnum
from typing import Final

# Third-Party Libraries
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)


class EnergyMode(IntEnum):
    """
    Inverter energy mode codes.

    Replace the codes below with the actual codes used by the inverter.
    """

    # 1 = SBU, 2 = SUB, 3 = UTI, 4 = SOL
    SBU = 1
    SUB = 2
    UTI = 3
    SOL = 4

def get_env_bool(variable_name: str, default: bool = False) -> bool:
    """
    Read and convert a boolean environment variable.
    """
    value = os.getenv(variable_name)

    if value is None:
        return default

    normalized_value = value.strip().lower()

    if normalized_value in {"true", "1", "yes", "on"}:
        return True

    if normalized_value in {"false", "0", "no", "off"}:
        return False

    raise ValueError(
        f"Environment variable {variable_name} must contain true or false"
    )


def get_env_int(
    variable_name: str,
    default: int,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """
    Read an integer environment variable.

    Returns the default value if the variable is missing
    or contains an invalid value.

    Optionally limits the value to a minimum and maximum.
    """
    raw_value = os.getenv(variable_name)

    if raw_value is None:
        return default

    try:
        value = int(raw_value.strip())
    except (TypeError, ValueError):
        logger.warning(
            "Invalid value for %s: %r. Using default value: %s.",
            variable_name,
            raw_value,
            default,
        )
        return default

    if min_value is not None and value < min_value:
        logger.warning(
            "%s is below the minimum value of %s. Using %s.",
            variable_name,
            min_value,
            min_value,
        )
        return min_value

    if max_value is not None and value > max_value:
        logger.warning(
            "%s is above the maximum value of %s. Using %s.",
            variable_name,
            max_value,
            max_value,
        )
        return max_value

    return value


def get_env_time(variable_name: str, default: str) -> time:
    """
    Read an environment variable in HH:MM format and convert it to time.
    """
    value = os.getenv(variable_name, default)

    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as error:
        raise ValueError(
            f"Environment variable {variable_name} "
            f"must use the HH:MM format"
        ) from error


def get_env_energy_mode(
    variable_name: str,
    default: EnergyMode,
) -> EnergyMode:
    """
    Read an energy mode name and convert it to EnergyMode.
    """
    value = os.getenv(variable_name, default.name).strip().upper()

    try:
        return EnergyMode[value]
    except KeyError as error:
        allowed_modes = ", ".join(mode.name for mode in EnergyMode)

        raise ValueError(
            f"Environment variable {variable_name} contains "
            f"unsupported mode {value}. Allowed modes: {allowed_modes}"
        ) from error


MUST_PORT: Final[str] = os.getenv("MUST_PORT", "COM3")

DATA_GATHER_INTERVAL_SECONDS: Final[int] = get_env_int(
    variable_name="DATA_GATHER_INTERVAL_SECONDS",
    default=60,
    min_value=10,
    max_value=3600,
)

ENABLE_AUTO_SWITCH: Final[bool] = get_env_bool(
    variable_name="ENABLE_AUTO_SWITCH",
    default=False,
)

AUTO_SWITCH_TARGET_TIME: Final[time] = get_env_time(
    variable_name="AUTO_SWITCH_TARGET_TIME",
    default="20:00",
)

AUTO_SWITCH_TARGET_MODE: Final[EnergyMode] = get_env_energy_mode(
    variable_name="AUTO_SWITCH_TARGET_MODE",
    default=EnergyMode.SUB,
)

# Grid outage automatic mode switch
ENABLE_GRID_OUTAGE_AUTO_SWITCH: Final[bool] = (
    get_env_bool(
        variable_name="ENABLE_GRID_OUTAGE_AUTO_SWITCH",
        default=False,
    )
)

GRID_OUTAGE_TARGET_MODE: Final[EnergyMode] = (
    get_env_energy_mode(
        variable_name="GRID_OUTAGE_TARGET_MODE",
        default=EnergyMode.SUB,
    )
)


if __name__ == '__main__':
    print("debugging config.py")

    # if (
    #         ENABLE_AUTO_SWITCH
    #         and is_time_reached(AUTO_SWITCH_TARGET_TIME)
    #         and current_energy_mode != AUTO_SWITCH_TARGET_MODE.value
    # ):
    #     switch_energy_mode(AUTO_SWITCH_TARGET_MODE.value)

    print("Enable auto switch:", ENABLE_AUTO_SWITCH)
    print("Object Type:", type(ENABLE_AUTO_SWITCH))

    auto_switch_target_mode_name = AUTO_SWITCH_TARGET_MODE.name
    print("Auto switch target mode name:", auto_switch_target_mode_name)
    print("Object Type:", type(auto_switch_target_mode_name))

    auto_switch_target_mode_code = AUTO_SWITCH_TARGET_MODE.value
    print("Auto switch target mode code:", auto_switch_target_mode_code)
    print("Object Type:", type(auto_switch_target_mode_code))

    grid_outage_auto_switch = ENABLE_GRID_OUTAGE_AUTO_SWITCH
    print("Grid outage auto switch:", grid_outage_auto_switch)
    print("Object Type:", type(grid_outage_auto_switch))

    grid_outage_target_mode_name = GRID_OUTAGE_TARGET_MODE.name
    grid_outage_target_mode_code = GRID_OUTAGE_TARGET_MODE.value
    print("Grid outage target mode:", grid_outage_target_mode_name)
    print("Object Type:", type(grid_outage_target_mode_name))
    print("Grid outage target mode code:", grid_outage_target_mode_code)
    print("Object Type:", type(grid_outage_target_mode_code))
