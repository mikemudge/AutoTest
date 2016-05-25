# The base root folder for your projects. Everything else is relative to this.
# This should be a git controlled directory which is not manually edited.
# E.g '/Users/mudge/projects/AutoTestWeb'
PROJECT_PATH = None

# TODO add config for server tests location (for nose)
# tests/server
# TODO add config for client tests location (for karma)
# tests/karma-auto.conf.js
# Could support a list of location/runner/extraConfig?

TEST_DB_FILE = 'local_tests.sqlite'

TEST_EXCLUDE_BRANCHES = ['']

try:
    # import the local config to override for local settings
    from local_auto_config import *
except:
    pass
