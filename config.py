# config.py

# Standard Libraries
import logging
import math
import os
from datetime import datetime, time
from enum import IntEnum
from typing import Final

# Third-party Libraries
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)

_configuration_warnings: list[str] = []
_defaulted_variables: set[str] = set()
_startup_configuration_logged = False

_INFO_ONLY_DEFAULT_VARIABLES: Final[frozenset[str]] = frozenset({
    "ENABLE_INVERTER_CONTROL",
    "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
    "ENABLE_SOLAR_AUTO_SWITCH",
})

_SCHEDULED_SETTING_VARIABLES: Final[tuple[str, ...]] = (
    "ENABLE_AUTO_SWITCH",
    "AUTO_SWITCH_TARGET_TIME",
    "AUTO_SWITCH_TARGET_MODE",
)

_COMMON_CONTROL_SETTING_VARIABLES: Final[tuple[str, ...]] = (
    "GRID_AVAILABLE_VOLTAGE_THRESHOLD",
)

_GRID_OUTAGE_SETTING_VARIABLES: Final[tuple[str, ...]] = (
    "GRID_OUTAGE_TARGET_MODE",
)

_SOLAR_SETTING_VARIABLES: Final[tuple[str, ...]] = (
    "SOLAR_AUTO_SWITCH_START_TIME",
    "SOLAR_AUTO_SWITCH_END_TIME",
    "SOLAR_AUTO_SWITCH_TARGET_MODE",
    "SOLAR_AUTO_SWITCH_LOOKBACK_MINUTES",
    "SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES",
    "SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES",
    "SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE",
    "SOLAR_AUTO_SWITCH_MAX_LOAD_POWER",
    "SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE",
    "SOLAR_AUTO_SWITCH_MIN_LATEST_BATTERY_VOLTAGE",
    "SOLAR_AUTO_SWITCH_MAX_LATEST_LOAD_POWER",
    "SOLAR_AUTO_SWITCH_MIN_LATEST_PV_VOLTAGE",
)

_INVERTER_CONTROL_SETTING_VARIABLES: Final[tuple[str, ...]] = (
    *_COMMON_CONTROL_SETTING_VARIABLES,
    *_SCHEDULED_SETTING_VARIABLES,
    "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
    *_GRID_OUTAGE_SETTING_VARIABLES,
    "ENABLE_SOLAR_AUTO_SWITCH",
    *_SOLAR_SETTING_VARIABLES,
)


class ConfigurationError(ValueError):
    """Raised when required application configuration is missing."""


def _record_default(variable_name: str, default: object) -> None:
    _defaulted_variables.add(variable_name)

    if variable_name in _INFO_ONLY_DEFAULT_VARIABLES:
        return

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


def get_env_inverter_control(variable_name: str) -> bool:
    """Enable inverter control only for an explicit true value."""
    value = os.getenv(variable_name)

    if value is None or not value.strip():
        _record_default(variable_name, "false")
        return False

    normalized_value = value.strip().lower()

    if normalized_value == "true":
        return True

    if normalized_value == "false":
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

ENABLE_INVERTER_CONTROL: Final[bool] = get_env_inverter_control(
    variable_name="ENABLE_INVERTER_CONTROL",
)

GRID_OUTAGE_VOLTAGE_THRESHOLD: Final[float] = 10.0

GRID_AVAILABLE_VOLTAGE_THRESHOLD: Final[float] = (
    get_env_float(
        variable_name="GRID_AVAILABLE_VOLTAGE_THRESHOLD",
        default=200.0,
        min_value=0.0,
    )
    if ENABLE_INVERTER_CONTROL
    else 200.0
)

ENABLE_AUTO_SWITCH: Final[bool] = (
    get_env_bool(
        variable_name="ENABLE_AUTO_SWITCH",
        default=False,
    )
    if ENABLE_INVERTER_CONTROL
    else False
)

AUTO_SWITCH_TARGET_TIME: Final[time] = (
    get_env_time(
        variable_name="AUTO_SWITCH_TARGET_TIME",
        default="20:00",
    )
    if ENABLE_INVERTER_CONTROL
    else time(hour=20)
)

