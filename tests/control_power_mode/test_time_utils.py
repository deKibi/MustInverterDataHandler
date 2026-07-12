# tests/control_power_mode/test_time_utils.py

# Standard Libraries
from datetime import datetime, time

# Third-party Libraries
import pytest

# Custom Modules
from energy_mode_control.time_utils import (
    is_time_in_window,
    is_time_reached,
)


@pytest.mark.parametrize(
    "hour,minute,expected",
    [
        (19, 59, False),
        (20, 0, True),
        (20, 1, True),
    ],
)
def test_scheduled_time_boundary(hour, minute, expected):
    current_datetime = datetime(2026, 7, 12, hour, minute)

    assert is_time_reached(
        target_time=time(20, 0),
        current_datetime=current_datetime,
    ) is expected


@pytest.mark.parametrize(
    "hour,minute,expected",
    [
        (11, 59, False),
        (12, 0, True),
        (17, 59, True),
        (18, 0, False),
    ],
)
def test_solar_time_window_boundary(hour, minute, expected):
    current_datetime = datetime(2026, 7, 12, hour, minute)

    assert is_time_in_window(
        start_time=time(12, 0),
        end_time=time(18, 0),
        current_datetime=current_datetime,
    ) is expected
