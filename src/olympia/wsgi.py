import logging
import os
import platform
import sys

from datetime import datetime

import django
import django.conf
import django.core.management
import django.utils

from django.core.wsgi import get_wsgi_application

import uwsgi
import uwsgidecorators


project_root = os.path.realpath(
    os.path.join(os.path.dirname(__file__), '..', '..'))

sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

log = logging.getLogger('z.startup')

# Remember when mod_wsgi loaded this file so we can track it in nagios.
wsgi_loaded = datetime.now()

# Do validate and activate translations before running the app.
django.setup()
django.utils.translation.activate(django.conf.settings.LANGUAGE_CODE)

# This is what mod_wsgi runs.
django_app = get_wsgi_application()


@uwsgidecorators.postfork
def set_uwsgi_proc_name():
    repo_dir = os.path.basename(project_root)
    try:
        build_num = open(os.path.join(project_root, '.BUILD')).read().strip()
    except IOError:
        build_num = '?'

    os.environ['DEPLOY_TAG'] = build_num

    uwsgi.setprocname("uwsgi worker %(worker_id)d <%(repo)s> [%(tag)s]" % {
        'worker_id': uwsgi.worker_id(),
        'repo': repo_dir,
        'tag': build_num,
    })


hostname = platform.node().partition('.')[0]


# Normally we could let WSGIHandler run directly, but while we're dark
# launching, we want to force the script name to be empty so we don't create
# any /z links through reverse.  This fixes bug 554576.
def application(env, start_response):
    uwsgi.set_logvar('hostname', hostname)
    uwsgi.set_logvar('worker_id', str(uwsgi.worker_id()))

    if 'HTTP_X_ZEUS_DL_PT' in env:
        env['SCRIPT_URL'] = env['SCRIPT_NAME'] = ''
    env['wsgi.loaded'] = wsgi_loaded
    env['hostname'] = django.conf.settings.HOSTNAME
    env['datetime'] = str(datetime.now())
    return django_app(env, start_response)


# Initialize Newrelic if we configured it
newrelic_ini = getattr(django.conf.settings, 'NEWRELIC_INI', None)
newrelic_uses_environment = os.environ.get('NEW_RELIC_LICENSE_KEY', None)

if newrelic_ini or newrelic_uses_environment:
    import newrelic.agent
    try:
        newrelic.agent.initialize(newrelic_ini)
    except Exception:
        log.exception('Failed to load new relic config.')

    application = newrelic.agent.wsgi_application()(application)
