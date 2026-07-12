# tests/control_power_mode/test_solar_windows.py

# Standard Libraries
import logging
from datetime import datetime, time, timezone

# Third-party Libraries
import pytest

# Custom Modules
from energy_mode_control import solar_windows
from energy_mode_control.solar_windows import SolarSeason
from energy_mode_control.time_utils import KYIV_TIMEZONE


@pytest.fixture(autouse=True)
def reset_window_log_state():
    solar_windows._solar_window_configuration_logged = False
    yield
    solar_windows._solar_window_configuration_logged = False


@pytest.mark.parametrize(
    "month,expected_season",
    [
        (1, SolarSeason.WINTER),
        (2, SolarSeason.WINTER),
        (3, SolarSeason.SPRING),
        (4, SolarSeason.SPRING),
        (5, SolarSeason.SPRING),
        (6, SolarSeason.SUMMER),
        (7, SolarSeason.SUMMER),
        (8, SolarSeason.SUMMER),
        (9, SolarSeason.AUTUMN),
        (10, SolarSeason.AUTUMN),
        (11, SolarSeason.AUTUMN),
        (12, SolarSeason.WINTER),
    ],
)
def test_maps_month_to_meteorological_season(month, expected_season):
    current_datetime = datetime(2026, month, 15, tzinfo=KYIV_TIMEZONE)

    assert solar_windows.get_solar_season(current_datetime) == expected_season


@pytest.mark.parametrize(
    "month,expected_start,expected_end",
    [
        (1, time(10, 0), time(15, 0)),
        (4, time(9, 0), time(18, 0)),
        (7, time(8, 0), time(19, 0)),
        (10, time(9, 0), time(17, 0)),
    ],
)
def test_resolves_conservative_seasonal_window(
    month,
    expected_start,
    expected_end,
):
    window = solar_windows.resolve_solar_window(
        datetime(2026, month, 15, tzinfo=KYIV_TIMEZONE)
    )

    assert window.start == expected_start
    assert window.end == expected_end
    assert window.seasonal_start == expected_start
    assert window.seasonal_end == expected_end


@pytest.mark.parametrize(
    "month,hour,minute,expected",
    [
        (1, 9, 59, False),
        (1, 10, 0, True),
        (1, 14, 59, True),
        (1, 15, 0, False),
        (4, 8, 59, False),
        (4, 9, 0, True),
        (4, 17, 59, True),
        (4, 18, 0, False),
        (7, 7, 59, False),
        (7, 8, 0, True),
        (7, 18, 59, True),
        (7, 19, 0, False),
        (10, 8, 59, False),
        (10, 9, 0, True),
        (10, 16, 59, True),
        (10, 17, 0, False),
    ],
)
def test_seasonal_window_boundaries(month, hour, minute, expected):
    current_datetime = datetime(
        2026,
        month,
        15,
        hour,
        minute,
        tzinfo=KYIV_TIMEZONE,
    )

    assert solar_windows.is_datetime_in_solar_window(
        current_datetime
    ) is expected


def test_converts_aware_utc_datetime_to_kyiv():
    utc_datetime = datetime(2026, 7, 12, 5, 0, tzinfo=timezone.utc)

    kyiv_datetime = solar_windows.to_kyiv_datetime(utc_datetime)

    assert kyiv_datetime.hour == 8
    assert kyiv_datetime.tzinfo == KYIV_TIMEZONE
    assert solar_windows.is_datetime_in_solar_window(utc_datetime) is True


def test_naive_datetime_is_interpreted_as_kyiv_wall_time():
    naive_datetime = datetime(2026, 7, 12, 8, 0)

    kyiv_datetime = solar_windows.to_kyiv_datetime(naive_datetime)

    assert kyiv_datetime.hour == 8
    assert kyiv_datetime.tzinfo == KYIV_TIMEZONE
    assert solar_windows.is_datetime_in_solar_window(naive_datetime) is True


@pytest.mark.parametrize(
    "start_override,end_override,expected_start,expected_end",
    [
        (time(12, 0), time(18, 0), time(12, 0), time(18, 0)),
        (time(12, 0), None, time(12, 0), time(19, 0)),
        (None, time(18, 0), time(8, 0), time(18, 0)),
    ],
)
def test_resolves_full_and_partial_summer_overrides(
    start_override,
    end_override,
    expected_start,
    expected_end,
):
    window = solar_windows.resolve_solar_window(
        current_datetime=datetime(2026, 7, 12, tzinfo=KYIV_TIMEZONE),
        start_override=start_override,
        end_override=end_override,
    )

    assert window.start == expected_start
    assert window.end == expected_end


def test_logs_automatic_window_as_info_once(caplog):
    current_datetime = datetime(2026, 7, 12, tzinfo=KYIV_TIMEZONE)

    with caplog.at_level(logging.INFO, logger=solar_windows.__name__):
        solar_windows.log_solar_window_configuration(
            start_override=None,
            end_override=None,
            current_datetime=current_datetime,
        )
        solar_windows.log_solar_window_configuration(
            start_override=None,
            end_override=None,
            current_datetime=current_datetime,
        )

    assert caplog.text.count("selected automatically") == 1
    assert "summer" in caplog.text
    assert "08:00-19:00" in caplog.text
    assert "Europe/Kyiv" in caplog.text


def test_logs_override_inside_seasonal_window_as_info(caplog):
    with caplog.at_level(logging.INFO, logger=solar_windows.__name__):
        solar_windows.log_solar_window_configuration(
            start_override=time(12, 0),
            end_override=time(18, 0),
            current_datetime=datetime(2026, 7, 12, tzinfo=KYIV_TIMEZONE),
        )

    assert "is within the summer seasonal window" in caplog.text
    assert not any(record.levelno >= logging.WARNING for record in caplog.records)


@pytest.mark.parametrize(
    "start_override,end_override",
    [
        (time(7, 30), time(18, 0)),
        (time(12, 0), time(20, 0)),
        (time(7, 0), time(20, 0)),
    ],
)
def test_warns_but_does_not_clip_override_outside_season(
    caplog,
    start_override,
    end_override,
):
    current_datetime = datetime(2026, 7, 12, tzinfo=KYIV_TIMEZONE)

    with caplog.at_level(logging.WARNING, logger=solar_windows.__name__):
        solar_windows.log_solar_window_configuration(
            start_override=start_override,
            end_override=end_override,
            current_datetime=current_datetime,
        )

    window = solar_windows.resolve_solar_window(
        current_datetime=current_datetime,
        start_override=start_override,
        end_override=end_override,
    )
    assert window.start == start_override
    assert window.end == end_override
    assert "used without automatic clipping" in caplog.text


@pytest.mark.parametrize(
    "start_override,end_override",
    [
        (time(16, 0), None),
        (None, time(8, 30)),
        (time(18, 0), time(17, 0)),
    ],
)
def test_rejects_override_invalid_for_at_least_one_season(
    start_override,
    end_override,
):
    with pytest.raises(ValueError):
        solar_windows.validate_solar_window_overrides(
            start_override=start_override,
            end_override=end_override,
        )
