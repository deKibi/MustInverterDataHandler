# energy_mode_control/solar_windows.py

# Standard Libraries
import logging
from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
from typing import Final

# Custom Modules
from energy_mode_control.time_utils import (
    KYIV_TIMEZONE,
    get_current_kyiv_datetime,
)


logger = logging.getLogger(__name__)


class SolarSeason(str, Enum):
    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"


SEASONAL_SOLAR_WINDOWS: Final[dict[SolarSeason, tuple[time, time]]] = {
    SolarSeason.WINTER: (time(10, 0), time(15, 0)),
    SolarSeason.SPRING: (time(9, 0), time(18, 0)),
    SolarSeason.SUMMER: (time(8, 0), time(19, 0)),
    SolarSeason.AUTUMN: (time(9, 0), time(17, 0)),
}

_solar_window_configuration_logged = False


@dataclass(frozen=True)
class SolarWindow:
    season: SolarSeason
    seasonal_start: time
    seasonal_end: time
    start: time
    end: time


def get_solar_season(current_datetime: datetime) -> SolarSeason:
    """Return the meteorological season for a Kyiv-local datetime."""
    month = to_kyiv_datetime(current_datetime).month

    if month in {12, 1, 2}:
        return SolarSeason.WINTER
    if month in {3, 4, 5}:
        return SolarSeason.SPRING
    if month in {6, 7, 8}:
        return SolarSeason.SUMMER

    return SolarSeason.AUTUMN


def to_kyiv_datetime(current_datetime: datetime) -> datetime:
    """Convert an aware datetime to Kyiv or treat a naive value as Kyiv."""
    if current_datetime.tzinfo is None:
        return current_datetime.replace(tzinfo=KYIV_TIMEZONE)

    return current_datetime.astimezone(KYIV_TIMEZONE)


def resolve_solar_window(
    current_datetime: datetime | None = None,
    start_override: time | None = None,
    end_override: time | None = None,
) -> SolarWindow:
    """Resolve the effective solar window for the current Kyiv season."""
    if current_datetime is None:
        current_datetime = get_current_kyiv_datetime()

    season = get_solar_season(current_datetime)
    seasonal_start, seasonal_end = SEASONAL_SOLAR_WINDOWS[season]
    resolved_start = start_override or seasonal_start
    resolved_end = end_override or seasonal_end

    if resolved_start >= resolved_end:
        raise ValueError(
            f"Resolved solar window for {season.value} must start before "
            f"it ends: {_format_time(resolved_start)}-"
            f"{_format_time(resolved_end)}"
        )

    return SolarWindow(
        season=season,
        seasonal_start=seasonal_start,
        seasonal_end=seasonal_end,
        start=resolved_start,
        end=resolved_end,
    )


def validate_solar_window_overrides(
    start_override: time | None,
    end_override: time | None,
) -> None:
    """Ensure configured overrides resolve to a valid window every season."""
    representative_months = (1, 4, 7, 10)

    for month in representative_months:
        resolve_solar_window(
            current_datetime=datetime(2026, month, 1, tzinfo=KYIV_TIMEZONE),
            start_override=start_override,
            end_override=end_override,
        )


def is_datetime_in_solar_window(
    current_datetime: datetime | None = None,
    start_override: time | None = None,
    end_override: time | None = None,
) -> bool:
    """Return whether the Kyiv-local time is inside the resolved window."""
    if current_datetime is None:
        current_datetime = get_current_kyiv_datetime()

    kyiv_datetime = to_kyiv_datetime(current_datetime)
    window = resolve_solar_window(
        current_datetime=kyiv_datetime,
        start_override=start_override,
        end_override=end_override,
    )
    current_time = time(
        hour=kyiv_datetime.hour,
        minute=kyiv_datetime.minute,
    )

    return window.start <= current_time < window.end


def log_solar_window_configuration(
    start_override: time | None,
    end_override: time | None,
    current_datetime: datetime | None = None,
) -> None:
    """Log the active automatic or overridden solar window once."""
    global _solar_window_configuration_logged

    if _solar_window_configuration_logged:
        return

    window = resolve_solar_window(
        current_datetime=current_datetime,
        start_override=start_override,
        end_override=end_override,
    )
    resolved_range = f"{_format_time(window.start)}-{_format_time(window.end)}"
    seasonal_range = (
        f"{_format_time(window.seasonal_start)}-"
        f"{_format_time(window.seasonal_end)}"
    )

    if start_override is None and end_override is None:
        logger.info(
            "Solar window is selected automatically for %s in "
            "Europe/Kyiv: %s.",
            window.season.value,
            resolved_range,
        )
    elif (
        window.start >= window.seasonal_start
        and window.end <= window.seasonal_end
    ):
        logger.info(
            "Solar window override %s is within the %s seasonal window %s "
            "in Europe/Kyiv.",
            resolved_range,
            window.season.value,
            seasonal_range,
        )
    else:
        logger.warning(
            "Solar window override %s extends outside the %s seasonal "
            "window %s in Europe/Kyiv; the override is used without "
            "automatic clipping.",
            resolved_range,
            window.season.value,
            seasonal_range,
        )

    _solar_window_configuration_logged = True


def _format_time(value: time) -> str:
    return value.strftime("%H:%M")
