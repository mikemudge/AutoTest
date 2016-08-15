import auto_config
import json
import nose
import os
import subprocess
import sys
import nose_plugin

def test_server(test_pattern=['!screenshot']):
    args = sys.argv[:1]
    # Comma does an and.
    # args.append('-a !screenshot,!local')
    # Repeat -a does an or
    # args.append('-a !screenshot -a !local')
    args.append('-a %s' % ','.join(test_pattern))

    # Running server tests with nose.
    myplugin = nose_plugin.HelloWorld()
    nose.run(defaultTest="tests/server", addplugins=[myplugin], argv=args)

    if len(myplugin.results) == 0:
        raise Exception('Something went wrong, results was not updated. \n%r', myplugin.results)

    return myplugin.results

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

if __name__ == '__main__':

    sys.path.insert(0, auto_config.PROJECT_PATH)
    os.chdir(auto_config.PROJECT_PATH)

    if len(sys.argv) > 1:
        args = sys.argv
    else:
        args = ['server', 'client']

    if 'server' in args:
        print "Running server tests"
        serverResults = test_server()
        print serverResults
        print json.dumps(serverResults, separators=(',', ':'), indent=4)

    if 'client' in args:
        print "Running client tests"
        clientResults = test_client()
        # print json.dumps(clientResults, separators=(',', ':'), indent=4)
        for (id, results) in clientResults.iteritems():
            for result in results:
                # TODO count things?
                if not result['success']:
                    print result