AUTO_SWITCH_TARGET_MODE: Final[EnergyMode] = (
    get_env_energy_mode(
        variable_name="AUTO_SWITCH_TARGET_MODE",
        default=EnergyMode.SUB,
    )
    if ENABLE_INVERTER_CONTROL
    else EnergyMode.SUB
)

# Grid outage automatic mode switch
ENABLE_GRID_OUTAGE_AUTO_SWITCH: Final[bool] = (
    get_env_bool(
        variable_name="ENABLE_GRID_OUTAGE_AUTO_SWITCH",
        default=False,
    )
    if ENABLE_INVERTER_CONTROL
    else False
)

GRID_OUTAGE_TARGET_MODE: Final[EnergyMode] = (
    get_env_energy_mode(
        variable_name="GRID_OUTAGE_TARGET_MODE",
        default=EnergyMode.SUB,
    )
    if ENABLE_INVERTER_CONTROL
    else EnergyMode.SUB
)

# Solar priority automatic mode switch
ENABLE_SOLAR_AUTO_SWITCH: Final[bool] = (
    get_env_bool(
        variable_name="ENABLE_SOLAR_AUTO_SWITCH",
        default=False,
    )
    if ENABLE_INVERTER_CONTROL
    else False
)

SOLAR_AUTO_SWITCH_START_TIME: Final[time] = (
    get_env_time(
        variable_name="SOLAR_AUTO_SWITCH_START_TIME",
        default="12:00",
    )
    if ENABLE_INVERTER_CONTROL
    else time(hour=12)
)

SOLAR_AUTO_SWITCH_END_TIME: Final[time] = (
    get_env_time(
        variable_name="SOLAR_AUTO_SWITCH_END_TIME",
        default="18:00",
    )
    if ENABLE_INVERTER_CONTROL
    else time(hour=18)
)

SOLAR_AUTO_SWITCH_TARGET_MODE: Final[EnergyMode] = (
    get_env_energy_mode(
        variable_name="SOLAR_AUTO_SWITCH_TARGET_MODE",
        default=EnergyMode.SBU,
    )
    if ENABLE_INVERTER_CONTROL
    else EnergyMode.SBU
)

SOLAR_AUTO_SWITCH_LOOKBACK_MINUTES: Final[int] = (
    get_env_int(
        variable_name="SOLAR_AUTO_SWITCH_LOOKBACK_MINUTES",
        default=10,
        min_value=1,
        max_value=1440,
    )
    if ENABLE_INVERTER_CONTROL
    else 10
)

SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES: Final[int] = (
    get_env_int(
        variable_name="SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES",
        default=8,
        min_value=2,
    )
    if ENABLE_INVERTER_CONTROL
    else 8
)

SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES: Final[int] = (
    get_env_int(
        variable_name="SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES",
        default=5,
        min_value=1,
        max_value=SOLAR_AUTO_SWITCH_LOOKBACK_MINUTES,
    )
    if ENABLE_INVERTER_CONTROL
    else 5
)

SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE: Final[float] = (
    get_env_float(
        variable_name="SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE",
        default=26.8,
        min_value=0.0,
    )
    if ENABLE_INVERTER_CONTROL
    else 26.8
)

SOLAR_AUTO_SWITCH_MAX_LOAD_POWER: Final[float] = (
    get_env_float(
        variable_name="SOLAR_AUTO_SWITCH_MAX_LOAD_POWER",
        default=400.0,
        min_value=0.0,
    )
    if ENABLE_INVERTER_CONTROL
    else 400.0
)

SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE: Final[float] = (
    get_env_float(
        variable_name="SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE",
        default=38.0,
        min_value=0.0,
    )
    if ENABLE_INVERTER_CONTROL
    else 38.0
)

SOLAR_AUTO_SWITCH_MIN_LATEST_BATTERY_VOLTAGE: Final[float] = (
    get_env_float(
        variable_name="SOLAR_AUTO_SWITCH_MIN_LATEST_BATTERY_VOLTAGE",
        default=26.4,
        min_value=0.0,
    )
    if ENABLE_INVERTER_CONTROL
    else 26.4
)

