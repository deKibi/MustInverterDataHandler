# config.py

# Standard Libraries
from datetime import datetime, time
from enum import IntEnum
import logging
import os
from typing import Final

# Third-party Libraries
from dotenv import load_dotenv


load_dotenv()

LOGGER = logging.getLogger(__name__)


def is_env_configured(variable_name: str) -> bool:
    """Return whether an environment variable has a non-empty value."""
    return bool(os.getenv(variable_name, "").strip())


def get_env_str(variable_name: str, default: str) -> str:
    """Read a non-empty string environment variable or use its default."""
    value = os.getenv(variable_name)

    if value is None:
        return default

    normalized_value = value.strip()

    if not normalized_value:
        raise ValueError(
            f"Environment variable {variable_name} must not be empty"
        )

    return normalized_value


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

    Returns the default value if the variable is missing. Explicitly
    configured values must be valid and within the optional bounds.
    """
    raw_value = os.getenv(variable_name)

    if raw_value is None:
        return default

    try:
        value = int(raw_value.strip())
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Environment variable {variable_name} must be an integer"
        ) from error

    if min_value is not None and value < min_value:
        raise ValueError(
            f"Environment variable {variable_name} must be at least "
            f"{min_value}"
        )

    if max_value is not None and value > max_value:
        raise ValueError(
            f"Environment variable {variable_name} must not exceed "
            f"{max_value}"
        )

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


def get_env_log_level(variable_name: str, default: str) -> int:
    """Read a standard logging level name or use its default."""
    value = get_env_str(variable_name, default).upper()
    allowed_levels = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }

    if value not in allowed_levels:
        allowed_level_names = ", ".join(allowed_levels)
        raise ValueError(
            f"Environment variable {variable_name} contains unsupported "
            f"level {value}. Allowed levels: {allowed_level_names}"
        )

    return allowed_levels[value]


DEFAULT_MUST_PORT: Final[str] = "COM3"
MUST_PORT_IS_CONFIGURED: Final[bool] = is_env_configured("MUST_PORT")
MUST_PORT: Final[str] = get_env_str("MUST_PORT", DEFAULT_MUST_PORT)

DEFAULT_MYSQL_HOST: Final[str] = "localhost"
MYSQL_HOST_IS_CONFIGURED: Final[bool] = is_env_configured("MYSQL_HOST")
MYSQL_HOST: Final[str] = get_env_str("MYSQL_HOST", DEFAULT_MYSQL_HOST)

DEFAULT_MYSQL_DATABASE: Final[str] = "must_data"
MYSQL_DATABASE_IS_CONFIGURED: Final[bool] = is_env_configured(
    "MYSQL_DATABASE"
)
MYSQL_DATABASE: Final[str] = get_env_str(
    "MYSQL_DATABASE",
    DEFAULT_MYSQL_DATABASE,
)

DEFAULT_MYSQL_USER: Final[str] = "root"
MYSQL_USER_IS_CONFIGURED: Final[bool] = is_env_configured("MYSQL_USER")
MYSQL_USER: Final[str] = get_env_str("MYSQL_USER", DEFAULT_MYSQL_USER)

DEFAULT_MYSQL_PASSWORD: Final[str] = ""
MYSQL_PASSWORD_IS_CONFIGURED: Final[bool] = is_env_configured(
    "MYSQL_PASSWORD"
)
MYSQL_PASSWORD: Final[str] = get_env_str(
    "MYSQL_PASSWORD",
    DEFAULT_MYSQL_PASSWORD,
)

DEFAULT_DATA_GATHER_INTERVAL_SECONDS: Final[int] = 60
DATA_GATHER_INTERVAL_SECONDS_IS_CONFIGURED: Final[bool] = is_env_configured(
    "DATA_GATHER_INTERVAL_SECONDS"
)
DATA_GATHER_INTERVAL_SECONDS: Final[int] = get_env_int(
    variable_name="DATA_GATHER_INTERVAL_SECONDS",
    default=DEFAULT_DATA_GATHER_INTERVAL_SECONDS,
    min_value=10,
    max_value=3600,
)

DEFAULT_ENABLE_AUTO_SWITCH: Final[bool] = False
ENABLE_AUTO_SWITCH_IS_CONFIGURED: Final[bool] = is_env_configured(
    "ENABLE_AUTO_SWITCH"
)
ENABLE_AUTO_SWITCH: Final[bool] = get_env_bool(
    variable_name="ENABLE_AUTO_SWITCH",
    default=DEFAULT_ENABLE_AUTO_SWITCH,
)

DEFAULT_AUTO_SWITCH_TARGET_TIME: Final[str] = "20:00"
AUTO_SWITCH_TARGET_TIME_IS_CONFIGURED: Final[bool] = is_env_configured(
    "AUTO_SWITCH_TARGET_TIME"
)
AUTO_SWITCH_TARGET_TIME: Final[time] = get_env_time(
    variable_name="AUTO_SWITCH_TARGET_TIME",
    default=DEFAULT_AUTO_SWITCH_TARGET_TIME,
)

DEFAULT_AUTO_SWITCH_TARGET_MODE: Final[EnergyMode] = EnergyMode.SUB
AUTO_SWITCH_TARGET_MODE_IS_CONFIGURED: Final[bool] = is_env_configured(
    "AUTO_SWITCH_TARGET_MODE"
)
AUTO_SWITCH_TARGET_MODE: Final[EnergyMode] = get_env_energy_mode(
    variable_name="AUTO_SWITCH_TARGET_MODE",
    default=DEFAULT_AUTO_SWITCH_TARGET_MODE,
)

# Grid outage automatic mode switch
DEFAULT_ENABLE_GRID_OUTAGE_AUTO_SWITCH: Final[bool] = False
ENABLE_GRID_OUTAGE_AUTO_SWITCH_IS_CONFIGURED: Final[bool] = (
    is_env_configured("ENABLE_GRID_OUTAGE_AUTO_SWITCH")
)
ENABLE_GRID_OUTAGE_AUTO_SWITCH: Final[bool] = (
    get_env_bool(
        variable_name="ENABLE_GRID_OUTAGE_AUTO_SWITCH",
        default=DEFAULT_ENABLE_GRID_OUTAGE_AUTO_SWITCH,
    )
)

DEFAULT_GRID_OUTAGE_TARGET_MODE: Final[EnergyMode] = EnergyMode.SUB
GRID_OUTAGE_TARGET_MODE_IS_CONFIGURED: Final[bool] = is_env_configured(
    "GRID_OUTAGE_TARGET_MODE"
)
GRID_OUTAGE_TARGET_MODE: Final[EnergyMode] = (
    get_env_energy_mode(
        variable_name="GRID_OUTAGE_TARGET_MODE",
        default=DEFAULT_GRID_OUTAGE_TARGET_MODE,
    )
)

DEFAULT_LOG_LEVEL: Final[str] = "INFO"
LOG_LEVEL_IS_CONFIGURED: Final[bool] = is_env_configured("LOG_LEVEL")
LOG_LEVEL: Final[int] = get_env_log_level("LOG_LEVEL", DEFAULT_LOG_LEVEL)


def _configuration_value_status(
    value: str,
    configured: bool,
    default: str,
) -> str:
    if configured:
        return value

    return f"not configured (using {default} default)"


def get_startup_configuration_summary() -> str:
    """Return a safe, human-readable summary of the active configuration."""
    password_status = (
        "configured"
        if MYSQL_PASSWORD_IS_CONFIGURED
        else "not configured (using empty default)"
    )
    auto_switch_status = _configuration_value_status(
        "enabled" if ENABLE_AUTO_SWITCH else "disabled",
        ENABLE_AUTO_SWITCH_IS_CONFIGURED,
        "disabled",
    )
    outage_switch_status = _configuration_value_status(
        "enabled" if ENABLE_GRID_OUTAGE_AUTO_SWITCH else "disabled",
        ENABLE_GRID_OUTAGE_AUTO_SWITCH_IS_CONFIGURED,
        "disabled",
    )
    time_target_time_status = _configuration_value_status(
        AUTO_SWITCH_TARGET_TIME.strftime("%H:%M"),
        AUTO_SWITCH_TARGET_TIME_IS_CONFIGURED,
        DEFAULT_AUTO_SWITCH_TARGET_TIME,
    )
    time_target_mode_status = _configuration_value_status(
        AUTO_SWITCH_TARGET_MODE.name,
        AUTO_SWITCH_TARGET_MODE_IS_CONFIGURED,
        DEFAULT_AUTO_SWITCH_TARGET_MODE.name,
    )
    outage_target_mode_status = _configuration_value_status(
        GRID_OUTAGE_TARGET_MODE.name,
        GRID_OUTAGE_TARGET_MODE_IS_CONFIGURED,
        DEFAULT_GRID_OUTAGE_TARGET_MODE.name,
    )

    if not ENABLE_AUTO_SWITCH:
        time_target_time_status += " (currently unused)"
        time_target_mode_status += " (currently unused)"

    if not ENABLE_GRID_OUTAGE_AUTO_SWITCH:
        outage_target_mode_status += " (currently unused)"

    return "\n".join(
        (
            "Startup configuration:",
            "  Serial port: "
            + _configuration_value_status(
                MUST_PORT,
                MUST_PORT_IS_CONFIGURED,
                DEFAULT_MUST_PORT,
            ),
            "  MySQL host: "
            + _configuration_value_status(
                MYSQL_HOST,
                MYSQL_HOST_IS_CONFIGURED,
                DEFAULT_MYSQL_HOST,
            ),
            "  MySQL database: "
            + _configuration_value_status(
                MYSQL_DATABASE,
                MYSQL_DATABASE_IS_CONFIGURED,
                DEFAULT_MYSQL_DATABASE,
            ),
            "  MySQL user: "
            + _configuration_value_status(
                MYSQL_USER,
                MYSQL_USER_IS_CONFIGURED,
                DEFAULT_MYSQL_USER,
            ),
            f"  MySQL password: {password_status}",
            "  Data gathering interval: "
            + _configuration_value_status(
                str(DATA_GATHER_INTERVAL_SECONDS),
                DATA_GATHER_INTERVAL_SECONDS_IS_CONFIGURED,
                str(DEFAULT_DATA_GATHER_INTERVAL_SECONDS),
            )
            + " seconds",
            f"  Time-based auto-switch: {auto_switch_status}",
            f"  Time-based target time: {time_target_time_status}",
            f"  Time-based target mode: {time_target_mode_status}",
            f"  Grid outage auto-switch: {outage_switch_status}",
            f"  Grid outage target mode: {outage_target_mode_status}",
            "  Log level: "
            + _configuration_value_status(
                logging.getLevelName(LOG_LEVEL),
                LOG_LEVEL_IS_CONFIGURED,
                DEFAULT_LOG_LEVEL,
            ),
        )
    )


def _warn_if_default_env_missing(
    variable_name: str,
    configured: bool,
    default: str,
) -> None:
    if configured:
        return

    LOGGER.warning(
        "%s is not configured; using %s default.",
        variable_name,
        default,
    )


_CONFIGURATION_WARNINGS_LOGGED = False


def log_configuration_warnings() -> None:
    """Log missing defaults and currently unused settings once."""
    global _CONFIGURATION_WARNINGS_LOGGED

    if _CONFIGURATION_WARNINGS_LOGGED:
        return

    default_settings = (
        ("MUST_PORT", MUST_PORT_IS_CONFIGURED, DEFAULT_MUST_PORT),
        ("MYSQL_HOST", MYSQL_HOST_IS_CONFIGURED, DEFAULT_MYSQL_HOST),
        (
            "MYSQL_DATABASE",
            MYSQL_DATABASE_IS_CONFIGURED,
            DEFAULT_MYSQL_DATABASE,
        ),
        ("MYSQL_USER", MYSQL_USER_IS_CONFIGURED, DEFAULT_MYSQL_USER),
        (
            "MYSQL_PASSWORD",
            MYSQL_PASSWORD_IS_CONFIGURED,
            "<empty>",
        ),
        (
            "DATA_GATHER_INTERVAL_SECONDS",
            DATA_GATHER_INTERVAL_SECONDS_IS_CONFIGURED,
            str(DEFAULT_DATA_GATHER_INTERVAL_SECONDS),
        ),
        (
            "ENABLE_AUTO_SWITCH",
            ENABLE_AUTO_SWITCH_IS_CONFIGURED,
            str(DEFAULT_ENABLE_AUTO_SWITCH),
        ),
        (
            "AUTO_SWITCH_TARGET_TIME",
            AUTO_SWITCH_TARGET_TIME_IS_CONFIGURED,
            DEFAULT_AUTO_SWITCH_TARGET_TIME,
        ),
        (
            "AUTO_SWITCH_TARGET_MODE",
            AUTO_SWITCH_TARGET_MODE_IS_CONFIGURED,
            DEFAULT_AUTO_SWITCH_TARGET_MODE.name,
        ),
        (
            "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
            ENABLE_GRID_OUTAGE_AUTO_SWITCH_IS_CONFIGURED,
            str(DEFAULT_ENABLE_GRID_OUTAGE_AUTO_SWITCH),
        ),
        (
            "GRID_OUTAGE_TARGET_MODE",
            GRID_OUTAGE_TARGET_MODE_IS_CONFIGURED,
            DEFAULT_GRID_OUTAGE_TARGET_MODE.name,
        ),
        ("LOG_LEVEL", LOG_LEVEL_IS_CONFIGURED, DEFAULT_LOG_LEVEL),
    )

    for variable_name, configured, default in default_settings:
        _warn_if_default_env_missing(variable_name, configured, default)

    if not ENABLE_AUTO_SWITCH:
        for variable_name, configured in (
            ("AUTO_SWITCH_TARGET_TIME", AUTO_SWITCH_TARGET_TIME_IS_CONFIGURED),
            ("AUTO_SWITCH_TARGET_MODE", AUTO_SWITCH_TARGET_MODE_IS_CONFIGURED),
        ):
            if configured:
                LOGGER.warning(
                    "%s is configured while ENABLE_AUTO_SWITCH is disabled; "
                    "the setting is currently unused.",
                    variable_name,
                )

    if (
        not ENABLE_GRID_OUTAGE_AUTO_SWITCH
        and GRID_OUTAGE_TARGET_MODE_IS_CONFIGURED
    ):
        LOGGER.warning(
            "GRID_OUTAGE_TARGET_MODE is configured while "
            "ENABLE_GRID_OUTAGE_AUTO_SWITCH is disabled; the setting is "
            "currently unused."
        )

    _CONFIGURATION_WARNINGS_LOGGED = True


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
