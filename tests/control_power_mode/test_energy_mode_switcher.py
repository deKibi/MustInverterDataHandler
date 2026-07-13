# tests/control_power_mode/test_energy_mode_switcher.py

# Standard Libraries
import logging
from unittest.mock import MagicMock, Mock

# Custom Modules
from config import EnergyMode
from energy_mode_control import energy_mode_switcher as switcher


def test_master_switch_blocks_serial_command(monkeypatch, caplog):
    build_mock = Mock()
    serial_mock = Mock()
    monkeypatch.setattr(switcher, "ENABLE_INVERTER_CONTROL", False)
    monkeypatch.setattr(switcher, "build_energy_mode_command", build_mock)
    monkeypatch.setattr(switcher.serial, "Serial", serial_mock)

    with caplog.at_level(logging.WARNING, logger=switcher.__name__):
        result = switcher.switch_energy_mode(EnergyMode.SBU)

    assert result is False
    assert "Inverter control is disabled" in caplog.text
    build_mock.assert_not_called()
    serial_mock.assert_not_called()


def test_enabled_master_switch_preserves_raw_response(monkeypatch):
    frame = b"command"
    response = b"response"
    serial_connection = MagicMock()
    serial_connection.in_waiting = len(response)
    serial_connection.read.return_value = response
    serial_context = MagicMock()
    serial_context.__enter__.return_value = serial_connection
    serial_mock = Mock(return_value=serial_context)
    build_mock = Mock(return_value=frame)
    monkeypatch.setattr(switcher, "ENABLE_INVERTER_CONTROL", True)
    monkeypatch.setattr(switcher, "build_energy_mode_command", build_mock)
    monkeypatch.setattr(switcher.serial, "Serial", serial_mock)
    monkeypatch.setattr(switcher.time, "sleep", Mock())

    result = switcher.switch_energy_mode(
        target_mode=EnergyMode.SBU,
        port="test-port",
    )

    assert result == response
    build_mock.assert_called_once_with(EnergyMode.SBU)
    serial_mock.assert_called_once_with(
        port="test-port",
        baudrate=19200,
        timeout=1,
        write_timeout=1,
    )
    serial_connection.write.assert_called_once_with(frame)
    serial_connection.read.assert_called_once_with(len(response))
