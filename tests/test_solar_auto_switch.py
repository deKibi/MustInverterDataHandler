# tests/test_solar_auto_switch.py

# Standard Libraries
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

# Custom Modules
from energy_mode_control import solar_auto_switch


class SolarAutoSwitchTestCase(unittest.TestCase):
    def setUp(self):
        self.current_datetime = datetime(2026, 7, 11, 12, 0)
        self.samples = [
            {
                "timestamp": self.current_datetime
                - timedelta(minutes=5)
                + timedelta(seconds=index * (300 / 7)),
                "BatteryVoltage": 26.8,
                "PLoad": 400.0,
                "PvVoltage": 38.0,
                "ChargerPower": 80.0,
            }
            for index in range(8)
        ]

        self.settings_patch = patch.multiple(
            solar_auto_switch,
            SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES=8,
            SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES=5,
            SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE=26.8,
            SOLAR_AUTO_SWITCH_MAX_LOAD_POWER=400.0,
            SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE=38.0,
            SOLAR_AUTO_SWITCH_MIN_CHARGER_POWER=80.0,
        )
        self.settings_patch.start()

    def tearDown(self):
        self.settings_patch.stop()

    def test_accepts_threshold_values_with_sufficient_history(self):
        result = solar_auto_switch.should_switch_to_solar_priority(
            solar_history=self.samples,
            current_datetime=self.current_datetime,
        )

        self.assertTrue(result)

    def test_rejects_insufficient_valid_samples(self):
        self.samples[0]["BatteryVoltage"] = None

        result = solar_auto_switch.should_switch_to_solar_priority(
            solar_history=self.samples,
            current_datetime=self.current_datetime,
        )

        self.assertFalse(result)

    def test_rejects_samples_with_too_short_time_span(self):
        for index, sample in enumerate(self.samples):
            sample["timestamp"] = (
                self.current_datetime
                - timedelta(minutes=4)
                + timedelta(seconds=index)
            )

        result = solar_auto_switch.should_switch_to_solar_priority(
            solar_history=self.samples,
            current_datetime=self.current_datetime,
        )

        self.assertFalse(result)

    def test_rejects_end_time_boundary(self):
        result = solar_auto_switch.should_switch_to_solar_priority(
            solar_history=self.samples,
            current_datetime=self.current_datetime.replace(hour=18),
        )

        self.assertFalse(result)

    def test_rejects_when_any_average_misses_its_threshold(self):
        threshold_fields = {
            "BatteryVoltage": 26.7,
            "PLoad": 401.0,
            "PvVoltage": 37.9,
            "ChargerPower": 79.0,
        }

        for field, invalid_value in threshold_fields.items():
            with self.subTest(field=field):
                samples = [sample.copy() for sample in self.samples]
                for sample in samples:
                    sample[field] = invalid_value

                result = solar_auto_switch.should_switch_to_solar_priority(
                    solar_history=samples,
                    current_datetime=self.current_datetime,
                )

                self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
