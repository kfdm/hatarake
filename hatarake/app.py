# -*- coding: utf-8 -*-
import datetime
import logging
import os

import pytz
import requests
import rumps
from gntp.config import GrowlNotifier

from icalendar import Calendar

from hatarake import USER_AGENT
import hatarake.config
import hatarake.shim

CONFIG_PATH = os.path.join(
    os.path.expanduser("~"),
    'Library',
    'Application Support',
    'Hatarake',
    'config.ini'
)

GROWL_INTERVAL = 30

logger = logging.getLogger(__name__)


class Hatarake(hatarake.shim.Shim):
    def __init__(self):
        super(Hatarake, self).__init__("Hatarake")
        self.menu = ["Reload", "Debug"]
        self.label = self.menu["Reload"]
        self.delay = GROWL_INTERVAL

        self.reload(None)

        self.notifier = GrowlNotifier(
            applicationName='Hatarake',
            notifications=['Nag'],
        )
        self.notifier.register()

    def alert(self, fmt, *args, **kwargs):
        self.notifier.notify(
            noteType='Nag',
            title=u"働け".encode('utf8', 'replace'),
            description=fmt.format(*args).encode('utf8', 'replace'),
            sticky=True,
            identifier=__file__,
            **kwargs
        )

    @rumps.timer(1)
    def _update_clock(self, sender):
        now = datetime.datetime.now(pytz.utc).replace(microsecond=0)
        delta = now - self.when

        logger.debug('Pomodoro %s %s, %s', self.title, self.when, now)

        if delta.total_seconds() % self.delay == 0:
            self.alert(u'[{0}] was {1} ago', self.zname, delta)

        self.label.title = u'Last pomodoro [{0}] was {1} ago'.format(self.zname, delta)

        # If delta is more than a day ago, show the infinity symbol to avoid
        # having a super long label in our menubar
        if delta.days:
            delta = u'∞'
        self.title = u'働 {0}'.format(delta)

    @rumps.timer(60)
    def _update_calendar(self, sender):
        self.reload(None)

    def get_latest(self, calendar_url):
        result = requests.get(calendar_url, headers={'User-Agent': USER_AGENT})
        cal = Calendar.from_ical(result.text)
        recent = None
        for entry in cal.subcomponents:
            if recent is None:
                recent = entry
                continue
            if 'DTEND' not in entry:
                continue
            if entry['DTEND'].dt > recent['DTEND'].dt:
                recent = entry
        return recent['SUMMARY'], recent['DTEND'].dt

    @rumps.clicked("Reload")
    def reload(self, sender):
        self.config = hatarake.config.Config(CONFIG_PATH)
        self.zname, self.when = self.get_latest(self.config.config.get('feed', 'nag'))

    @rumps.clicked("Debug")
    def toggledebug(self, sender):
        sender.state = not sender.state
        if sender.state:
            self.delay = 5
            logging.getLogger().setLevel(logging.INFO)
            logging.info('Setting debugging to INFO and delay to %d', self.delay)
        else:
            logging.info('Setting debugging to WARNING and delay to %d', self.delay)
            logging.getLogger().setLevel(logging.WARNING)
            self.delay = GROWL_INTERVAL


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    Hatarake().run()
