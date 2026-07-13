# config.py

# Standard Libraries
import logging
import math
import os
from datetime import datetime, time
from enum import IntEnum
from typing import Final

# Third-Party Libraries
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)

_configuration_warnings: list[str] = []
_defaulted_variables: set[str] = set()
_startup_configuration_logged = False


class ConfigurationError(ValueError):
    """Raised when required application configuration is missing."""


def _record_default(variable_name: str, default: object) -> None:
    _defaulted_variables.add(variable_name)
    _configuration_warnings.append(
        f"{variable_name} is not configured; using {default} default."
    )


def _record_warning(message: str) -> None:
    _configuration_warnings.append(message)


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

    if value is None or not value.strip():
        _record_default(variable_name, str(default).lower())
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

    if raw_value is None or not raw_value.strip():
        _record_default(variable_name, default)
        return default

    try:
        value = int(raw_value.strip())
    except (TypeError, ValueError):
        _record_warning(
            f"Invalid value for {variable_name}: {raw_value!r}. "
            f"Using default value: {default}."
        )
        return default

    if min_value is not None and value < min_value:
        _record_warning(
            f"{variable_name} is below the minimum value of {min_value}. "
            f"Using {min_value}."
        )
        return min_value

    if max_value is not None and value > max_value:
        _record_warning(
            f"{variable_name} is above the maximum value of {max_value}. "
            f"Using {max_value}."
        )
        return max_value

    return value


