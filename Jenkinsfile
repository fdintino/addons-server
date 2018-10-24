def is_prod_branch() {
  return "${BRANCH_NAME}" == "develop" || "${BRANCH_NAME}" == "master"
}

def get_custom_workspace() {
  (project, branch) = ("${JOB_NAME}").toLowerCase().split('/')
  branch = branch.replaceFirst("beta%2f","")
  return "/www/builds/${project}/${branch}"
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
    DJANGO_SETTINGS_MODULE = 'settings_tests'
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
  }

  stages {
    stage('checkout') {
      steps {
        checkout scm
        sh 'git clean -d -f -x'
        sh 'virtualenv .'
        sh 'env'
        sh """
echo "from olympia.lib.settings_base import *\n\\
LESS_BIN = 'node_modules/less/bin/lessc'\n\\
CLEANCSS_BIN = 'node_modules/clean-css-cli/bin/cleancss'\n\\
UGLIFY_BIN = 'node_modules/uglify-js/bin/uglifyjs'\n\\
FXA_CONFIG = {'default': {}, 'internal': {}}\n"\\
> settings_local.py"""
      }
    }
    stage('install dependencies') {
      parallel {
        stage('pip') {
          stages {
            stage('pip_system') {
              steps {
                sh """
                  bin/pip install --no-cache-dir --exists-action=w --no-deps \\
                    -r requirements/system.txt
                """
              }
            }
            stage('pip_prod') {
              steps {
                sh """
                  bin/pip install --no-cache-dir --exists-action=w --no-deps \\
                    -r requirements/prod_py2.txt
                """
              }
            }
            stage('pip_project') {
              steps {
                sh """
                  bin/pip install --no-cache-dir --exists-action=w --no-deps .
                """
              }
            }
            stage('pip_tests') {
              steps {
                sh """
                  bin/pip install --no-cache-dir --exists-action=w --no-deps \\
                    -r requirements/tests.txt
                """
              }
            }
          }
        }
        stage('node') {
          stages {
            stage('npm install') {
              steps {
                sh 'npm install'
              }
            }
            stage('js copy') {
              steps {
                withEnv(["PATH=${WORKSPACE}/bin:$PATH"]) {
                  sh 'make -f Makefile-docker copy_node_js'
                }
              }
            }
          }
        }
      }
    }
    stage('locale') {
      steps {
        withEnv(["DJANGO_SETTINGS_MODULE=settings_local"]) {
          withEnv(["PATH=${WORKSPACE}/bin:$PATH"]) {
            sh 'locale/compile-mo.sh locale'
          }
        }
      }
    }
    stage('build') {
      parallel {
        stage('assets') {
          steps {
            withEnv(["DJANGO_SETTINGS_MODULE=settings_local"]) {
              sh 'bin/python manage.py compress_assets'
              sh 'bin/python manage.py collectstatic --noinput'
            }
          }
        }
      }
    }
    // stage('data') {
    //   parallel {
    //     stage('update_product_details') {
    //       steps {
    //         sh 'bin/python manage.py update_product_details'
    //       }            
    //     }
    //     stage('db') {
    //       steps {
    //         withEnv(["PATH=${WORKSPACE}/bin:$PATH"]) {
    //           sh 'make -f Makefile-docker initialize_db'
    //         }
    //       }
    //     }
    //   }
    // }
  }
}
