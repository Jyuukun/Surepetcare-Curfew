# -*- coding: utf-8 -*-

import os
import sys
import signal
import smtplib

from configparser import ConfigParser
from datetime import datetime

from weboob.browser.browsers import APIBrowser, need_login
from weboob.exceptions import BrowserIncorrectPassword

from curfew import PARIS, acclimatization_from_config, curfew_times, season_settings_from_config


class SurepetcareBrowser(APIBrowser):
    TIMEOUT = 20
    BASEURL = 'https://app.api.surehub.io'

    BATTERY_ALERT = 15  # 0 to 100

    def __init__(self, config, *args, **kwargs):
        super(SurepetcareBrowser, self).__init__(*args, **kwargs)
        self.config = config

    @property
    def curfew(self):
        today = datetime.now(PARIS).date()

        results = self.request(
            'https://api.sunrise-sunset.org/json',
            params={'lat': 49.41794, 'lng': 2.82606, 'formatted': 0, 'date': today.isoformat()}
        )['results']

        unlock_time, lock_time = curfew_times(
            datetime.fromisoformat(results['sunrise']),
            datetime.fromisoformat(results['sunset']),
            season_settings_from_config(self.config, today),
            acclimatization_from_config(self.config),
        )

        return {
            'enabled': True,
            'unlock_time': unlock_time.strftime('%H:%M'),
            'lock_time': lock_time.strftime('%H:%M'),
        }

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
        """
        for battery not sure how it works but what I see is :

        5.679 = full
        5.589 = 3 bars
        5.406 = 3 bars
        5.337 = 2 bars
        5.188 = 2 bars
        4.849 = empty
        3.916 = empty
        """
        for device in self.request('/api/me/start')['data']['devices']:
            if 'chatiere' in device['name'].lower():
                battery = device['status']['battery']
                empty = 4.849
                full = 5.679
                battery = max(0, round((battery - empty) / (full - empty) * 100))

                if battery and battery <= self.BATTERY_ALERT:
                    self.send_mail(
                        "Chatière - Batterie faible !",
                        f"La batterie de la chatière est faible ({battery} %) !\n"
                        "Attention les petits chats d'amour vont être coincés ! :0\n"
                        "Donc on s'active et on va recharger les piles, okey ?!\n"
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
