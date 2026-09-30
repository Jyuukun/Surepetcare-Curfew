# Surepetcare-Curfew

A Python automation tool to manage the curfew schedule of Sure Petcare cat flaps (e.g., SureFlap) based on sunrise and sunset times. It also monitors battery status and sends email alerts when the battery is low.

## Features

-   Automatically sets the cat flap curfew according to sunrise and sunset, with configurable bounds for summer and winter.
-   Detects the season from French summer time (Europe/Paris), no manual switch.
-   Optional acclimatization ramp: after a move, lock earlier and push the lock time a bit later every day.
-   Sends email notifications if the cat flap battery is low.
-   Fully automated: can be run as a scheduled job (e.g., via cron).

## Requirements

-   Python 3.10+
-   [woob](https://woob.tech/) (Web Outside Of Browsers)

## Installation

1. Clone this repository:
    ```bash
    git clone https://github.com/Jyuukun/Surepetcare-Curfew.git
    cd Surepetcare-Curfew
    ```
2. Install dependencies:
    ```bash
    pip install woob
    ```

## Configuration

Copy the example config and fill in your credentials:

```bash
cp config.example config
```

Edit the `config` file:

```
[credentials]
email = <your_email>
password = <your_password>

[mail]
login = <your_login>
password = <your_password>
sender = <sender_email>
receiver = <receiver_email>
```

-   `credentials`: Sure Petcare account credentials.
-   `mail`: SMTP credentials for sending email notifications (tested with Gmail).
-   `curfew.summer` / `curfew.winter`: curfew bounds in Paris local time, see `config.example`.
    -   `unlock_max`: unlock at sunrise, but never later than this time.
    -   `lock_min`: lock at sunset minus `sunset_delta` hours, but never earlier than this time.
-   `acclimatization` (optional): see below.

### Acclimatization

After a move, cats should go out for short periods first. Add this section to `config`:

```
[acclimatization]
start = 2026-10-01
lock_time = 12:00
step_minutes = 15
unlock_time = 08:00
```

Each daily run locks at `lock_time + step_minutes × days since start` and never unlocks before `unlock_time`.
When this lock time reaches the normal sunset lock time, the section has no effect any more: remove it when you want.

## Tests

```bash
pip install pytest
python -m pytest
```

## Usage

Run the script manually:

```bash
python surepetcare.py
```

Or add to your crontab for daily automation:

```
0 5 * * * /usr/bin/python3 /path/to/Surepetcare-Curfew/surepetcare.py
```

## How it works

-   Fetches today's sunrise and sunset times (UTC) for a fixed location (lat/lng hardcoded in script).
-   Converts them to Paris local time and picks the summer or winter bounds from the current summer time state.
-   Applies the acclimatization ramp when it is active.
-   Logs in to Sure Petcare API and sets the curfew for your cat flap.
-   Checks battery level and sends an email if below threshold.

## Notes

-   The script is designed for a single SureFlap device named with 'chatiere'.
-   The location (latitude/longitude) is hardcoded; adjust in the script if needed.
-   Make sure to allow less secure apps or use an app password for Gmail SMTP.
-   This project is not affiliated with Sure Petcare.

## Credits

Built using [woob](https://woob.tech/)

## License

MIT License. See LICENSE file.
