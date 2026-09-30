from configparser import ConfigParser
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

PARIS = ZoneInfo('Europe/Paris')


@dataclass(frozen=True)
class SeasonSettings:
    unlock_max: time
    lock_min: time
    sunset_delta: timedelta


@dataclass(frozen=True)
class Acclimatization:
    start: date
    lock_time: time
    step: timedelta
    unlock_time: time


def season_on(day: date) -> str:
    noon = datetime.combine(day, time(12, 0), tzinfo=PARIS)

    return 'summer' if noon.dst() else 'winter'


def season_settings_from_config(config: ConfigParser, day: date) -> SeasonSettings:
    section = config[f'curfew.{season_on(day)}']

    return SeasonSettings(
        unlock_max=time.fromisoformat(section['unlock_max']),
        lock_min=time.fromisoformat(section['lock_min']),
        sunset_delta=timedelta(hours=section.getfloat('sunset_delta')),
    )


def acclimatization_from_config(config: ConfigParser) -> Acclimatization | None:
    if not config.has_section('acclimatization'):
        return None

    section = config['acclimatization']

    return Acclimatization(
        start=date.fromisoformat(section['start']),
        lock_time=time.fromisoformat(section['lock_time']),
        step=timedelta(minutes=section.getint('step_minutes')),
        unlock_time=time.fromisoformat(section['unlock_time']),
    )


def paris_wall_clock(moment: datetime) -> datetime:
    return moment.astimezone(PARIS).replace(tzinfo=None)


def curfew_times(
    sunrise: datetime, sunset: datetime, settings: SeasonSettings, acclimatization: Acclimatization | None
) -> tuple[time, time]:
    """Unlock at sunrise (never after unlock_max), lock at sunset - delta (never before lock_min).

    An active acclimatization ramp locks earlier and delays the unlock until the ramp catches up.
    """
    local_sunrise = paris_wall_clock(sunrise)
    today = local_sunrise.date()

    unlock = min(local_sunrise, datetime.combine(today, settings.unlock_max))
    lock = max(paris_wall_clock(sunset) - settings.sunset_delta, datetime.combine(today, settings.lock_min))

    if acclimatization is None:
        return unlock.time(), lock.time()

    days_since_start = (today - acclimatization.start).days
    ramp_lock = datetime.combine(today, acclimatization.lock_time) + days_since_start * acclimatization.step

    if days_since_start < 0 or ramp_lock >= lock:
        return unlock.time(), lock.time()

    return max(unlock, datetime.combine(today, acclimatization.unlock_time)).time(), ramp_lock.time()
