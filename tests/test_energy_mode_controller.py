# tests/test_energy_mode_controller.py

# Standard Libraries
import unittest
from unittest.mock import patch

# Custom Modules
from config import EnergyMode
from energy_mode_control import energy_mode_controller


class EnergyModeControllerTestCase(unittest.TestCase):
    def setUp(self):
        energy_mode_controller._last_command_timestamps.clear()
        self.must_data = {
            "EnergyUseMode": EnergyMode.SUB.value,
            "GridVoltage": 230.0,
        }

    def tearDown(self):
        energy_mode_controller._last_command_timestamps.clear()

    def test_grid_outage_rule_has_priority(self):
        self.must_data["GridVoltage"] = 0.0

        with (
            patch.object(
                energy_mode_controller,
                "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
                True,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_AUTO_SWITCH",
                True,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_SOLAR_AUTO_SWITCH",
                True,
            ),
            patch.object(
                energy_mode_controller,
                "GRID_OUTAGE_TARGET_MODE",
                EnergyMode.UTI,
            ),
            patch.object(
                energy_mode_controller,
                "is_time_reached",
                return_value=True,
            ),
            patch.object(
                energy_mode_controller,
                "should_switch_to_solar_priority",
                return_value=True,
            ),
            patch.object(
                energy_mode_controller,
                "switch_energy_mode",
            ) as switch_mock,
        ):
            result = energy_mode_controller.handle_energy_mode_control(
                self.must_data,
                solar_history=[],
            )

        self.assertTrue(result)
        switch_mock.assert_called_once_with(target_mode=EnergyMode.UTI)

    def test_solar_rule_switches_only_from_sub(self):
        with (
            patch.object(
                energy_mode_controller,
                "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
                False,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_AUTO_SWITCH",
                False,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_SOLAR_AUTO_SWITCH",
                True,
            ),
            patch.object(
                energy_mode_controller,
                "SOLAR_AUTO_SWITCH_TARGET_MODE",
                EnergyMode.SBU,
            ),
            patch.object(
                energy_mode_controller,
                "should_switch_to_solar_priority",
                return_value=True,
            ),
            patch.object(
                energy_mode_controller,
                "switch_energy_mode",
            ) as switch_mock,
        ):
            result = energy_mode_controller.handle_energy_mode_control(
                self.must_data,
                solar_history=[],
            )

        self.assertTrue(result)
        switch_mock.assert_called_once_with(target_mode=EnergyMode.SBU)

    def test_scheduled_rule_has_priority_over_solar_rule(self):
        with (
            patch.object(
                energy_mode_controller,
                "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
                False,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_AUTO_SWITCH",
                True,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_SOLAR_AUTO_SWITCH",
                True,
            ),
            patch.object(
                energy_mode_controller,
                "AUTO_SWITCH_TARGET_MODE",
                EnergyMode.UTI,
            ),
            patch.object(
                energy_mode_controller,
                "is_time_reached",
                return_value=True,
            ),
            patch.object(
                energy_mode_controller,
                "should_switch_to_solar_priority",
                return_value=True,
            ) as solar_rule_mock,
            patch.object(
                energy_mode_controller,
                "switch_energy_mode",
            ) as switch_mock,
        ):
            result = energy_mode_controller.handle_energy_mode_control(
                self.must_data,
                solar_history=[],
            )

        self.assertTrue(result)
        switch_mock.assert_called_once_with(target_mode=EnergyMode.UTI)
        solar_rule_mock.assert_not_called()

    def test_solar_rule_does_not_switch_from_another_source_mode(self):
        self.must_data["EnergyUseMode"] = EnergyMode.UTI.value

        with (
            patch.object(
                energy_mode_controller,
                "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
                False,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_AUTO_SWITCH",
                False,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_SOLAR_AUTO_SWITCH",
                True,
            ),
            patch.object(
                energy_mode_controller,
                "should_switch_to_solar_priority",
                return_value=True,
            ) as solar_rule_mock,
            patch.object(
                energy_mode_controller,
                "switch_energy_mode",
            ) as switch_mock,
        ):
            result = energy_mode_controller.handle_energy_mode_control(
                self.must_data,
                solar_history=[],
            )

        self.assertFalse(result)
        solar_rule_mock.assert_not_called()
        switch_mock.assert_not_called()

    def test_cooldown_blocks_only_the_same_target_mode(self):
        energy_mode_controller._last_command_timestamps[EnergyMode.SBU] = 900.0

        with (
            patch.object(energy_mode_controller.time, "monotonic", return_value=1000.0),
            patch.object(
                energy_mode_controller,
                "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
                False,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_AUTO_SWITCH",
                False,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_SOLAR_AUTO_SWITCH",
                True,
            ),
            patch.object(
                energy_mode_controller,
                "should_switch_to_solar_priority",
                return_value=True,
            ),
            patch.object(
                energy_mode_controller,
                "switch_energy_mode",
            ) as switch_mock,
        ):
            result = energy_mode_controller.handle_energy_mode_control(
                self.must_data,
                solar_history=[],
            )

        self.assertFalse(result)
        switch_mock.assert_not_called()

        self.must_data["GridVoltage"] = 0.0

        with (
            patch.object(energy_mode_controller.time, "monotonic", return_value=1000.0),
            patch.object(
                energy_mode_controller,
                "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
                True,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_AUTO_SWITCH",
                False,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_SOLAR_AUTO_SWITCH",
                True,
            ),
            patch.object(
                energy_mode_controller,
                "GRID_OUTAGE_TARGET_MODE",
                EnergyMode.UTI,
            ),
            patch.object(
                energy_mode_controller,
                "switch_energy_mode",
            ) as different_target_switch_mock,
        ):
            result = energy_mode_controller.handle_energy_mode_control(
                self.must_data,
                solar_history=[],
            )

        self.assertTrue(result)
        different_target_switch_mock.assert_called_once_with(
            target_mode=EnergyMode.UTI,
        )

    def test_failed_command_does_not_start_cooldown(self):
        with (
            patch.object(
                energy_mode_controller,
                "ENABLE_GRID_OUTAGE_AUTO_SWITCH",
                False,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_AUTO_SWITCH",
                False,
            ),
            patch.object(
                energy_mode_controller,
                "ENABLE_SOLAR_AUTO_SWITCH",
                True,
            ),
            patch.object(
                energy_mode_controller,
                "should_switch_to_solar_priority",
                return_value=True,
            ),
            patch.object(
                energy_mode_controller,
                "switch_energy_mode",
                side_effect=OSError("serial failure"),
            ),
        ):
            result = energy_mode_controller.handle_energy_mode_control(
                self.must_data,
                solar_history=[],
            )

        self.assertFalse(result)
        self.assertNotIn(
            EnergyMode.SBU,
            energy_mode_controller._last_command_timestamps,
        )


if __name__ == "__main__":
    unittest.main()
