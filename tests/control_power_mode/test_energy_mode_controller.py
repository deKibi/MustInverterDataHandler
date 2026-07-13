# tests/control_power_mode/test_energy_mode_controller.py

# Standard Libraries
from unittest.mock import Mock

# Third-party Libraries
import pytest

# Custom Modules
from config import EnergyMode
from energy_mode_control import energy_mode_controller as controller


@pytest.fixture(autouse=True)
def clear_command_cooldowns():
    controller._last_command_timestamps.clear()
    yield
    controller._last_command_timestamps.clear()


@pytest.fixture
def must_data():
    return {
        "EnergyUseMode": EnergyMode.SUB.value,
        "GridVoltage": 230.0,
    }


def configure_rules(
    monkeypatch,
    control=True,
    grid_outage=False,
    scheduled=False,
    solar=False,
):
    monkeypatch.setattr(controller, "ENABLE_INVERTER_CONTROL", control)
    monkeypatch.setattr(
        controller,
        "GRID_AVAILABLE_VOLTAGE_THRESHOLD",
        200.0,
    )
    monkeypatch.setattr(
        controller,
        "GRID_OUTAGE_VOLTAGE_THRESHOLD",
        10.0,
    )
    monkeypatch.setattr(
        controller,
        "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
        grid_outage,
    )
    monkeypatch.setattr(controller, "ENABLE_AUTO_SWITCH", scheduled)
    monkeypatch.setattr(controller, "ENABLE_SOLAR_AUTO_SWITCH", solar)


def test_master_switch_blocks_all_control_rules(monkeypatch, must_data):
    configure_rules(
        monkeypatch,
        control=False,
        grid_outage=True,
        scheduled=True,
        solar=True,
    )
    must_data["GridVoltage"] = 0.0
    switch_mock = Mock()
    solar_mock = Mock(return_value=True)
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)
    monkeypatch.setattr(
        controller,
        "should_switch_to_solar_priority",
        solar_mock,
    )

    result = controller.handle_energy_mode_control(must_data, [])

    assert result is False
    switch_mock.assert_not_called()
    solar_mock.assert_not_called()


def test_returns_false_when_all_rules_are_disabled(monkeypatch, must_data):
    configure_rules(monkeypatch)
    switch_mock = Mock()
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data)

    assert result is False
    switch_mock.assert_not_called()


@pytest.mark.parametrize("invalid_data", [None, [], "invalid", 123])
def test_rejects_invalid_telemetry(monkeypatch, invalid_data):
    configure_rules(monkeypatch, solar=True)
    switch_mock = Mock()
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(invalid_data)

    assert result is False
    switch_mock.assert_not_called()


@pytest.mark.parametrize(
    "incomplete_data",
    [
        {"GridVoltage": 230.0},
        {"EnergyUseMode": EnergyMode.SUB.value},
    ],
)
def test_rejects_missing_required_telemetry(monkeypatch, incomplete_data):
    configure_rules(monkeypatch, solar=True)
    switch_mock = Mock()
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(incomplete_data)

    assert result is False
    switch_mock.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("EnergyUseMode", "unsupported"),
        ("EnergyUseMode", 99),
        ("GridVoltage", "unknown"),
    ],
)
def test_rejects_invalid_mode_or_grid_voltage(
    monkeypatch,
    must_data,
    field,
    value,
):
    configure_rules(monkeypatch, solar=True)
    must_data[field] = value
    switch_mock = Mock()
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data)

    assert result is False
    switch_mock.assert_not_called()


def test_grid_outage_rule_has_highest_priority(monkeypatch, must_data):
    configure_rules(monkeypatch, grid_outage=True, scheduled=True, solar=True)
    must_data["GridVoltage"] = 0.0
    switch_mock = Mock()
    solar_mock = Mock(return_value=True)
    monkeypatch.setattr(controller, "GRID_OUTAGE_TARGET_MODE", EnergyMode.UTI)
    monkeypatch.setattr(controller, "is_time_reached", Mock(return_value=True))
    monkeypatch.setattr(controller, "should_switch_to_solar_priority", solar_mock)
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data, solar_history=[])

    assert result is True
    switch_mock.assert_called_once_with(target_mode=EnergyMode.UTI)
    solar_mock.assert_not_called()


def test_grid_voltage_below_outage_boundary_triggers_outage_rule(
    monkeypatch,
    must_data,
):
    configure_rules(monkeypatch, grid_outage=True)
    must_data["GridVoltage"] = 9.99
    switch_mock = Mock()
    monkeypatch.setattr(controller, "GRID_OUTAGE_TARGET_MODE", EnergyMode.UTI)
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data)

    assert result is True
    switch_mock.assert_called_once_with(target_mode=EnergyMode.UTI)


