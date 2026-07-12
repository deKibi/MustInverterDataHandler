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
                "PLoad": 700.0,
                "PvVoltage": 38.0,
            }
            for index in range(8)
        ]

        self.settings_patch = patch.multiple(
            solar_auto_switch,
            SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES=8,
            SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES=5,
            SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE=26.8,
            SOLAR_AUTO_SWITCH_MAX_LOAD_POWER=700.0,
            SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE=38.0,
            SOLAR_AUTO_SWITCH_MIN_LATEST_BATTERY_VOLTAGE=26.4,
            SOLAR_AUTO_SWITCH_MAX_LATEST_LOAD_POWER=800.0,
            SOLAR_AUTO_SWITCH_MIN_LATEST_PV_VOLTAGE=35.0,
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
            "PLoad": 701.0,
            "PvVoltage": 37.9,
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

    def test_rejects_latest_load_spike_hidden_by_good_average(self):
        for sample in self.samples:
            sample["PLoad"] = 100.0
        self.samples[-1]["PLoad"] = 1200.0

        result = solar_auto_switch.should_switch_to_solar_priority(
            solar_history=self.samples,
            current_datetime=self.current_datetime,
        )

        self.assertLess(
            sum(sample["PLoad"] for sample in self.samples)
            / len(self.samples),
            700.0,
        )
        self.assertFalse(result)

    def test_rejects_latest_battery_drop_hidden_by_good_average(self):
        for sample in self.samples:
            sample["BatteryVoltage"] = 27.0
        self.samples[-1]["BatteryVoltage"] = 26.3

        result = solar_auto_switch.should_switch_to_solar_priority(
            solar_history=self.samples,
            current_datetime=self.current_datetime,
        )

        self.assertFalse(result)

    def test_rejects_latest_pv_drop_hidden_by_good_average(self):
        for sample in self.samples:
            sample["PvVoltage"] = 39.0
        self.samples[-1]["PvVoltage"] = 34.0

        result = solar_auto_switch.should_switch_to_solar_priority(
            solar_history=self.samples,
            current_datetime=self.current_datetime,
        )

        self.assertFalse(result)

    def test_accepts_latest_values_on_hard_limit_boundaries(self):
        for sample in self.samples:
            sample["BatteryVoltage"] = 27.0
            sample["PLoad"] = 100.0
            sample["PvVoltage"] = 39.0

        self.samples[-1]["BatteryVoltage"] = 26.4
        self.samples[-1]["PLoad"] = 800.0
        self.samples[-1]["PvVoltage"] = 35.0

        result = solar_auto_switch.should_switch_to_solar_priority(
            solar_history=self.samples,
            current_datetime=self.current_datetime,
        )

        self.assertTrue(result)

    def test_rejects_invalid_latest_raw_sample(self):
        invalid_latest_sample = self.samples[-1].copy()
        invalid_latest_sample["timestamp"] += timedelta(seconds=1)
        invalid_latest_sample["PLoad"] = None

        result = solar_auto_switch.should_switch_to_solar_priority(
            solar_history=self.samples + [invalid_latest_sample],
            current_datetime=self.current_datetime,
        )

        self.assertFalse(result)

    def test_accepts_sub_mode_conditions_with_low_charger_power(self):
        for sample in self.samples:
            sample["BatteryVoltage"] = 27.1
            sample["PLoad"] = 595.0
            sample["PvVoltage"] = 43.7
            sample["ChargerPower"] = 8.0

        result = solar_auto_switch.should_switch_to_solar_priority(
            solar_history=self.samples,
            current_datetime=self.current_datetime,
        )

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