SOLAR_AUTO_SWITCH_MAX_LATEST_LOAD_POWER: Final[float] = (
    get_env_float(
        variable_name="SOLAR_AUTO_SWITCH_MAX_LATEST_LOAD_POWER",
        default=500.0,
        min_value=0.0,
    )
    if ENABLE_INVERTER_CONTROL
    else 500.0
)

SOLAR_AUTO_SWITCH_MIN_LATEST_PV_VOLTAGE: Final[float] = (
    get_env_float(
        variable_name="SOLAR_AUTO_SWITCH_MIN_LATEST_PV_VOLTAGE",
        default=35.0,
        min_value=0.0,
    )
    if ENABLE_INVERTER_CONTROL
    else 35.0
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

    if (
        ENABLE_INVERTER_CONTROL
        and SOLAR_AUTO_SWITCH_START_TIME >= SOLAR_AUTO_SWITCH_END_TIME
    ):
        errors.append(
            "SOLAR_AUTO_SWITCH_START_TIME must be earlier than "
            "SOLAR_AUTO_SWITCH_END_TIME"
        )

    if (
        ENABLE_INVERTER_CONTROL
        and GRID_AVAILABLE_VOLTAGE_THRESHOLD
        <= GRID_OUTAGE_VOLTAGE_THRESHOLD
    ):
        errors.append(
            "GRID_AVAILABLE_VOLTAGE_THRESHOLD must be greater than "
            "GRID_OUTAGE_VOLTAGE_THRESHOLD"
        )

    if errors:
        raise ConfigurationError("; ".join(errors))


def log_startup_configuration() -> None:
    """Log a safe startup summary and deferred warnings exactly once."""
    global _startup_configuration_logged

    if _startup_configuration_logged:
        return

    summary_lines = [
        "Startup configuration:",
        f"  MySQL port: {_format_setting('MYSQL_PORT')}",
        f"  Inverter serial port: {_format_setting('MUST_PORT')}",
        f"  Data gathering interval: "
        f"{_format_setting('DATA_GATHER_INTERVAL_SECONDS')} seconds",
        f"  Inverter control: {_format_setting('ENABLE_INVERTER_CONTROL')}",
    ]

    if not ENABLE_INVERTER_CONTROL:
        logger.info("Configuration loaded and validated.")
        logger.info("\n".join(summary_lines))

        for warning_message in _configuration_warnings:
            if any(
                variable_name in warning_message
                for variable_name in _INVERTER_CONTROL_SETTING_VARIABLES
            ):
                continue

            logger.warning(warning_message)

        _startup_configuration_logged = True
        return

    grid_outage_explicit_settings = _get_explicit_variables(
        _GRID_OUTAGE_SETTING_VARIABLES,
    )
    solar_explicit_settings = _get_explicit_variables(
        _SOLAR_SETTING_VARIABLES,
    )
    summary_lines.append(
        "  Grid voltage states: unavailable < "
        f"{GRID_OUTAGE_VOLTAGE_THRESHOLD:g} V; available >= "
        f"{_format_setting('GRID_AVAILABLE_VOLTAGE_THRESHOLD')} V"
    )
    summary_lines.append(
        f"  Scheduled auto-switch: {_format_setting('ENABLE_AUTO_SWITCH')}; "
        f"target time: {_format_setting('AUTO_SWITCH_TARGET_TIME')}; "
        f"target mode: {_format_setting('AUTO_SWITCH_TARGET_MODE')}"
    )

    grid_outage_status = _format_setting(
        "ENABLE_GRID_OUTAGE_AUTO_SWITCH"
    )
    if ENABLE_GRID_OUTAGE_AUTO_SWITCH:
        summary_lines.append(
            f"  Grid outage auto-switch: {grid_outage_status}; "
            f"target mode: {_format_setting('GRID_OUTAGE_TARGET_MODE')}"
        )
    else:
        summary_lines.append(f"  Grid outage auto-switch: {grid_outage_status}")
        if "GRID_OUTAGE_TARGET_MODE" in grid_outage_explicit_settings:
            summary_lines.append(
                "  GRID_OUTAGE_TARGET_MODE: "
                f"{_format_configured_value('GRID_OUTAGE_TARGET_MODE')} "
                "(unused)"
            )

    solar_status = _format_setting("ENABLE_SOLAR_AUTO_SWITCH")
    if ENABLE_SOLAR_AUTO_SWITCH:
        summary_lines.extend([
            f"  Solar auto-switch: {solar_status}; window: "
            f"{_format_setting('SOLAR_AUTO_SWITCH_START_TIME')}-"
            f"{_format_setting('SOLAR_AUTO_SWITCH_END_TIME')}; "
            "target mode: "
            f"{_format_setting('SOLAR_AUTO_SWITCH_TARGET_MODE')}",
            "  Solar history: "
            f"{_format_setting('SOLAR_AUTO_SWITCH_LOOKBACK_MINUTES')} "
            "minutes; minimum samples: "
            f"{_format_setting('SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES')}; "
            "minimum span: "
            f"{_format_setting('SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES')} "
            "minutes",
            "  Solar average thresholds: battery >= "
            f"{_format_setting('SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE')} V; "
            "load <= "
            f"{_format_setting('SOLAR_AUTO_SWITCH_MAX_LOAD_POWER')} W; "
            f"PV >= {_format_setting('SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE')} V",
            "  Solar latest limits: battery >= "
            f"{_format_setting('SOLAR_AUTO_SWITCH_MIN_LATEST_BATTERY_VOLTAGE')} "
            "V; load <= "
            f"{_format_setting('SOLAR_AUTO_SWITCH_MAX_LATEST_LOAD_POWER')} "
            "W; PV >= "
            f"{_format_setting('SOLAR_AUTO_SWITCH_MIN_LATEST_PV_VOLTAGE')} V.",
        ])
    else:
        summary_lines.append(f"  Solar auto-switch: {solar_status}")
        summary_lines.extend(
            f"  {name}: {_format_configured_value(name)} (unused)"
            for name in solar_explicit_settings
        )

    logger.info("Configuration loaded and validated.")
    logger.info("\n".join(summary_lines))

    suppressed_default_warnings: set[str] = set()
    if not ENABLE_GRID_OUTAGE_AUTO_SWITCH:
        suppressed_default_warnings.update(_GRID_OUTAGE_SETTING_VARIABLES)
    if not ENABLE_SOLAR_AUTO_SWITCH:
        suppressed_default_warnings.update(_SOLAR_SETTING_VARIABLES)

    for warning_message in _configuration_warnings:
        if any(
            variable_name in _defaulted_variables
            and warning_message.startswith(
                f"{variable_name} is not configured;"
            )
            for variable_name in suppressed_default_warnings
        ):
            continue

        logger.warning(warning_message)

    if not ENABLE_GRID_OUTAGE_AUTO_SWITCH and grid_outage_explicit_settings:
        logger.warning(
            "Grid outage auto-switch is disabled; configured related "
            "settings are unused: %s.",
            ", ".join(grid_outage_explicit_settings),
        )

    if not ENABLE_SOLAR_AUTO_SWITCH and solar_explicit_settings:
        logger.warning(
            "Solar auto-switch is disabled; configured related settings "
            "are unused: %s.",
            ", ".join(solar_explicit_settings),
        )

    _startup_configuration_logged = True


def _get_explicit_variables(variable_names: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        variable_name
        for variable_name in variable_names
        if variable_name not in _defaulted_variables
    )


def _format_setting(variable_name: str) -> str:
    return _format_summary_value(
        variable_name,
        _format_configured_value(variable_name),
    )


def _format_configured_value(variable_name: str) -> str:
    value = globals()[variable_name]

    if isinstance(value, bool):
        return _format_bool(value)

    if isinstance(value, time):
        return value.strftime("%H:%M")

    if isinstance(value, EnergyMode):
        return value.name

    return str(value)


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
