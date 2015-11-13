from setuptools import setup
from hatarake import __version__

APP = ['hatarake/app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
    },
    'packages': [
        'certifi'
        'gntp',
        'icalendar',
        'jinja2',
        'rumps',
    ],
}

setup(
    name='Hatarake',
    author='Paul Traylor',
    version=__version__,
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'certifi',
        'click',
        'gntp',
        'icalendar',
        'jinja2',
        'requests',
        'rumps',
    ],
    entry_points={
        'console_scripts': [
            'hatarake = hatarake.cli:main'
        ]
    }
)
