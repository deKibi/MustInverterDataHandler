# tests/config/test_logging_config.py

# Standard Libraries
import json
import logging
from logging.handlers import TimedRotatingFileHandler

# Third-party Libraries
import pytest

# Custom Modules
import config
import logging_config


@pytest.fixture
def isolated_logging(monkeypatch, tmp_path):
    root_logger = logging.getLogger()
    data_logger = logging.getLogger(
        logging_config.INVERTER_DATA_LOGGER_NAME
    )
    config_logger = logging.getLogger(logging_config.CONFIG_LOGGER_NAME)
    mysql_connector_logger = logging.getLogger(
        logging_config.MYSQL_CONNECTOR_LOGGER_NAME
    )
    module_logger = logging.getLogger(logging_config.__name__)
    original_root_handlers = list(root_logger.handlers)
    original_data_handlers = list(data_logger.handlers)
    original_root_level = root_logger.level
    original_data_level = data_logger.level
    original_data_propagate = data_logger.propagate
    original_config_level = config_logger.level
    original_mysql_connector_level = mysql_connector_logger.level
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
    config_logger.setLevel(original_config_level)
    mysql_connector_logger.setLevel(original_mysql_connector_level)
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


def test_mysql_connector_logs_only_warnings_and_errors(
    isolated_logging,
    capsys,
):
    logging_config.configure_logging()
    mysql_plugin_logger = logging.getLogger(
        "mysql.connector.plugins"
    )

    mysql_plugin_logger.debug("MySQL connector debug message.")
    mysql_plugin_logger.info("MySQL connector info message.")
    mysql_plugin_logger.warning("MySQL connector warning message.")

    for handler in logging.getLogger().handlers:
        handler.flush()

    console_output = capsys.readouterr().err
    general_log = logging_config.GENERAL_LOG_PATH.read_text(
        encoding="utf-8"
    )

    assert "MySQL connector debug message." not in console_output
    assert "MySQL connector info message." not in console_output
    assert "MySQL connector warning message." in console_output
    assert "MySQL connector debug message." not in general_log
    assert "MySQL connector info message." not in general_log
    assert "MySQL connector warning message." in general_log


def test_defaulted_master_switch_details_are_logged_to_console_only(
    isolated_logging,
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(config, "ENABLE_INVERTER_CONTROL", False)
    monkeypatch.setattr(
        config,
        "_defaulted_variables",
        {"ENABLE_INVERTER_CONTROL"},
    )
    monkeypatch.setattr(config, "_configuration_warnings", [])
    monkeypatch.setattr(config, "_startup_configuration_logged", False)
    for variable_name in config._INVERTER_CONTROL_SETTING_VARIABLES:
        monkeypatch.delenv(variable_name, raising=False)

    logging_config.configure_logging()
    config.log_startup_configuration()

    for handler in logging.getLogger().handlers:
        handler.flush()

    console_output = capsys.readouterr().err
    general_log = logging_config.GENERAL_LOG_PATH.read_text(
        encoding="utf-8"
    )
    default_message = (
        "ENABLE_INVERTER_CONTROL is not configured; using false default."
    )

    assert "Inverter control: disabled" in console_output
    assert "Inverter control: disabled" in general_log
    assert default_message in console_output
    assert default_message not in general_log


def test_disabled_inverter_control_status_is_logged_to_console_only(
    isolated_logging,
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(logging_config, "ENABLE_INVERTER_CONTROL", False)

    logging_config.configure_logging()
    logging_config.logger.info("Test general log entry.")
    logging_config.log_inverter_control_status()

    for handler in logging.getLogger().handlers:
        handler.flush()

    console_output = capsys.readouterr().err
    general_log = logging_config.GENERAL_LOG_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "Inverter control status: disabled (read-only mode)."
        in console_output
    )
    assert "Scheduled auto-switch:" not in console_output
    assert "Grid outage auto-switch:" not in console_output
    assert "Solar auto-switch:" not in console_output
    assert "Inverter control status:" not in general_log


def test_enabled_inverter_control_rule_statuses_are_console_only(
    isolated_logging,
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(logging_config, "ENABLE_INVERTER_CONTROL", True)
    monkeypatch.setattr(logging_config, "ENABLE_AUTO_SWITCH", True)
    monkeypatch.setattr(
        logging_config,
        "AUTO_SWITCH_TARGET_MODE",
        logging_config.EnergyMode.SUB,
    )
    monkeypatch.setattr(
        logging_config,
        "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
        False,
    )
    monkeypatch.setattr(logging_config, "ENABLE_SOLAR_AUTO_SWITCH", True)
    monkeypatch.setattr(
        logging_config,
        "SOLAR_AUTO_SWITCH_TARGET_MODE",
        logging_config.EnergyMode.SBU,
    )

    logging_config.configure_logging()
    logging_config.logger.info("Test general log entry.")
    logging_config.log_inverter_control_status()

    for handler in logging.getLogger().handlers:
        handler.flush()

    console_output = capsys.readouterr().err
    general_log = logging_config.GENERAL_LOG_PATH.read_text(
        encoding="utf-8"
    )

    assert "Inverter control status: enabled." in console_output
    assert (
        "Scheduled auto-switch: enabled; target mode: SUB."
        in console_output
    )
    assert "Grid outage auto-switch: disabled." in console_output
    assert (
        "Solar auto-switch: enabled; target mode: SBU."
        in console_output
    )
    assert "Inverter control status:" not in general_log
    assert "Scheduled auto-switch:" not in general_log
    assert "Grid outage auto-switch:" not in general_log
    assert "Solar auto-switch:" not in general_log
