import os
import subprocess
import sys
import traceback

from datetime import datetime
from test_models import Base, Branch, TestResult, TestRun
from run_tests import test_client, test_server
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

def run_all_tests(branch, commit_hash):
    results = {}

    try:
        print "Running server tests"
        serverResults = test_server()
    except Exception as e:
        print e
        traceback.print_exc()
        serverResults = {}
    try:
        print "Running client tests"
        clientResults = test_client()
    except Exception as e:
        print e
        traceback.print_exc()
        clientResults = {}

    error_count = 0
    failure_count = 0

    for browser_id, tests in clientResults.iteritems():
        for t in tests:
            name = '%s.%s' % ('.'.join(t['suite']), t['description'])
            test = TestResult(result="success", path=name)
            if len(t.get('log')) > 0:
                test.message = '\n'.join(t.get('log'))
            if t.get('skipped'):
                test.result = "skipped"
            elif not t.get('success'):
                test.result = "failure"
                failure_count = failure_count + 1
            results[name] = test

    for test in serverResults['run']:
        results[test] = TestResult(result="success", path=test)

    for (test, errorOutput) in serverResults['last'].errors:
        results[test.id()].result = "error"
        error_count = error_count + 1
        results[test.id()].message = errorOutput

    for (test, errorOutput) in serverResults['last'].failures:
        results[test.id()].result = "failure"
        failure_count = failure_count + 1
        results[test.id()].message = errorOutput

    testRun = TestRun(
        branch=branch,
        commit_hash=commit_hash,
        created_date=datetime.utcnow(),
        test_count=len(results),
        error_count=error_count,
        failure_count=failure_count,
    )

    testResults = results.values()
    testResults.sort()
    for testResult in testResults:
        testRun.results.append(testResult)

    return testRun

def cleanUp():
    try:
        print "git remote prune origin"
        out = subprocess.check_output(["git", "remote", "prune", "origin"])
        print "Pruned remote branches", out
    except Exception as e:
        # This is just a nice to have.
        print "Couldn't prune remote branches", e
    try:
        print "git branch --merged master"
        mergedBranches = subprocess.check_output(['git', 'branch', '--merged', 'master'])
        mergedBranches = [x.strip() for x in mergedBranches.split('\n') if not x.endswith('master') and len(x) > 0]
        print 'mergedBranches', mergedBranches

        if mergedBranches:
            print "git branch -d " + ' '.join(mergedBranches)
            subprocess.check_output(['git', 'branch', '-d'] + mergedBranches)
        print "Removed local merged branches"
    except Exception as e:
        # This is just a nice to have.
        print "Couldn't remove local branches", mergedBranches, e

def check_status(branch):
    branchName = 'origin/%s' % branch.name

    if not branch:
        print "No existing branch for %s, running all tests." % branchName
        # Need to run the tests.
        return True

    latestTestRun = session.query(TestRun).filter(TestRun.branch == branch).order_by(desc(TestRun.created_date)).limit(1).first()
    if not latestTestRun:
        print "No previous test run for %s, running all tests." % branchName
        # Need to run the tests.
        return True

    commit_hash = subprocess.check_output(["git", "rev-parse", branchName]).strip()
    if latestTestRun.commit_hash == commit_hash:
        # No testing required?
        print "Commit hashes match for %s, not testing" % branchName
        return False

    print "New commit hash for %s, running all tests." % branchName
    return True

def test_branch(branch):
    print "Testing branch %s" % branch.name

    # Get into that branch
    print "git checkout " + branch.name
    output = subprocess.check_output(["git", "checkout", branch.name])
    print output

    print "git pull"
    output = subprocess.check_output(["git", "pull"])
    print output

    commit_hash = subprocess.check_output(["git", "rev-parse", 'origin/%s' % branch.name]).strip()
    testRun = run_all_tests(branch, commit_hash)
    session.add(testRun)
    session.commit()

if __name__ == '__main__':
    baseFolder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    sys.path.insert(0, baseFolder)
    import config

    print 'Test runner is running from', baseFolder
    print 'cwd is', os.getcwd()
    print 'on branch', subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()

    testProject = os.path.dirname(baseFolder) + '/WebPlatformTest'
    sys.path.insert(0, testProject)
    print 'Tests are running in', testProject
    oldDir = os.getcwd()
    os.chdir(testProject)

    if config.TEST_DB_FILE == '../WebPlatform/local_tests.sqlite':
        # Put results in WebPlatform so they will get sync'd to mudge.dev.8i.com for viewing.
        localTesting = os.path.dirname(baseFolder) + '/WebPlatform'
        engine = create_engine('sqlite:///' + localTesting + '/local_tests.sqlite')
        print 'Test results are in ', localTesting + '/local_tests.sqlite'
    else:
        engine = create_engine('sqlite:///' + testProject + '/local_tests.sqlite')
        print 'Test results are in ', testProject + '/local_tests.sqlite'

    d = os.getcwd()
    if d != testProject:
        print "Not in testProject.", d
        exit(1)
    originalBranch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()

    if originalBranch != 'master':
        print "Not in master branch, not doing anything.", d, originalBranch
        exit(1)

    try:
        print "git pull"
        output = subprocess.check_output(["git", "pull"])
        # TODO if this branch updates we should re test all?
        # This is the test runner branch so only need to if one of the test running files updates?
        print output
    except subprocess.CalledProcessError as e:
        # I don't think this matters much as it only means that this file is not going to be updated.
        print "Failed to update the test runner branch"

    # if returncode != 0:
    #     print "git pull failed with error code %s" % returncode

    # Clean up old branches locally and on remote.
    cleanUp()

    if "reset" in sys.argv:
        print "Wiping database of all test results due to reset arg."
        Base.metadata.drop_all(engine)

    # Always create all, incase none exist.
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    dbBranches = {b.name: b for b in session.query(Branch).all()}
    print "db branches = ", [str(b) for b in list(dbBranches)]

    branches = subprocess.check_output(["git", "branch", "-r"]).strip()
    # split on whitespace and ignore origin/HEAD -> origin/master
    branches = branches.replace('origin/HEAD -> origin/master', '').split()

    # Some branches get out of date and no longer run.
    branches = [b[7:] for b in branches if b not in config.TEST_EXCLUDE_BRANCHES]
    print 'found branches', branches

    force = "force" in sys.argv

    testBranches = []
    for branchName in branches:
        # Remove origin/ from the branch name.
        dbBranch = dbBranches.get(branchName)
        if not dbBranch:
            dbBranch = Branch(name=branchName)

        if force or check_status(dbBranch):
            testBranches.append(dbBranch)

    errorOccured = False
    for branch in testBranches:
        try:
            test_branch(branch)
        except Exception as e:
            errorOccured = True
            print e

    print "git checkout master"
    output = subprocess.check_output(["git", "checkout", "master"])
    print output

    # Update database with merged branches.
    for key, branch in dbBranches.iteritems():
        if (branch.name not in branches):
            if not branch.merged:
                print branch.name, "marked as merged"
            branch.merged = True
        else:
            branch.merged = False
    session.commit()

    os.chdir(oldDir)

    if errorOccured:
        # Will cause cron to fail and send logs.
        exit(1)
