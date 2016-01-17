# -*- coding: utf-8 -*-
import datetime
import logging
import webbrowser

import gntp.config
import pytz
import requests
import rumps
from icalendar import Calendar

import hatarake
import hatarake.config
import hatarake.shim

LOGGER = logging.getLogger(__name__)

MENU_RELOAD = 'Reload'
MENU_DEBUG = 'Debug'
MENU_ISSUE = 'Report Issue'


class Growler(object):
    def __init__(self):
        self.growl = gntp.config.GrowlNotifier(
            applicationName='Hatarake',
            notifications=['Nag']
        )
        self.growl.register()

    def alert(self, fmt, *args, **kwargs):
        self.growl.notify(
            noteType='Nag',
            title=u"働け".encode('utf8', 'replace'),
            description=fmt.format(*args).encode('utf8', 'replace'),
            sticky=True,
            identifier=__file__,
            **kwargs
        )


class Hatarake(hatarake.shim.Shim):
    def __init__(self):
        super(Hatarake, self).__init__(
            "Hatarake",
            menu=[MENU_RELOAD, MENU_DEBUG, MENU_ISSUE]
        )

        self.delay = hatarake.GROWL_INTERVAL
        self.notifier = Growler()
        self.last_pomodoro_name = None
        self.zwhen = None

        self.reload(None)

    @rumps.timer(1)
    def _update_clock(self, sender):
        now = datetime.datetime.now(pytz.utc).replace(microsecond=0)
        delta = now - self.last_pomodoro_timestamp

        LOGGER.debug('Pomodoro %s %s, %s', self.title, self.last_pomodoro_timestamp, now)

        if delta.total_seconds() % self.delay == 0:
            self.notifier.alert(u'[{0}] was {1} ago', self.last_pomodoro_name, delta)

        self.menu[MENU_RELOAD].title = u'Last pomodoro [{0}] was {1} ago'.format(
            self.last_pomodoro_name,
            delta
        )

        # If delta is more than a day ago, show the infinity symbol to avoid
        # having a super long label in our menubar
        if delta.days:
            delta = u'∞'
        self.title = u'働 {0}'.format(delta)

    @rumps.timer(300)
    @rumps.clicked(MENU_RELOAD)
    def reload(self, sender):
        config = hatarake.config.Config(hatarake.CONFIG_PATH)
        calendar_url = config.config.get('feed', 'nag')

        result = requests.get(calendar_url, headers={'User-Agent': hatarake.USER_AGENT})
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

        self.last_pomodoro_name = recent['SUMMARY']
        self.last_pomodoro_timestamp = recent['DTEND'].dt

    @rumps.clicked(MENU_DEBUG)
    def toggledebug(self, sender):
        sender.state = not sender.state
        if sender.state:
            self.delay = 5
            logging.getLogger().setLevel(logging.INFO)
            logging.info('Setting debugging to INFO and delay to %d', self.delay)
        else:
            logging.info('Setting debugging to WARNING and delay to %d', self.delay)
            logging.getLogger().setLevel(logging.WARNING)
            self.delay = hatarake.GROWL_INTERVAL

    @rumps.clicked(MENU_ISSUE)
    def issues(self, sender):
        webbrowser.open(hatarake.ISSUES_LINK)

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    Hatarake().run()
