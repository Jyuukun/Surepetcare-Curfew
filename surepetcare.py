# -*- coding: utf-8 -*-

import os
import sys
import signal
import smtplib

from configparser import ConfigParser
from datetime import datetime
from dateutil.relativedelta import relativedelta

from weboob.browser.browsers import APIBrowser, need_login
from weboob.exceptions import BrowserIncorrectPassword
from weboob.tools.date import utc2local


class SurepetcareBrowser(APIBrowser):
    BASEURL = 'https://app.api.surehub.io'
    BATTERY_ALERT = 0.3
    SEASON = 'winter'
    # XXX verify -1 hour due to +01:00 set on time
    TIME_CONFIG = {
        'summer': {
            'delta': {
                'sunrise': 0.5,
                'sunset': 1.5,
            },
            'min': "08:30:00",  # -1 hour
            'max': "17:30:00",  # -1 hour
        },
        'winter': {
            'delta': {
                'sunrise': 0,
                'sunset': 1,
            },
            'min': "07:00:00",  # -1 hour
            'max': "15:00:00",  # -1 hour
        },
    }

    def __init__(self, config, *args, **kwargs):
        super(SurepetcareBrowser, self).__init__(*args, **kwargs)
        self.config = config

    @property
    def curfew(self):
        results = self.request(
            'https://api.sunrise-sunset.org/json',
            params={'lat': 49.41794, 'lng': 2.82606,}
        )['results']

        curfew = {'enabled': True}

        for sun_state in ('sunrise', 'sunset'):
            time = utc2local(datetime.strptime(results[sun_state].split()[0], '%H:%M:%S'))

            time_config = self.TIME_CONFIG[self.SEASON]
            is_summer = int(self.SEASON == "summer")
            if sun_state == "sunrise":
                time += relativedelta(hours=time_config['delta']['sunrise'] + is_summer)
                time = min(time, utc2local(datetime.strptime(time_config['min'], '%H:%M:%S')))
                curfew['unlock_time'] = time.strftime('%H:%M')
            else:
                # convert to 24 hours format
                time += relativedelta(hours=12 + is_summer)
                time -= relativedelta(hours=time_config['delta']['sunset'])
                time = max(time, utc2local(datetime.strptime(time_config['max'], '%H:%M:%S')))
                curfew['lock_time'] = time.strftime('%H:%M')

        return curfew

    def do_login(self):
        r = self.request(
            '/api/auth/login', data={
                'device_id': "1",
                'email_address': self.config['credentials']['email'],
                'password': self.config['credentials']['password'],
            }
        )

        if 'error' in r:
            raise BrowserIncorrectPassword()

        self.session.headers['Authorization'] = 'Bearer %s' % r['data']['token']

    def send_mail(self, subject, text):
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(
                self.config['mail']['login'], self.config['mail']['password']
            )

            message = 'Subject: {}\n\n{}'.format(subject, text)
            server.sendmail(
                self.config['mail']['sender'], self.config['mail']['receiver'],
                message.encode('utf-8')
            )

    @need_login
    def set_curfew(self):
        for device in self.request('/api/me/start')['data']['devices']:
            if 'chatiere' in device['name'].lower():
                battery = device['status']['battery']
                if battery and (battery / 10) < self.BATTERY_ALERT:
                    self.send_mail(
                        "Chati??re - Batterie faible !",
                        "La batterie de la chati??re est faible, il reste seulement %s pourcents !" % (device['status']['battery'] * 10)
                    )

                device_id = device['id']
                break

        self.request(
            '/api/device/%s/control' % device_id,
            method='PUT', data={"curfew": [self.curfew]}
        )


def get_config():
    config = ConfigParser()
    config.read(os.path.dirname(os.path.abspath(sys.argv[0])) + '/config')
    return config


def signal_handler(signal, frame):
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    config = get_config()
    SurepetcareBrowser(config).set_curfew()


if __name__ == '__main__':
    main()
