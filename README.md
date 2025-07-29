# Surepetcare-Curfew

A Python automation tool to manage the curfew schedule of Sure Petcare cat flaps (e.g., SureFlap) based on sunrise and sunset times. It also monitors battery status and sends email alerts when the battery is low.

## Features

-   Automatically sets the cat flap curfew according to sunrise and sunset, with configurable offsets for summer and winter.
-   Sends email notifications if the cat flap battery is low.
-   Fully automated: can be run as a scheduled job (e.g., via cron).

## Requirements

-   Python 3.6+
-   [woob](https://woob.tech/) (Web Outside Of Browsers)
-   [python-dateutil](https://pypi.org/project/python-dateutil/)

## Installation

1. Clone this repository:
    ```bash
    git clone <repo-url>
    cd Surepetcare-Curfew
    ```
2. Install dependencies:
    ```bash
    pip install woob python-dateutil
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

-   Fetches sunrise and sunset times for a fixed location (lat/lng hardcoded in script).
-   Calculates curfew unlock/lock times based on season and configuration.
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
