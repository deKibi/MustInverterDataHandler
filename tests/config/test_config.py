# tests/config/test_config.py

# Standard Libraries
import logging
from datetime import time
from unittest.mock import Mock

# Third-party Libraries
import pytest

# Custom Modules
import config
import main as application


REQUIRED_MYSQL_VALUES = {
    "MYSQL_HOST": "fake-db-host",
    "MYSQL_DATABASE": "fake-db-name",
    "MYSQL_USER": "fake-db-user",
    "MYSQL_PASSWORD": "fake-secret-password",
}


@pytest.fixture(autouse=True)
def isolated_config_state(monkeypatch):
    original_warnings = list(config._configuration_warnings)
    original_defaults = set(config._defaulted_variables)
    original_logged_state = config._startup_configuration_logged

    config._configuration_warnings.clear()
    config._defaulted_variables.clear()
    config._startup_configuration_logged = False

    for variable_name, value in REQUIRED_MYSQL_VALUES.items():
        monkeypatch.setattr(config, variable_name, value)

    yield

    config._configuration_warnings[:] = original_warnings
    config._defaulted_variables.clear()
    config._defaulted_variables.update(original_defaults)
    config._startup_configuration_logged = original_logged_state


def test_valid_required_mysql_configuration_passes():
    config.validate_configuration()


@pytest.mark.parametrize(
    "variable_name,missing_value",
    [
        (variable_name, missing_value)
        for variable_name in REQUIRED_MYSQL_VALUES
        for missing_value in (None, "", "   ")
    ],
)
def test_rejects_missing_required_mysql_value(
    monkeypatch,
    variable_name,
    missing_value,
):
    monkeypatch.setattr(config, variable_name, missing_value)

    with pytest.raises(config.ConfigurationError) as error_info:
        config.validate_configuration()

    assert variable_name in str(error_info.value)
    assert "fake-secret-password" not in str(error_info.value)


def test_reports_all_missing_required_mysql_values(monkeypatch):
    for variable_name in REQUIRED_MYSQL_VALUES:
        monkeypatch.setattr(config, variable_name, None)

    with pytest.raises(config.ConfigurationError) as error_info:
        config.validate_configuration()

    error_message = str(error_info.value)
    for variable_name in REQUIRED_MYSQL_VALUES:
        assert variable_name in error_message


def test_main_stops_before_hardware_when_configuration_is_invalid(
    monkeypatch,
):
    inverter_handler_mock = Mock()
    monkeypatch.setattr(application, "configure_logging", Mock())
    monkeypatch.setattr(
        application,
        "validate_configuration",
        Mock(side_effect=config.ConfigurationError("MYSQL_HOST is missing")),
    )
    monkeypatch.setattr(
        application,
        "MustInverterDataHandler",
        inverter_handler_mock,
    )

    with pytest.raises(SystemExit) as error_info:
        application.main()

    assert error_info.value.code == 1
    inverter_handler_mock.assert_not_called()


@pytest.mark.parametrize("raw_value", [None, "", "invalid", "0", "65536"])
def test_mysql_port_uses_3306_default_for_missing_or_invalid_value(
    monkeypatch,
    raw_value,
):
    variable_name = "TEST_MYSQL_PORT"

    if raw_value is None:
        monkeypatch.delenv(variable_name, raising=False)
    else:
        monkeypatch.setenv(variable_name, raw_value)

    result = config.get_env_port(variable_name, default=3306)

    assert result == 3306
    assert any(
        variable_name in warning
        and "3306" in warning
        for warning in config._configuration_warnings
    )


def test_mysql_port_accepts_explicit_valid_value(monkeypatch):
    monkeypatch.setenv("TEST_MYSQL_PORT", "3307")

    result = config.get_env_port("TEST_MYSQL_PORT", default=3306)

    assert result == 3307
    assert config._configuration_warnings == []


@pytest.mark.parametrize(
    "getter_name,getter_kwargs,expected",
    [
        ("get_env_string", {"default": "COM3"}, "COM3"),
        ("get_env_bool", {"default": False}, False),
        ("get_env_int", {"default": 60}, 60),
        ("get_env_float", {"default": 26.8}, 26.8),
        ("get_env_time", {"default": "12:00"}, time(12, 0)),
        (
            "get_env_energy_mode",
            {"default": config.EnergyMode.SBU},
            config.EnergyMode.SBU,
        ),
    ],
)
@pytest.mark.parametrize("missing_value", [None, ""])
def test_optional_missing_value_uses_default_and_records_warning(
    monkeypatch,
    getter_name,
    getter_kwargs,
    expected,
    missing_value,
):
    variable_name = f"TEST_{getter_name.upper()}"
    if missing_value is None:
        monkeypatch.delenv(variable_name, raising=False)
    else:
        monkeypatch.setenv(variable_name, missing_value)
    getter = getattr(config, getter_name)

    result = getter(variable_name=variable_name, **getter_kwargs)

    assert result == expected
    assert variable_name in config._defaulted_variables
    assert any(
        variable_name in warning
        for warning in config._configuration_warnings
    )


def test_startup_summary_is_safe_complete_and_logged_once(caplog):
    config._record_default("MYSQL_PORT", 3306)

    with caplog.at_level(logging.INFO, logger="config"):
        config.validate_configuration()
        config.log_startup_configuration()
        config.log_startup_configuration()

    log_text = caplog.text
    assert log_text.count("Configuration loaded and validated.") == 1
    assert log_text.count("Startup configuration:") == 1
    assert "MySQL host: configured" in log_text
    assert "MySQL password: configured" in log_text
    assert "MySQL port: not configured (using 3306 default)" in log_text
    assert "Scheduled auto-switch:" in log_text
    assert "Grid outage auto-switch:" in log_text
    assert "Solar auto-switch:" in log_text
    assert "Solar average thresholds:" in log_text
    assert "fake-secret-password" not in log_text
    assert "fake-db-host" not in log_text


def test_deferred_default_warning_is_logged_once(caplog):
    config._record_default("TEST_OPTION", "value")

    with caplog.at_level(logging.INFO, logger="config"):
        config.log_startup_configuration()
        config.log_startup_configuration()

    assert caplog.text.count(
        "TEST_OPTION is not configured; using value default."
    ) == 1
