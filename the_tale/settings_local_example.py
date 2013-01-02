# -*- coding: utf-8 -*-
import sys

TESTS_RUNNING = 'test' in sys.argv or 'testserver' in sys.argv

DEBUG = 'runserver' in sys.argv

# DEBUG_DATABASE_USAGE = True
# DEBUG_DATABASE_USAGE_OUTPUT_DIR = '/home/tie/tmp/db/'

GAME_ENABLE_WORKER_HIGHLEVEL = True
GAME_ENABLE_WORKER_TURNS_LOOP = False
GAME_ENABLE_WORKER_MIGHT_CALCULATOR = False
GAME_ENABLE_WORKER_LONG_COMMANDS = False
GAME_ENABLE_PVP = True

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/emails'

PVP_BALANCING_WITHOUT_LEVELS = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'the-tale',
        'USER': 'the-tale',
        'PASSWORD': 'the-tale',
        'HOST': '',
        'PORT': '',
    }
}

if TESTS_RUNNING:
    SOUTH_TESTS_MIGRATE=False
    SKIP_SOUTH_TESTS=True
    PVP_BALANCING_WITHOUT_LEVELS = False

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'the_tale.sqlite',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
            }
        }
