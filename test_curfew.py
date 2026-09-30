from configparser import ConfigParser
from datetime import date, datetime, time, timedelta, timezone

import pytest

from curfew import (
    Acclimatization,
    SeasonSettings,
    acclimatization_from_config,
    curfew_times,
    season_on,
    season_settings_from_config,
)

SUMMER = SeasonSettings(unlock_max=time(7, 0), lock_min=time(19, 0), sunset_delta=timedelta(hours=1.5))
WINTER = SeasonSettings(unlock_max=time(8, 0), lock_min=time(17, 30), sunset_delta=timedelta(hours=1))

CONFIG = """
[curfew.summer]
unlock_max = 07:00
lock_min = 19:00
sunset_delta = 1.5

[curfew.winter]
unlock_max = 08:00
lock_min = 17:30
sunset_delta = 1
"""

ACCLIMATIZATION = """
[acclimatization]
start = 2026-10-01
lock_time = 12:00
step_minutes = 15
unlock_time = 08:00
"""


def utc(year: int, month: int, day: int, hour: int, minute: int, second: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


def parse_config(text: str) -> ConfigParser:
    config = ConfigParser()
    config.read_string(text)

    return config


@pytest.mark.parametrize(
    ('day', 'expected'),
    [
        (date(2026, 3, 28), 'winter'),
        (date(2026, 3, 29), 'summer'),
        (date(2026, 10, 24), 'summer'),
        (date(2026, 10, 25), 'winter'),
    ],
)
def test_season_follows_paris_summer_time(day: date, expected: str) -> None:
    assert season_on(day) == expected


@pytest.mark.parametrize(
    ('sunrise', 'sunset', 'settings', 'expected'),
    [
        # summer, UTC+2, no clamp: sunset 22:00:44 - 1h30
        (utc(2026, 6, 21, 3, 40, 18), utc(2026, 6, 21, 20, 0, 44), SUMMER, (time(5, 40, 18), time(20, 30, 44))),
        # winter, UTC+1, no clamp
        (utc(2026, 12, 21, 6, 30), utc(2026, 12, 21, 17, 45), WINTER, (time(7, 30), time(17, 45))),
        # winter, late sunrise capped at unlock_max, early sunset raised to lock_min
        (utc(2026, 12, 21, 7, 45), utc(2026, 12, 21, 15, 0), WINTER, (time(8, 0), time(17, 30))),
    ],
)
def test_curfew_follows_sun_within_season_bounds(
    sunrise: datetime, sunset: datetime, settings: SeasonSettings, expected: tuple[time, time]
) -> None:
    assert curfew_times(sunrise, sunset, settings, None) == expected


# 2026-10-30: normal curfew is unlock 07:10, lock 17:30 (lock_min)
RAMP_SUNRISE = utc(2026, 10, 30, 6, 10)
RAMP_SUNSET = utc(2026, 10, 30, 16, 20)


@pytest.mark.parametrize(
    ('start', 'unlock_time', 'expected'),
    [
        (date(2026, 10, 30), time(8, 0), (time(8, 0), time(12, 0))),
        (date(2026, 10, 26), time(8, 0), (time(8, 0), time(13, 0))),
        # sunrise after unlock_time: unlock stays at sunrise
        (date(2026, 10, 26), time(7, 0), (time(7, 10), time(13, 0))),
        # day 22: 12:00 + 22 * 15 min reaches the normal lock, ramp is over
        (date(2026, 10, 8), time(8, 0), (time(7, 10), time(17, 30))),
        (date(2026, 9, 1), time(8, 0), (time(7, 10), time(17, 30))),
        (date(2026, 11, 2), time(8, 0), (time(7, 10), time(17, 30))),
    ],
)
def test_acclimatization_moves_lock_later_each_day_until_normal_lock(
    start: date, unlock_time: time, expected: tuple[time, time]
) -> None:
    ramp = Acclimatization(start=start, lock_time=time(12, 0), step=timedelta(minutes=15), unlock_time=unlock_time)

    assert curfew_times(RAMP_SUNRISE, RAMP_SUNSET, WINTER, ramp) == expected


@pytest.mark.parametrize(('day', 'expected'), [(date(2026, 6, 21), SUMMER), (date(2026, 12, 21), WINTER)])
def test_season_settings_read_from_matching_config_section(day: date, expected: SeasonSettings) -> None:
    assert season_settings_from_config(parse_config(CONFIG), day) == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        (CONFIG, None),
        (
            CONFIG + ACCLIMATIZATION,
            Acclimatization(
                start=date(2026, 10, 1), lock_time=time(12, 0), step=timedelta(minutes=15), unlock_time=time(8, 0)
            ),
        ),
    ],
    ids=['absent', 'present'],
)
def test_acclimatization_read_from_optional_config_section(text: str, expected: Acclimatization | None) -> None:
    assert acclimatization_from_config(parse_config(text)) == expected
