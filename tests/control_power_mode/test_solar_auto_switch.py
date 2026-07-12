# tests/control_power_mode/test_solar_auto_switch.py

# Standard Libraries
from datetime import datetime, time, timedelta

# Third-party Libraries
import pytest

# Custom Modules
from energy_mode_control import solar_auto_switch


@pytest.fixture
def current_datetime():
    return datetime(2026, 7, 12, 12, 0)


@pytest.fixture
def valid_samples(current_datetime):
    return [
        {
            "timestamp": current_datetime
            - timedelta(minutes=5)
            + timedelta(seconds=index * (300 / 7)),
            "BatteryVoltage": 26.8,
            "PLoad": 700.0,
            "PvVoltage": 38.0,
        }
        for index in range(8)
    ]


@pytest.fixture(autouse=True)
def solar_settings(monkeypatch):
    settings = {
        "SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES": 8,
        "SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES": 5,
        "SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE": 26.8,
        "SOLAR_AUTO_SWITCH_MAX_LOAD_POWER": 700.0,
        "SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE": 38.0,
        "SOLAR_AUTO_SWITCH_MIN_LATEST_BATTERY_VOLTAGE": 26.4,
        "SOLAR_AUTO_SWITCH_MAX_LATEST_LOAD_POWER": 800.0,
        "SOLAR_AUTO_SWITCH_MIN_LATEST_PV_VOLTAGE": 35.0,
        "SOLAR_AUTO_SWITCH_START_TIME": time(12, 0),
        "SOLAR_AUTO_SWITCH_END_TIME": time(18, 0),
    }

    for setting_name, value in settings.items():
        monkeypatch.setattr(solar_auto_switch, setting_name, value)


def evaluate(samples, current_datetime):
    return solar_auto_switch.should_switch_to_solar_priority(
        solar_history=samples,
        current_datetime=current_datetime,
    )


def test_accepts_average_threshold_boundaries(valid_samples, current_datetime):
    assert evaluate(valid_samples, current_datetime) is True


def test_rejects_insufficient_valid_samples(valid_samples, current_datetime):
    assert evaluate(valid_samples[:-1], current_datetime) is False


def test_rejects_samples_with_too_short_span(valid_samples, current_datetime):
    for index, sample in enumerate(valid_samples):
        sample["timestamp"] = (
            current_datetime
            - timedelta(minutes=4)
            + timedelta(seconds=index)
        )

    assert evaluate(valid_samples, current_datetime) is False


@pytest.mark.parametrize(
    "current_hour,current_minute,expected",
    [
        (11, 59, False),
        (12, 0, True),
        (17, 59, True),
        (18, 0, False),
    ],
)
def test_respects_active_time_window(
    valid_samples,
    current_datetime,
    current_hour,
    current_minute,
    expected,
):
    test_datetime = current_datetime.replace(
        hour=current_hour,
        minute=current_minute,
    )

    assert evaluate(valid_samples, test_datetime) is expected


@pytest.mark.parametrize(
    "field,invalid_value",
    [
        ("BatteryVoltage", 26.7),
        ("PLoad", 701.0),
        ("PvVoltage", 37.9),
    ],
)
def test_rejects_failed_average_condition(
    valid_samples,
    current_datetime,
    field,
    invalid_value,
):
    for sample in valid_samples:
        sample[field] = invalid_value

    assert evaluate(valid_samples, current_datetime) is False


@pytest.mark.parametrize(
    "field,good_value,invalid_latest_value",
    [
        ("BatteryVoltage", 27.0, 26.3),
        ("PLoad", 100.0, 801.0),
        ("PvVoltage", 39.0, 34.9),
    ],
)
def test_rejects_failed_latest_hard_limit(
    valid_samples,
    current_datetime,
    field,
    good_value,
    invalid_latest_value,
):
    for sample in valid_samples:
        sample[field] = good_value
    valid_samples[-1][field] = invalid_latest_value

    assert evaluate(valid_samples, current_datetime) is False


def test_rejects_load_spike_hidden_by_good_average(
    valid_samples,
    current_datetime,
):
    for sample in valid_samples:
        sample["PLoad"] = 100.0
    valid_samples[-1]["PLoad"] = 1200.0

    average_load = sum(
        sample["PLoad"] for sample in valid_samples
    ) / len(valid_samples)

    assert average_load < 700.0
    assert evaluate(valid_samples, current_datetime) is False


def test_accepts_latest_hard_limit_boundaries(
    valid_samples,
    current_datetime,
):
    for sample in valid_samples:
        sample["BatteryVoltage"] = 27.0
        sample["PLoad"] = 100.0
        sample["PvVoltage"] = 39.0

    valid_samples[-1]["BatteryVoltage"] = 26.4
    valid_samples[-1]["PLoad"] = 800.0
    valid_samples[-1]["PvVoltage"] = 35.0

    assert evaluate(valid_samples, current_datetime) is True


@pytest.mark.parametrize(
    "field,invalid_value",
    [
        ("timestamp", None),
        ("PLoad", None),
        ("PvVoltage", float("nan")),
    ],
)
def test_rejects_invalid_latest_sample(
    valid_samples,
    current_datetime,
    field,
    invalid_value,
):
    invalid_latest = valid_samples[-1].copy()
    invalid_latest["timestamp"] += timedelta(seconds=1)
    invalid_latest[field] = invalid_value

    assert evaluate(
        valid_samples + [invalid_latest],
        current_datetime,
    ) is False


def test_accepts_observed_sub_mode_sunny_conditions(
    valid_samples,
    current_datetime,
):
    for sample in valid_samples:
        sample["BatteryVoltage"] = 27.1
        sample["PLoad"] = 595.0
        sample["PvVoltage"] = 43.7
        sample["ChargerPower"] = 8.0

    assert evaluate(valid_samples, current_datetime) is True