@pytest.mark.parametrize("grid_voltage", [10.0, 11.0, 190.0, 199.99])
def test_uncertain_grid_voltage_blocks_all_control_rules(
    monkeypatch,
    must_data,
    grid_voltage,
):
    configure_rules(
        monkeypatch,
        grid_outage=True,
        scheduled=True,
        solar=True,
    )
    must_data["GridVoltage"] = grid_voltage
    time_reached_mock = Mock(return_value=True)
    solar_mock = Mock(return_value=True)
    switch_mock = Mock()
    monkeypatch.setattr(controller, "is_time_reached", time_reached_mock)
    monkeypatch.setattr(
        controller,
        "should_switch_to_solar_priority",
        solar_mock,
    )
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data, [])

    assert result is False
    time_reached_mock.assert_not_called()
    solar_mock.assert_not_called()
    switch_mock.assert_not_called()


def test_available_grid_boundary_allows_scheduled_rule(
    monkeypatch,
    must_data,
):
    configure_rules(monkeypatch, scheduled=True)
    must_data["GridVoltage"] = 200.0
    switch_mock = Mock()
    monkeypatch.setattr(controller, "AUTO_SWITCH_TARGET_MODE", EnergyMode.UTI)
    monkeypatch.setattr(controller, "is_time_reached", Mock(return_value=True))
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data)

    assert result is True
    switch_mock.assert_called_once_with(target_mode=EnergyMode.UTI)


def test_available_grid_boundary_allows_solar_evaluation(
    monkeypatch,
    must_data,
):
    configure_rules(monkeypatch, solar=True)
    must_data["GridVoltage"] = 200.0
    solar_mock = Mock(return_value=False)
    monkeypatch.setattr(
        controller,
        "should_switch_to_solar_priority",
        solar_mock,
    )

    result = controller.handle_energy_mode_control(must_data, [])

    assert result is False
    solar_mock.assert_called_once_with([])


def test_scheduled_rule_has_priority_over_solar(monkeypatch, must_data):
    configure_rules(monkeypatch, scheduled=True, solar=True)
    switch_mock = Mock()
    solar_mock = Mock(return_value=True)
    monkeypatch.setattr(controller, "AUTO_SWITCH_TARGET_MODE", EnergyMode.UTI)
    monkeypatch.setattr(controller, "is_time_reached", Mock(return_value=True))
    monkeypatch.setattr(controller, "is_time_in_window", Mock(return_value=False))
    monkeypatch.setattr(controller, "should_switch_to_solar_priority", solar_mock)
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data, solar_history=[])

    assert result is True
    switch_mock.assert_called_once_with(target_mode=EnergyMode.UTI)
    solar_mock.assert_not_called()


def test_scheduled_switch_is_blocked_inside_solar_window(
    monkeypatch,
    must_data,
):
    configure_rules(monkeypatch, scheduled=True, solar=True)
    switch_mock = Mock()
    solar_mock = Mock(return_value=False)
    monkeypatch.setattr(controller, "AUTO_SWITCH_TARGET_MODE", EnergyMode.UTI)
    monkeypatch.setattr(controller, "is_time_reached", Mock(return_value=True))
    monkeypatch.setattr(controller, "is_time_in_window", Mock(return_value=True))
    monkeypatch.setattr(controller, "should_switch_to_solar_priority", solar_mock)
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data, solar_history=[])

    assert result is False
    solar_mock.assert_called_once_with([])
    switch_mock.assert_not_called()


def test_scheduled_switch_is_allowed_at_solar_window_end(
    monkeypatch,
    must_data,
):
    configure_rules(monkeypatch, scheduled=True, solar=True)
    switch_mock = Mock()
    monkeypatch.setattr(controller, "AUTO_SWITCH_TARGET_MODE", EnergyMode.UTI)
    monkeypatch.setattr(controller, "is_time_reached", Mock(return_value=True))
    monkeypatch.setattr(controller, "is_time_in_window", Mock(return_value=False))
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data)

    assert result is True
    switch_mock.assert_called_once_with(target_mode=EnergyMode.UTI)


def test_scheduled_switch_is_unchanged_when_solar_is_disabled(
    monkeypatch,
    must_data,
):
    configure_rules(monkeypatch, scheduled=True, solar=False)
    switch_mock = Mock()
    window_mock = Mock(return_value=True)
    monkeypatch.setattr(controller, "AUTO_SWITCH_TARGET_MODE", EnergyMode.UTI)
    monkeypatch.setattr(controller, "is_time_reached", Mock(return_value=True))
    monkeypatch.setattr(controller, "is_time_in_window", window_mock)
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data)

    assert result is True
    window_mock.assert_not_called()
    switch_mock.assert_called_once_with(target_mode=EnergyMode.UTI)


def test_solar_rule_switches_only_from_sub(monkeypatch, must_data):
    configure_rules(monkeypatch, solar=True)
    switch_mock = Mock()
    monkeypatch.setattr(controller, "SOLAR_AUTO_SWITCH_TARGET_MODE", EnergyMode.SBU)
    monkeypatch.setattr(
        controller,
        "should_switch_to_solar_priority",
        Mock(return_value=True),
    )
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data, solar_history=[])

    assert result is True
    switch_mock.assert_called_once_with(target_mode=EnergyMode.SBU)


