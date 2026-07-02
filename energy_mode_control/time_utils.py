# energy_mode_control/time_utils.py

# Standard Libraries
from datetime import datetime, time
from typing import Final
from zoneinfo import ZoneInfo


# Timezone
KYIV_TIMEZONE: Final[ZoneInfo] = ZoneInfo("Europe/Kyiv")


def get_current_kyiv_datetime() -> datetime:
    """
    Return the current date and time in the Europe/Kyiv timezone.

    Returns:
        Timezone-aware datetime object.
    """
    return datetime.now(tz=KYIV_TIMEZONE)


def is_time_reached(
    target_time: time,
    current_datetime: datetime | None = None,
) -> bool:
    """
    Check whether the target time has already been reached today.

    Seconds and microseconds are ignored.
    """
    if current_datetime is None:
        current_datetime = get_current_kyiv_datetime()

    current_time = time(
        hour=current_datetime.hour,
        minute=current_datetime.minute,
    )

    return current_time >= target_time


if __name__ == '__main__':
    print("debugging time_utils")

    kyiv_datetime_now = get_current_kyiv_datetime()
    print("Current Kyiv datetime", kyiv_datetime_now)
    print("Object Type:", type(kyiv_datetime_now))

    now_reached_20 = is_time_reached(kyiv_datetime_now.time())
    print("Is current time after 20:00:", now_reached_20)

    time_9_00 = time(9, 0)
    now_reached_9 = is_time_reached(target_time=time_9_00, current_datetime=kyiv_datetime_now)
    print("Is current time after 9:00:", now_reached_9)

    print("Testing time close boarders:")

    kyiv_datetime_now = get_current_kyiv_datetime()
    target_time = time(20, 0)

    test_datetime_20_00 = kyiv_datetime_now.replace(
        hour=20,
        minute=0,
        second=0,
        microsecond=0,
    )

    test_datetime_20_01 = kyiv_datetime_now.replace(
        hour=20,
        minute=1,
        second=0,
        microsecond=0,
    )

    test_datetime_20_02 = kyiv_datetime_now.replace(
        hour=20,
        minute=2,
        second=0,
        microsecond=0,
    )

    test_datetime_21_30 = kyiv_datetime_now.replace(
        hour=21,
        minute=30,
        second=0,
        microsecond=0,
    )

    print(
        "20:00 reached 20:00:",
        is_time_reached(
            target_time=target_time,
            current_datetime=test_datetime_20_00,
        ),
    )

    print(
        "20:01 reached 20:00:",
        is_time_reached(
            target_time=target_time,
            current_datetime=test_datetime_20_01,
        ),
    )

    print(
        "20:02 reached 20:00:",
        is_time_reached(
            target_time=target_time,
            current_datetime=test_datetime_20_02,
        ),
    )

    print(
        "21:30 reached 20:00:",
        is_time_reached(
            target_time=target_time,
            current_datetime=test_datetime_21_30,
        ),
    )
