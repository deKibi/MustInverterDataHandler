# energy_mode_control/solar_auto_switch.py

# Standard Libraries
import logging
import math
from datetime import datetime, timedelta
from typing import Any

# Custom Modules
from config import (
    SOLAR_AUTO_SWITCH_END_TIME,
    SOLAR_AUTO_SWITCH_MAX_LOAD_POWER,
    SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE,
    SOLAR_AUTO_SWITCH_MIN_CHARGER_POWER,
    SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE,
    SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES,
    SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES,
    SOLAR_AUTO_SWITCH_START_TIME,
)
from energy_mode_control.time_utils import is_time_in_window


logger = logging.getLogger(__name__)

REQUIRED_TELEMETRY_FIELDS = (
    "BatteryVoltage",
    "PLoad",
    "PvVoltage",
    "ChargerPower",
)


def should_switch_to_solar_priority(
    solar_history: list[dict[str, Any]] | None,
    current_datetime: datetime | None = None,
) -> bool:
    """Evaluate whether recent telemetry safely supports solar priority."""
    if not is_time_in_window(
        start_time=SOLAR_AUTO_SWITCH_START_TIME,
        end_time=SOLAR_AUTO_SWITCH_END_TIME,
        current_datetime=current_datetime,
    ):
        logger.info("Solar auto-switch is outside its active time window.")
        return False

    valid_samples = _get_valid_samples(solar_history)

    if len(valid_samples) < SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES:
        logger.info(
            "Solar auto-switch needs at least %s valid samples; got %s.",
            SOLAR_AUTO_SWITCH_MIN_VALID_SAMPLES,
            len(valid_samples),
        )
        return False

    sample_span = valid_samples[-1]["timestamp"] - valid_samples[0]["timestamp"]
    minimum_span = timedelta(
        minutes=SOLAR_AUTO_SWITCH_MIN_SAMPLE_SPAN_MINUTES,
    )

    if sample_span < minimum_span:
        logger.info(
            "Solar auto-switch sample span is too short: %s; required: %s.",
            sample_span,
            minimum_span,
        )
        return False

    averages = {
        field: sum(sample[field] for sample in valid_samples)
        / len(valid_samples)
        for field in REQUIRED_TELEMETRY_FIELDS
    }

    conditions_met = (
        averages["BatteryVoltage"]
        >= SOLAR_AUTO_SWITCH_MIN_BATTERY_VOLTAGE
        and averages["PLoad"] <= SOLAR_AUTO_SWITCH_MAX_LOAD_POWER
        and averages["PvVoltage"] >= SOLAR_AUTO_SWITCH_MIN_PV_VOLTAGE
        and averages["ChargerPower"]
        >= SOLAR_AUTO_SWITCH_MIN_CHARGER_POWER
    )

    logger.info(
        "Solar auto-switch averages: BatteryVoltage=%.2f V, "
        "PLoad=%.2f W, PvVoltage=%.2f V, ChargerPower=%.2f W; "
        "conditions met: %s.",
        averages["BatteryVoltage"],
        averages["PLoad"],
        averages["PvVoltage"],
        averages["ChargerPower"],
        conditions_met,
    )

    return conditions_met


def _get_valid_samples(
    solar_history: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    valid_samples = []

    for sample in solar_history or []:
        timestamp = sample.get("timestamp")

        if not isinstance(timestamp, datetime):
            logger.warning(
                "Skipping solar telemetry sample with invalid timestamp."
            )
            continue

        try:
            normalized_sample = {
                field: float(sample[field])
                for field in REQUIRED_TELEMETRY_FIELDS
            }
        except (KeyError, TypeError, ValueError):
            logger.warning(
                "Skipping incomplete or invalid solar telemetry sample."
            )
            continue

        if not all(
            math.isfinite(normalized_sample[field])
            for field in REQUIRED_TELEMETRY_FIELDS
        ):
            logger.warning(
                "Skipping non-finite solar telemetry sample."
            )
            continue

        normalized_sample["timestamp"] = timestamp
        valid_samples.append(normalized_sample)

    return sorted(valid_samples, key=lambda sample: sample["timestamp"])