def test_solar_rule_ignores_other_source_modes(monkeypatch, must_data):
    configure_rules(monkeypatch, solar=True)
    must_data["EnergyUseMode"] = EnergyMode.UTI.value
    solar_mock = Mock(return_value=True)
    switch_mock = Mock()
    monkeypatch.setattr(controller, "should_switch_to_solar_priority", solar_mock)
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data, solar_history=[])

    assert result is False
    solar_mock.assert_not_called()
    switch_mock.assert_not_called()


def test_does_not_send_command_when_target_mode_is_current(monkeypatch, must_data):
    configure_rules(monkeypatch, scheduled=True)
    monkeypatch.setattr(controller, "AUTO_SWITCH_TARGET_MODE", EnergyMode.SUB)
    monkeypatch.setattr(controller, "is_time_reached", Mock(return_value=True))
    switch_mock = Mock()
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data)

    assert result is False
    switch_mock.assert_not_called()


def test_repeated_solar_command_is_blocked_as_spam(monkeypatch, must_data):
    configure_rules(monkeypatch, solar=True)
    switch_mock = Mock()
    monotonic_mock = Mock(side_effect=[1000.0, 1000.0, 1100.0])
    monkeypatch.setattr(controller.time, "monotonic", monotonic_mock)
    monkeypatch.setattr(
        controller,
        "should_switch_to_solar_priority",
        Mock(return_value=True),
    )
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    first_result = controller.handle_energy_mode_control(must_data, [])
    second_result = controller.handle_energy_mode_control(must_data, [])

    assert first_result is True
    assert second_result is False
    switch_mock.assert_called_once_with(target_mode=EnergyMode.SBU)


def test_solar_command_is_allowed_after_cooldown(monkeypatch, must_data):
    configure_rules(monkeypatch, solar=True)
    cooldown_key = (controller.SOLAR_SWITCH_RULE, EnergyMode.SBU)
    controller._last_command_timestamps[cooldown_key] = 1000.0
    switch_mock = Mock()
    monkeypatch.setattr(
        controller.time,
        "monotonic",
        Mock(side_effect=[1300.0, 1300.0]),
    )
    monkeypatch.setattr(
        controller,
        "should_switch_to_solar_priority",
        Mock(return_value=True),
    )
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data, [])

    assert result is True
    switch_mock.assert_called_once_with(target_mode=EnergyMode.SBU)


def test_emergency_bypasses_solar_cooldown_for_same_target(
    monkeypatch,
    must_data,
):
    configure_rules(monkeypatch, grid_outage=True, solar=True)
    must_data["GridVoltage"] = 0.0
    solar_key = (controller.SOLAR_SWITCH_RULE, EnergyMode.SBU)
    controller._last_command_timestamps[solar_key] = 1000.0
    switch_mock = Mock()
    monkeypatch.setattr(controller, "GRID_OUTAGE_TARGET_MODE", EnergyMode.SBU)
    monkeypatch.setattr(
        controller.time,
        "monotonic",
        Mock(side_effect=[1100.0, 1100.0]),
    )
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data, [])

    assert result is True
    switch_mock.assert_called_once_with(target_mode=EnergyMode.SBU)


def test_repeated_emergency_command_is_blocked_as_spam(monkeypatch, must_data):
    configure_rules(monkeypatch, grid_outage=True)
    must_data["GridVoltage"] = 0.0
    emergency_key = (controller.GRID_OUTAGE_SWITCH_RULE, EnergyMode.SBU)
    controller._last_command_timestamps[emergency_key] = 1000.0
    switch_mock = Mock()
    monkeypatch.setattr(controller, "GRID_OUTAGE_TARGET_MODE", EnergyMode.SBU)
    monkeypatch.setattr(controller.time, "monotonic", Mock(return_value=1100.0))
    monkeypatch.setattr(controller, "switch_energy_mode", switch_mock)

    result = controller.handle_energy_mode_control(must_data)

    assert result is False
    switch_mock.assert_not_called()


def test_failed_command_does_not_start_cooldown(monkeypatch, must_data):
    configure_rules(monkeypatch, solar=True)
    monkeypatch.setattr(
        controller,
        "should_switch_to_solar_priority",
        Mock(return_value=True),
    )
    monkeypatch.setattr(
        controller,
        "switch_energy_mode",
        Mock(side_effect=OSError("serial failure")),
    )

    result = controller.handle_energy_mode_control(must_data, [])

    cooldown_key = (controller.SOLAR_SWITCH_RULE, EnergyMode.SBU)
    assert result is False
    assert cooldown_key not in controller._last_command_timestamps


def test_guarded_command_does_not_start_cooldown(monkeypatch, must_data):
    configure_rules(monkeypatch, solar=True)
    monkeypatch.setattr(
        controller,
        "should_switch_to_solar_priority",
        Mock(return_value=True),
    )
    monkeypatch.setattr(
        controller,
        "switch_energy_mode",
        Mock(return_value=False),
    )

    result = controller.handle_energy_mode_control(must_data, [])

    cooldown_key = (controller.SOLAR_SWITCH_RULE, EnergyMode.SBU)
    assert result is False
    assert cooldown_key not in controller._last_command_timestamps
