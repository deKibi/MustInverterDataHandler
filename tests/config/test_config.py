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

OPTIONAL_FEATURE_ENABLE_VARIABLES = {
    "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
    "ENABLE_SOLAR_AUTO_SWITCH",
}

OPTIONAL_FEATURE_SETTING_VARIABLES = {
    *config._GRID_OUTAGE_SETTING_VARIABLES,
    *config._SOLAR_SETTING_VARIABLES,
}


@pytest.fixture(autouse=True)
def isolated_config_state(monkeypatch):
    original_warnings = list(config._configuration_warnings)
    original_defaults = set(config._defaulted_variables)
    original_logged_state = config._startup_configuration_logged

    config._configuration_warnings.clear()
    config._defaulted_variables.clear()
    config._defaulted_variables.update(OPTIONAL_FEATURE_ENABLE_VARIABLES)
    config._defaulted_variables.update(OPTIONAL_FEATURE_SETTING_VARIABLES)
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


@pytest.mark.parametrize(
    "variable_name",
    sorted(OPTIONAL_FEATURE_ENABLE_VARIABLES),
)
def test_missing_optional_feature_switch_does_not_record_warning(
    monkeypatch,
    variable_name,
):
    monkeypatch.delenv(variable_name, raising=False)
    config._defaulted_variables.discard(variable_name)

    result = config.get_env_bool(variable_name, default=False)

    assert result is False
    assert variable_name in config._defaulted_variables
    assert not any(
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
    assert "MySQL host:" not in log_text
    assert "MySQL database:" not in log_text
    assert "MySQL user:" not in log_text
    assert "MySQL password:" not in log_text
    assert "MySQL port: not configured (using 3306 default)" in log_text
    assert "Scheduled auto-switch:" in log_text
    assert "Grid outage auto-switch:" in log_text
    assert "Solar auto-switch:" in log_text
    assert "Solar average thresholds:" not in log_text
    assert "fake-secret-password" not in log_text
    assert "fake-db-host" not in log_text


def test_missing_optional_feature_switches_are_info_only(
    monkeypatch,
    caplog,
):
    monkeypatch.setattr(config, "ENABLE_GRID_OUTAGE_AUTO_SWITCH", False)
    monkeypatch.setattr(config, "ENABLE_SOLAR_AUTO_SWITCH", False)

    with caplog.at_level(logging.INFO, logger="config"):
        config.log_startup_configuration()

    assert (
        "Grid outage auto-switch: "
        "not configured (using false default)"
    ) in caplog.text
    assert (
        "Solar auto-switch: not configured (using false default)"
    ) in caplog.text
    assert not any(
        record.levelno == logging.WARNING
        and record.getMessage().startswith(
            tuple(OPTIONAL_FEATURE_ENABLE_VARIABLES)
        )
        for record in caplog.records
    )


def test_disabled_features_hide_defaulted_related_settings(
    monkeypatch,
    caplog,
):
    monkeypatch.setattr(config, "ENABLE_GRID_OUTAGE_AUTO_SWITCH", False)
    monkeypatch.setattr(config, "ENABLE_SOLAR_AUTO_SWITCH", False)

    for variable_name in OPTIONAL_FEATURE_SETTING_VARIABLES:
        config._record_default(variable_name, "test-default")

    with caplog.at_level(logging.INFO, logger="config"):
        config.log_startup_configuration()

    assert "GRID_OUTAGE_TARGET_MODE:" not in caplog.text
    assert "SOLAR_AUTO_SWITCH_START_TIME:" not in caplog.text
    assert "Solar history:" not in caplog.text
    assert "Solar average thresholds:" not in caplog.text
    assert "Solar latest limits:" not in caplog.text
    assert "(unused)" not in caplog.text
    assert not any(
        record.levelno == logging.WARNING
        and any(
            variable_name in record.getMessage()
            for variable_name in OPTIONAL_FEATURE_SETTING_VARIABLES
        )
        for record in caplog.records
    )


def test_disabled_features_report_explicit_settings_as_unused(
    monkeypatch,
    caplog,
):
    monkeypatch.setattr(config, "ENABLE_GRID_OUTAGE_AUTO_SWITCH", False)
    monkeypatch.setattr(config, "ENABLE_SOLAR_AUTO_SWITCH", False)
    explicit_settings = {
        "GRID_OUTAGE_TARGET_MODE",
        "SOLAR_AUTO_SWITCH_START_TIME",
        "SOLAR_AUTO_SWITCH_MAX_LOAD_POWER",
    }
    config._defaulted_variables.difference_update(explicit_settings)

    with caplog.at_level(logging.INFO, logger="config"):
        config.log_startup_configuration()

    assert "GRID_OUTAGE_TARGET_MODE: SUB (unused)" in caplog.text
    assert "SOLAR_AUTO_SWITCH_START_TIME: 12:00 (unused)" in caplog.text
    assert "SOLAR_AUTO_SWITCH_MAX_LOAD_POWER: 400.0 (unused)" in caplog.text
    assert "SOLAR_AUTO_SWITCH_END_TIME:" not in caplog.text

    unused_warnings = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.WARNING
        and "configured related settings are unused" in record.getMessage()
    ]
    assert len(unused_warnings) == 2
    assert "GRID_OUTAGE_TARGET_MODE" in unused_warnings[0]
    assert "SOLAR_AUTO_SWITCH_START_TIME" in unused_warnings[1]
    assert "SOLAR_AUTO_SWITCH_MAX_LOAD_POWER" in unused_warnings[1]
    assert "SOLAR_AUTO_SWITCH_END_TIME" not in unused_warnings[1]


def test_enabled_features_show_active_settings(monkeypatch, caplog):
    monkeypatch.setattr(config, "ENABLE_GRID_OUTAGE_AUTO_SWITCH", True)
    monkeypatch.setattr(config, "ENABLE_SOLAR_AUTO_SWITCH", True)

    with caplog.at_level(logging.INFO, logger="config"):
        config.log_startup_configuration()

    assert "Grid outage auto-switch:" in caplog.text
    assert "; target mode:" in caplog.text
    assert "Solar auto-switch:" in caplog.text
    assert "; window:" in caplog.text
    assert "Solar history:" in caplog.text
    assert "Solar average thresholds:" in caplog.text
    assert "Solar latest limits:" in caplog.text
    assert "(unused)" not in caplog.text


def test_deferred_default_warning_is_logged_once(caplog):
    config._record_default("TEST_OPTION", "value")

    with caplog.at_level(logging.INFO, logger="config"):
        config.log_startup_configuration()
        config.log_startup_configuration()

    assert caplog.text.count(
        "TEST_OPTION is not configured; using value default."
    ) == 1
