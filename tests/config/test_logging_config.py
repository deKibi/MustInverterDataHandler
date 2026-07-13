# tests/config/test_logging_config.py

# Standard Libraries
import json
import logging
from logging.handlers import TimedRotatingFileHandler

# Third-party Libraries
import pytest

# Custom Modules
import logging_config


@pytest.fixture
def isolated_logging(monkeypatch, tmp_path):
    root_logger = logging.getLogger()
    data_logger = logging.getLogger(
        logging_config.INVERTER_DATA_LOGGER_NAME
    )
    module_logger = logging.getLogger(logging_config.__name__)
    original_root_handlers = list(root_logger.handlers)
    original_data_handlers = list(data_logger.handlers)
    original_root_level = root_logger.level
    original_data_level = data_logger.level
    original_data_propagate = data_logger.propagate
    original_module_level = module_logger.level

    root_logger.handlers.clear()
    data_logger.handlers.clear()
    monkeypatch.setattr(logging_config, "LOG_DIRECTORY", tmp_path)
    monkeypatch.setattr(
        logging_config,
        "GENERAL_LOG_PATH",
        tmp_path / "app.log",
    )
    monkeypatch.setattr(
        logging_config,
        "INVERTER_DATA_LOG_PATH",
        tmp_path / "inverter_data.jsonl",
    )
    monkeypatch.setattr(logging_config, "_LOGGING_CONFIGURED", False)

    yield

    for handler in root_logger.handlers + data_logger.handlers:
        handler.close()

    root_logger.handlers[:] = original_root_handlers
    root_logger.setLevel(original_root_level)
    data_logger.handlers[:] = original_data_handlers
    data_logger.setLevel(original_data_level)
    data_logger.propagate = original_data_propagate
    module_logger.setLevel(original_module_level)


def test_general_log_uses_app_filename():
    assert logging_config.GENERAL_LOG_PATH.name == "app.log"


def test_full_inverter_data_is_logged_to_console_only(
    isolated_logging,
    capsys,
):
    inverter_data = {
        "EnergyUseMode": 1,
        "GridVoltage": "227.20",
        "BatteryVoltage": "27.00",
        "PvVoltage": "43.40",
        "ChargerPower": 118,
        "PLoad": 68,
    }

    logging_config.configure_logging()
    logging_config.log_inverter_data(inverter_data)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.flush()

    console_output = capsys.readouterr().err
    general_log = logging_config.GENERAL_LOG_PATH.read_text(
        encoding="utf-8"
    )
    inverter_data_log = logging_config.INVERTER_DATA_LOG_PATH.read_text(
        encoding="utf-8"
    )

    assert "Inverter's data received:" in console_output
    assert str(inverter_data) in console_output
    assert "Inverter's data received:" not in general_log
    assert "Inverter telemetry received:" in general_log
    assert json.loads(inverter_data_log)["data"] == inverter_data


def test_console_and_general_file_use_separate_log_levels(
    isolated_logging,
):
    logging_config.configure_logging()

    root_handlers = logging.getLogger().handlers
    console_handler = next(
        handler
        for handler in root_handlers
        if type(handler) is logging.StreamHandler
    )
    general_file_handler = next(
        handler
        for handler in root_handlers
        if isinstance(handler, TimedRotatingFileHandler)
    )

    assert console_handler.level == logging.DEBUG
    assert general_file_handler.level == logging.INFO
    assert logging.getLogger().level == logging.INFO
    assert logging.getLogger(logging_config.__name__).level == logging.DEBUG