def get_env_float(
    variable_name: str,
    default: float,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    """Read and optionally limit a floating-point environment variable."""
    raw_value = os.getenv(variable_name)

    if raw_value is None or not raw_value.strip():
        _record_default(variable_name, default)
        return default

    try:
        value = float(raw_value.strip())
    except (TypeError, ValueError):
        _record_warning(
            f"Invalid value for {variable_name}: {raw_value!r}. "
            f"Using default value: {default}."
        )
        return default

    if not math.isfinite(value):
        _record_warning(
            f"Invalid value for {variable_name}: {raw_value!r}. "
            f"Using default value: {default}."
        )
        return default

    if min_value is not None and value < min_value:
        _record_warning(
            f"{variable_name} is below the minimum value of {min_value}. "
            f"Using {min_value}."
        )
        return min_value

    if max_value is not None and value > max_value:
        _record_warning(
            f"{variable_name} is above the maximum value of {max_value}. "
            f"Using {max_value}."
        )
        return max_value

    return value


def get_env_time(variable_name: str, default: str) -> time:
    """
    Read an environment variable in HH:MM format and convert it to time.
    """
    value = os.getenv(variable_name)

    if value is None or not value.strip():
        _record_default(variable_name, default)
        value = default

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
    value = os.getenv(variable_name)

    if value is None or not value.strip():
        _record_default(variable_name, default.name)
        value = default.name

    value = value.strip().upper()

    try:
        return EnergyMode[value]
    except KeyError as error:
        allowed_modes = ", ".join(mode.name for mode in EnergyMode)

        raise ValueError(
            f"Environment variable {variable_name} contains "
            f"unsupported mode {value}. Allowed modes: {allowed_modes}"
        ) from error


def get_env_string(variable_name: str, default: str) -> str:
    """Read a string environment variable or record its default."""
    value = os.getenv(variable_name)

    if value is None or not value.strip():
        _record_default(variable_name, default)
        return default

    return value


def get_env_port(variable_name: str, default: int) -> int:
    """Read a TCP port, using the default for missing or invalid values."""
    raw_value = os.getenv(variable_name)

    if raw_value is None or not raw_value.strip():
        _record_default(variable_name, default)
        return default

    try:
        value = int(raw_value.strip())
    except (TypeError, ValueError):
        _record_warning(
            f"Invalid value for {variable_name}: {raw_value!r}. "
            f"Using default value: {default}."
        )
        return default

    if not 1 <= value <= 65535:
        _record_warning(
            f"{variable_name} must be between 1 and 65535. "
            f"Using default value: {default}."
        )
        return default

    return value


MYSQL_HOST: Final[str | None] = os.getenv("MYSQL_HOST")
MYSQL_DATABASE: Final[str | None] = os.getenv("MYSQL_DATABASE")
MYSQL_USER: Final[str | None] = os.getenv("MYSQL_USER")
MYSQL_PASSWORD: Final[str | None] = os.getenv("MYSQL_PASSWORD")
MYSQL_PORT: Final[int] = get_env_port("MYSQL_PORT", 3306)

MUST_PORT: Final[str] = get_env_string("MUST_PORT", "COM3")

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

# Solar priority automatic mode switch
ENABLE_SOLAR_AUTO_SWITCH: Final[bool] = get_env_bool(
    variable_name="ENABLE_SOLAR_AUTO_SWITCH",
    default=False,
)

SOLAR_AUTO_SWITCH_START_TIME: Final[time] = get_env_time(
    variable_name="SOLAR_AUTO_SWITCH_START_TIME",
    default="12:00",
)

SOLAR_AUTO_SWITCH_END_TIME: Final[time] = get_env_time(
    variable_name="SOLAR_AUTO_SWITCH_END_TIME",
    default="18:00",
)

SOLAR_AUTO_SWITCH_TARGET_MODE: Final[EnergyMode] = get_env_energy_mode(
    variable_name="SOLAR_AUTO_SWITCH_TARGET_MODE",
    default=EnergyMode.SBU,
)

SOLAR_AUTO_SWITCH_LOOKBACK_MINUTES: Final[int] = get_env_int(
    variable_name="SOLAR_AUTO_SWITCH_LOOKBACK_MINUTES",
    default=10,
    min_value=1,
    max_value=1440,
)

SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES: Final[int] = get_env_int(
    variable_name="SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES",
    default=8,
    min_value=2,
)

SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES: Final[int] = get_env_int(
    variable_name="SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES",
    default=5,
    min_value=1,
    max_value=SOLAR_AUTO_SWITCH_LOOKBACK_MINUTES,
)

SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE: Final[float] = get_env_float(
    variable_name="SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE",
    default=26.8,
    min_value=0.0,
)

SOLAR_AUTO_SWITCH_MAX_LOAD_POWER: Final[float] = get_env_float(
    variable_name="SOLAR_AUTO_SWITCH_MAX_LOAD_POWER",
    default=400.0,
    min_value=0.0,
)

SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE: Final[float] = get_env_float(
    variable_name="SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE",
    default=38.0,
    min_value=0.0,
)

SOLAR_AUTO_SWITCH_MIN_LATEST_BATTERY_VOLTAGE: Final[float] = get_env_float(
    variable_name="SOLAR_AUTO_SWITCH_MIN_LATEST_BATTERY_VOLTAGE",
    default=26.4,
    min_value=0.0,
)

SOLAR_AUTO_SWITCH_MAX_LATEST_LOAD_POWER: Final[float] = get_env_float(
    variable_name="SOLAR_AUTO_SWITCH_MAX_LATEST_LOAD_POWER",
    default=500.0,
    min_value=0.0,
)

SOLAR_AUTO_SWITCH_MIN_LATEST_PV_VOLTAGE: Final[float] = get_env_float(
    variable_name="SOLAR_AUTO_SWITCH_MIN_LATEST_PV_VOLTAGE",
    default=35.0,
    min_value=0.0,
)


def validate_configuration() -> None:
    """Validate required settings before hardware or database startup."""
    required_mysql_values = {
        "MYSQL_HOST": MYSQL_HOST,
        "MYSQL_DATABASE": MYSQL_DATABASE,
        "MYSQL_USER": MYSQL_USER,
        "MYSQL_PASSWORD": MYSQL_PASSWORD,
    }
    missing_variables = [
        variable_name
        for variable_name, value in required_mysql_values.items()
        if value is None or not value.strip()
    ]
    errors = []

    if missing_variables:
        errors.append(
            "Missing required environment variables: "
            + ", ".join(missing_variables)
        )

    if SOLAR_AUTO_SWITCH_START_TIME >= SOLAR_AUTO_SWITCH_END_TIME:
        errors.append(
            "SOLAR_AUTO_SWITCH_START_TIME must be earlier than "
            "SOLAR_AUTO_SWITCH_END_TIME"
        )

    if errors:
        raise ConfigurationError("; ".join(errors))


def log_startup_configuration() -> None:
    """Log a safe startup summary and deferred warnings exactly once."""
    global _startup_configuration_logged

    if _startup_configuration_logged:
        return

    logger.info("Configuration loaded and validated.")
    logger.info(
        "Startup configuration:\n"
        "  MySQL host: configured\n"
        "  MySQL database: configured\n"
        "  MySQL user: configured\n"
        "  MySQL password: configured\n"
        "  MySQL port: %s\n"
        "  Inverter serial port: %s\n"
        "  Data gathering interval: %s seconds\n"
        "  Scheduled auto-switch: %s; target time: %s; target mode: %s\n"
        "  Grid outage auto-switch: %s; target mode: %s\n"
        "  Solar auto-switch: %s; window: %s-%s; target mode: %s\n"
        "  Solar history: %s minutes; minimum samples: %s; "
        "minimum span: %s minutes\n"
        "  Solar average thresholds: battery >= %s V; "
        "load <= %s W; PV >= %s V\n"
        "  Solar latest limits: battery >= %s V; "
        "load <= %s W; PV >= %s V.",
        _format_summary_value("MYSQL_PORT", MYSQL_PORT),
        _format_summary_value("MUST_PORT", MUST_PORT),
        _format_summary_value(
            "DATA_GATHER_INTERVAL_SECONDS",
            DATA_GATHER_INTERVAL_SECONDS,
        ),
        _format_summary_value(
            "ENABLE_AUTO_SWITCH",
            _format_bool(ENABLE_AUTO_SWITCH),
        ),
        _format_summary_value(
            "AUTO_SWITCH_TARGET_TIME",
            AUTO_SWITCH_TARGET_TIME.strftime("%H:%M"),
        ),
        _format_summary_value(
            "AUTO_SWITCH_TARGET_MODE",
            AUTO_SWITCH_TARGET_MODE.name,
        ),
        _format_summary_value(
            "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
            _format_bool(ENABLE_GRID_OUTAGE_AUTO_SWITCH),
        ),
        _format_summary_value(
            "GRID_OUTAGE_TARGET_MODE",
            GRID_OUTAGE_TARGET_MODE.name,
        ),
        _format_summary_value(
            "ENABLE_SOLAR_AUTO_SWITCH",
            _format_bool(ENABLE_SOLAR_AUTO_SWITCH),
        ),
        _format_summary_value(
            "SOLAR_AUTO_SWITCH_START_TIME",
            SOLAR_AUTO_SWITCH_START_TIME.strftime("%H:%M"),
        ),
        _format_summary_value(
            "SOLAR_AUTO_SWITCH_END_TIME",
            SOLAR_AUTO_SWITCH_END_TIME.strftime("%H:%M"),
        ),
        _format_summary_value(
            "SOLAR_AUTO_SWITCH_TARGET_MODE",
            SOLAR_AUTO_SWITCH_TARGET_MODE.name,
        ),
        _format_summary_value(
            "SOLAR_AUTO_SWITCH_LOOKBACK_MINUTES",
            SOLAR_AUTO_SWITCH_LOOKBACK_MINUTES,
        ),
        _format_summary_value(
            "SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES",
            SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES,
        ),
        _format_summary_value(
            "SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES",
            SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES,
        ),
        _format_summary_value(
            "SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE",
            SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE,
        ),
        _format_summary_value(
            "SOLAR_AUTO_SWITCH_MAX_LOAD_POWER",
            SOLAR_AUTO_SWITCH_MAX_LOAD_POWER,
        ),
        _format_summary_value(
            "SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE",
            SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE,
        ),
        _format_summary_value(
            "SOLAR_AUTO_SWITCH_MIN_LATEST_BATTERY_VOLTAGE",
            SOLAR_AUTO_SWITCH_MIN_LATEST_BATTERY_VOLTAGE,
        ),
        _format_summary_value(
            "SOLAR_AUTO_SWITCH_MAX_LATEST_LOAD_POWER",
            SOLAR_AUTO_SWITCH_MAX_LATEST_LOAD_POWER,
        ),
        _format_summary_value(
            "SOLAR_AUTO_SWITCH_MIN_LATEST_PV_VOLTAGE",
            SOLAR_AUTO_SWITCH_MIN_LATEST_PV_VOLTAGE,
        ),
    )

    for warning_message in _configuration_warnings:
        logger.warning(warning_message)

    _startup_configuration_logged = True


def _format_summary_value(variable_name: str, value: object) -> str:
    if variable_name in _defaulted_variables:
        return f"not configured (using {value} default)"

    return str(value)


def _format_bool(value: bool) -> str:
    return str(value).lower()


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
