import json
import nose
import os
import subprocess
import sys

def test_server(test_pattern=['!screenshot']):
    from tests.server import base_test_case
    reload(base_test_case)
    import config
    reload(config)

    args = sys.argv[:1]
    # Comma does an and.
    # args.append('-a !screenshot,!local')
    # Repeat -a does an or
    # args.append('-a !screenshot -a !local')
    args.append('-a %s' % ','.join(test_pattern))

    # Running server tests with nose.
    nose.core.run(defaultTest="tests/", argv=args)

    if 'last' not in base_test_case.results:
        raise Exception('Something went wrong, results was not updated. \n%r', base_test_case.results)

    return base_test_case.results

def test_client():
    # Client testing
    if os.path.isfile('results.json'):
        os.remove('results.json')

    # Running client tests with karma.
    command = ["karma", "start", os.getcwd() + "/tests/karma-auto.conf.js"]
    print ' '.join(command)
    subprocess.call(command)

    with open("results.json") as f:
        result = json.load(f)

        if len(result.get('result')) == 0:
            # Might need https://github.com/douglasduteil/karma-json-reporter/issues/13
            # /usr/local/lib/node_modules/karma-json-reporter/index.js
            raise Exception('Something went wrong, no client results')

    os.remove('results.json')
    return result.get('result')
