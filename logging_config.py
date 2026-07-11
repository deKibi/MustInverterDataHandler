# logging_config.py

# Standard Libraries
import json
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Final
from zoneinfo import ZoneInfo

# Custom Modules
from config import EnergyMode


# Logging
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent
LOG_DIRECTORY: Final[Path] = PROJECT_ROOT / "logs"
GENERAL_LOG_PATH: Final[Path] = LOG_DIRECTORY / "application.log"
INVERTER_DATA_LOG_PATH: Final[Path] = LOG_DIRECTORY / "inverter_data.jsonl"
GENERAL_LOG_RETENTION_DAYS: Final[int] = 30
INVERTER_DATA_LOG_RETENTION_DAYS: Final[int] = 14
INVERTER_DATA_LOGGER_NAME: Final[str] = "inverter_data"
KYIV_TIMEZONE: Final[ZoneInfo] = ZoneInfo("Europe/Kyiv")
_LOGGING_CONFIGURED = False


def configure_logging() -> None:
    """Configure console, general file, and inverter data logging."""
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

    general_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(general_formatter)

    general_file_handler = TimedRotatingFileHandler(
        filename=GENERAL_LOG_PATH,
        when="midnight",
        backupCount=GENERAL_LOG_RETENTION_DAYS,
        encoding="utf-8",
        delay=True,
    )
    general_file_handler.setFormatter(general_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(general_file_handler)

    inverter_data_handler = TimedRotatingFileHandler(
        filename=INVERTER_DATA_LOG_PATH,
        when="midnight",
        backupCount=INVERTER_DATA_LOG_RETENTION_DAYS,
        encoding="utf-8",
        delay=True,
    )
    inverter_data_handler.setFormatter(logging.Formatter("%(message)s"))

    inverter_data_logger = logging.getLogger(INVERTER_DATA_LOGGER_NAME)
    inverter_data_logger.setLevel(logging.INFO)
    inverter_data_logger.propagate = False
    inverter_data_logger.addHandler(inverter_data_handler)

    _LOGGING_CONFIGURED = True


def log_inverter_data(data: dict[str, object] | None) -> None:
    """Write full inverter data as JSONL and log a short summary."""
    record = {
        "timestamp": datetime.now(tz=KYIV_TIMEZONE).isoformat(),
        "data": data,
    }
    data_logger = logging.getLogger(INVERTER_DATA_LOGGER_NAME)
    data_logger.info(
        json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    )

    logging.getLogger(__name__).info(
        "Inverter telemetry received: mode=%s, grid=%s V, "
        "battery=%s V, PV=%s V / %s W, load=%s W.",
        _format_energy_mode(data),
        _format_telemetry_value(data, "GridVoltage", 1),
        _format_telemetry_value(data, "BatteryVoltage", 1),
        _format_telemetry_value(data, "PvVoltage", 1),
        _format_telemetry_value(data, "ChargerPower"),
        _format_telemetry_value(data, "PLoad"),
    )


def _format_energy_mode(data: dict[str, object] | None) -> str:
    if not isinstance(data, dict):
        return "unknown"

    try:
        return EnergyMode(int(data["EnergyUseMode"])).name
    except (KeyError, TypeError, ValueError):
        return "unknown"


def _format_telemetry_value(
    data: dict[str, object] | None,
    field_name: str,
    decimal_places: int | None = None,
) -> str:
    if not isinstance(data, dict):
        return "unknown"

    try:
        value = float(data[field_name])
    except (KeyError, TypeError, ValueError):
        return "unknown"

    if decimal_places is not None:
        return f"{value:.{decimal_places}f}"

    return f"{value:g}"
