import config
import logging
import nose
import os
import subprocess
import sys

from nose.plugins import Plugin

log = logging.getLogger('nose.plugins.helloworld')

class HelloWorld(Plugin):
    name = 'helloworld'

    def options(self, parser, env=os.environ):
        super(HelloWorld, self).options(parser, env=env)

    def configure(self, options, conf):
        super(HelloWorld, self).configure(options, conf)
        self.results = []
        self.enabled = True
        if not self.enabled:
            return

    def addError(self, test, err):
        print 'error'
        result = {
            'success': False,
            'result': 'error',
            'error': err,
            'module': test.test.__class__.__module__,
            'name': test.test.__class__.__name__,
            'method': test.test._testMethodName
        }
        self.results.append(result)

    # TODO not sure that this gets called.
    def addFailure(self, test, err):
        print 'failure'
        result = {
            'success': False,
            'result': 'failure',
            'failure': err,
            'module': test.test.__class__.__module__,
            'name': test.test.__class__.__name__,
            'method': test.test._testMethodName
        }
        self.results.append(result)

    def addSuccess(self, test):
        print 'success'
        result = {
            'success': True,
            'result': 'success',
            'module': test.test.__class__.__module__,
            'name': test.test.__class__.__name__,
            'method': test.test._testMethodName
        }
        self.results.append(result)

    def finalize(self, result):
        # TODO parse result?
        self.result = result

def run_tests():
    print 'testing %s' % config.PROJECT_PATH
    os.chdir(config.PROJECT_PATH)

    try:
        subprocess.check_output('git pull'.split())
    except subprocess.CalledProcessError as e:
        print 'Cmd: %s returned %s' % (e.cmd, e.returncode)

    # Run tests?
    myplugin = HelloWorld()
    nose.run(defaultTest=config.PROJECT_PATH, addplugins=[myplugin])

    for test in myplugin.results:
        print test
    # gather results???

if __name__ == '__main__':
    print sys.argv
    run_tests()
