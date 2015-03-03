#!/usr/bin/env python
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ),
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.staticfiles',
            'rapidsms',
            'multitenancy',
        ),
        # multitenancy uses a test-only model, which won't be loaded if we only load
        # our real migration files, so point to a nonexistent one, which will make
        # the test runner load all of the models it finds.
        MIGRATION_MODULES={
            'multitenancy': 'multitenancy.migrations_not_used_in_tests'
        },
        ROOT_URLCONF='multitenancy.tests.urls',
        SITE_ID=1,
        SECRET_KEY='this-is-just-for-tests-so-not-that-secret',
        STATIC_URL='/static/',
    )


def runtests():
    if hasattr(django, 'setup'):
        django.setup()
    apps = sys.argv[1:] or ['multitenancy', ]
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True, failfast=False)
    failures = test_runner.run_tests(apps)
    sys.exit(failures)


if __name__ == '__main__':
    runtests()
