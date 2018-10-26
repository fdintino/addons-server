def is_prod_branch() {
  return "${BRANCH_NAME}" == "develop" || "${BRANCH_NAME}" == "master"
}

def get_custom_workspace() {
  (project, branch) = ("${JOB_NAME}").toLowerCase().split('/')
  branch = branch.replaceFirst("beta%2f","")
  return "/www/builds/${project}/${branch}"
}

def database_suffix() {
  if ("${BRANCH_NAME}".startsWith('PR-')) {
    return 'dev'
  } else {
    return build_name_uc()
  }
}

def build_name() {
  build = "${BRANCH_NAME}".toLowerCase()
  if (build.startsWith('beta/')) {
    build = build[5..-1]
  }
  return build
}

def build_name_uc() {
  return build_name().replace('-', '_')
}

def get_local_settings() {
  return """\
    import os

    CACHES = {
        'default': {
              'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
              'LOCATION': '${MEMCACHE_LOCATION}',
              'KEY_PREFIX': '${build_name_uc()}_',
        },
    }
    ES_INDEXES = {
        'default': 'addons_${build_name_uc()}'
    }
    SITE_URL = '${OLYMPIA_SITE_URL}'
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '${MEMCACHE_LOCATION}',
        },
    }
    DATABASES = {
        'default': {
            'ENGINE': 'olympia.core.db.mysql',
            'AUTOCOMMIT': True,
            'ATOMIC_REQUESTS': True,
            'NAME': '${DATABASE_NAME}',
            'CONN_MAX_AGE': 300,
            'TIME_ZONE': None,
            'OPTIONS': {
                'isolation_level': 'read committed',
                'sql_mode': 'STRICT_ALL_TABLES',
            },
            'HOST': 'mysqld',
            'USER': 'root',
            'TEST': {
                'COLLATION': 'utf8_general_ci',
                'CHARSET': 'utf8',
                'NAME': None,
                'MIRROR': None,
            },
            'PASSWORD': '',
            'PORT': '',
        },
    }
    CELERY_BROKER_URL = '${CELERY_BROKER_URL}'
    CELERY_RESULT_BACKEND = '${CELERY_RESULT_BACKEND}'
    ALLOWED_HOSTS = ['${build_name()}.djangobeta.nginxdemo']""".stripIndent()
}

pipeline {
  agent {
    node {
      label "addons"
      customWorkspace get_custom_workspace()
    }
  }

  options {
    timestamps()
    skipStagesAfterUnstable()
    disableConcurrentBuilds()
  }

  environment {
    DJANGO_SETTINGS_MODULE = 'settings'
    CHROME_BIN = '/usr/lib64/chromium-browser/headless_shell'
    NODE_ENV = 'deployment'
    COVERAGE_PROCESS_START = "${WORKSPACE}/.coveragerc"  // enables python coverage
    LANG = 'en_US.UTF-8'
    LC_ALL = 'en_US.UTF-8'
    PYTHONPATH = "${WORKSPACE}/src"
    ADDONS_LINTER_BIN = "${WORKSPACE}/node_modules/.bin/addons-linter"
    CLEANCSS_BIN = "${WORKSPACE}/node_modules/.bin/cleancss"
    LESS_BIN = "${WORKSPACE}/node_modules/.bin/lessc"
    UGLIFY_BIN = "${WORKSPACE}/node_modules/.bin/uglifyjs"
    ADDONS_VALIDATOR_BIN = "${WORKSPACE}/bin"
    RUNNING_IN_CI = '1'
    DATABASE_NAME = "olympia_${database_suffix()}"
    DATABASES_DEFAULT_URL = "mysql://root:@mysqld/olympia_${database_suffix()}"
    CELERY_RESULT_BACKEND = "db+mysql://root:@mysqld/${DATABASE_NAME}"
    OLYMPIA_SITE_URL = "http://${build_name()}.djangobeta.nginxdemo"
    CELERY_BROKER_URL = "amqp://olympia:olympia@rabbitmq/olympia_${build_name_uc()}"
    ELASTICSEARCH_LOCATION = "elasticsearch:9200"
    MEMCACHE_LOCATION = "memcached:11211"
    PATH = "${WORKSPACE}/bin:$PATH"
    FXA_EMAIL = "uitest-${UUID.randomUUID().toString()}@restmail.net"
    FXA_PASSWORD = "uitester"
  }

  stages {
    stage('checkout') {
      steps {
        checkout scm
        sh 'git clean -d -f -x'
        sh 'virtualenv .'
        sh 'env'
        script {
          writeFile(file: 'local_settings.py', text: get_local_settings())
        }
      }
    }
    stage('install dependencies') {
      parallel {
        stage('pip') {
          steps {
            sh """
              bin/pip install --no-cache-dir --exists-action=w --no-deps \\
                -r requirements/system.txt \\
                -r requirements/prod_py2.txt \\
                -r requirements/prod_py2.txt \\
                -r requirements/tests.txt
            """
          }
        }
        stage('node') {
          steps {
            sh 'npm install'
            sh 'make -f Makefile-docker copy_node_js'
          }
        }
      }
    }
    stage('setup') {
      parallel {
        stage('locale') {
          steps {
            sh 'locale/compile-mo.sh locale'
          }
        }
        stage('init_db') {
          steps {
            script {
              try {
                sh "nginxdemo_scripts/create_beta_db.py ${DATABASE_NAME}"
              } catch (exc) {
                // non-zero exit code means db was created, continue initializing
              	sh 'rm -rf ./user-media/* ./tmp/*'
              	sh 'python manage.py reset_db --noinput'
              	sh 'python manage.py migrate --noinput --run-syncdb'
              	sh 'python manage.py loaddata initial.json'
              	sh 'python manage.py import_prod_versions'
              	sh 'schematic --fake src/olympia/migrations/'
              	sh '''python manage.py createsuperuser --username admin \\
                    --email admin@example.com --noinput'''
              	sh 'python manage.py loaddata zadmin/users'
              	sh 'python manage.py update_permissions_from_mc'
                sh 'python manage.py generate_default_addons_for_frontend'
              }
            }
          }
        }
        stage('assets') {
          steps {
            sh 'bin/python manage.py compress_assets'
            sh 'bin/python manage.py collectstatic --noinput'
          }
        }
        stage('rabbitmq') {
          steps {
            sh "nginxdemo_scripts/create_rabbitmq_vhost.py olympia_${build_name_uc()}"
          }
        }
      }
    }
    stage('stage') {
      steps {
        sh 'cp uwsgi/master.ini.tmpl uwsgi/master.ini'
        sh 'cp uwsgi/workerweb.ini.tmpl uwsgi/workerweb.ini'
        sh 'cp uwsgi/workercelery.ini.tmpl uwsgi/workercelery.ini'
      }
    }
  }
}
