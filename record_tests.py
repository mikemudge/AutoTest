import os
import subprocess
import sys
import traceback

from datetime import datetime
from test_models import Base, Branch, TestResult, TestRun
from run_tests import test_client, test_server
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

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
        if (len(tests) != len(results)):
            print "something went wrong", len(tests), len(results)
    print "clientResults processed, totalLength:", len(results)

    for test in serverResults:
        testName = "%s.%s.%s" % (test['module'], test['name'], test['method'])
        result = TestResult(result=test['result'], path=testName)
        if not test.get('success', False):
            failure_count += 1
        if 'failure' in test:
            # TODO format this nicer, its an AssertionError.
            result.message = str(test['failure'])
        # TODO error count?
        results[testName] = result
    print "serverResults processed, totalLength:", len(results)

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
    return run_all_tests(branch, commit_hash)

def run_tests(testBranches):
    print "Testing branches", [t.name for t in testBranches]

    errorOccured = False
    testRuns = []
    for branch in testBranches:
        try:
            testRun = test_branch(branch)
            print "db rows created, totalLength:", testRun.results.count()
            testRuns.append(testRun)
        except Exception as e:
            errorOccured = True
            print e
            traceback.print_exc()

    # Return to master branch.
    print "git checkout master"
    output = subprocess.check_output(["git", "checkout", "master"])
    print output

    if errorOccured:
        raise Exception("There was an error during testing")
    return testRuns

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

def check_status(branch, session):
    if branch.name.startswith('origin/'):
        print "Bad branch", branch.name, branch.id
        exit(1)

    branchName = branch.name

    if not branch.id:
        print "%s - New Branch, running all tests." % branchName
        return True

    latestTestRun = session.query(TestRun).filter(TestRun.branch == branch).order_by(desc(TestRun.created_date)).limit(1).first()
    if not latestTestRun:
        print "%s - No previous test run, running all tests." % branchName
        # Need to run the tests.
        return True

    if branch.force_run:
        # No testing required?
        print "%s - run forced by force_run=True, running all tests." % branchName
        branch.force_run = False
        session.commit()
        return True

    commit_hash = subprocess.check_output(["git", "rev-parse", "origin/%s" % branchName]).strip()
    if latestTestRun.commit_hash == commit_hash:
        # No testing required?
        print "%s - Commit hashes match, not testing" % branchName
        return False

    print "%s - New commit hash, running all tests." % branchName
    return True

def test_project(testProject, session):
    d = os.getcwd()
    if d != testProject:
        print "Not in testProject.", d
        exit(1)

    # Do test stuff.
    originalBranch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()

    if originalBranch != 'master':
        print "Not in master branch, not doing anything.", testProject, originalBranch
        exit(1)

    try:
        # Update the testProject branches.
        print "git pull"
        subprocess.check_output(["git", "pull"])
        # This will update the commit hashes for all branches known to the test project.
    except subprocess.CalledProcessError as e:
        print e
        print "Failed to update the test project branch"
        # As the commit hashes won't be updated, I don't think any tests will actually run?

    # Clean up old branches locally and on remote.
    cleanUp()

    dbBranches = {b.name: b for b in session.query(Branch).all()}
    print "db branches =", [str(v.id) + "-" + str(b) for b, v in dbBranches.iteritems()]
    print [v.force_run for b, v in dbBranches.iteritems()]

    branches = subprocess.check_output(["git", "branch", "-r"]).strip()
    # split on whitespace and ignore origin/HEAD -> origin/master
    branches = branches.replace('origin/HEAD -> origin/master', '').split()

    # Some branches get out of date and no longer run.
    # TODO Assuming all branches start with origin/ is a bit near sighted.
    branches = [b[7:] for b in branches if b not in auto_config.TEST_EXCLUDE_BRANCHES]
    print 'current branches', [b for b in branches]

    # Update database with merged branches.
    for key, branch in dbBranches.iteritems():
        if (branch.name not in branches):
            if not branch.merged:
                print branch.name, "marked as merged"
            branch.merged = True
        else:
            branch.merged = False

    force = "force" in sys.argv

    testBranches = []
    if "single" in sys.argv:
        testBranches = [dbBranches.get("master", Branch(name="master"))]
    else:
        for branchName in branches:
            # Remove origin/ from the branch name.
            dbBranch = dbBranches.get(branchName)
            if not dbBranch:
                dbBranch = Branch(name=branchName)

            if force or check_status(dbBranch, session):
                testBranches.append(dbBranch)

    if "skiptests" in sys.argv:
        print "skipping testing", [t.name for t in testBranches]
        session.commit()
        return

    testRuns = run_tests(testBranches)

    if len(testBranches) == 0:
        print "No branches require testing"
    elif not testRuns or len(testRuns) == 0:
        print "No test runs?"
    for testRun in testRuns:
        print "adding test run for", testRun.branch.name
        session.add(testRun)

    try:
        session.commit()
        # Saw a disk I/O error once, not sure how they happen.
    except OperationalError as e:
        # Try again.
        print "Got error during commit, trying again:", e
        session.commit()

def create_db_session(testProject):
    if os.path.isabs(auto_config.TEST_DB_FILE):
        localTests = auto_config.TEST_DB_FILE
    else:
        localTests = testProject + auto_config.TEST_DB_FILE

    engine = create_engine('sqlite:///' + localTests)
    print 'Test results are in ', localTests

    if "reset" in sys.argv:
        print "Wiping database of all test results due to reset arg."
        Base.metadata.drop_all(engine)

    # Always create all, incase none exist.
    # If it doesn't match then we should migrate?
    # New tables are easy, sohuld just work with this.
    # new columns are more tricky and not automatically supported.
    # Removing isn't supported.
    Base.metadata.create_all(engine)

    if "upgradedb" in sys.argv:
        # Iterate tables and there columns to see if there is some new things.
        from sqlalchemy import MetaData
        print Base.metadata
        metadata = MetaData()
        metadata.reflect(engine)
        # Iterate all tables and columns and make sure they all exist.
        # TODO works for simple types, but not throughly tested.
        for t in Base.metadata.sorted_tables:
            t2 = metadata.tables[t.name]
            print "Table", t.name, t2.name
            for c in t.columns:
                # This has force_run because its generated from the classes.
                print c.name
                if c.name not in t2.columns:
                    print "need to add ", c.name, "with type", c.type
                    format_str = ("ALTER TABLE '{table_name}' ADD column '{column_name}' '{data_type}'")
                    sql_command = format_str.format(table_name=t.name, column_name=c.name, data_type=c.type)
                    engine.execute(sql_command)

    Session = sessionmaker(bind=engine)
    session = Session()
    return session

if __name__ == '__main__':
    import auto_config

    branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
    print 'Test runner is running from', os.getcwd(), 'on branch', branch
    print 'Tests run at', datetime.now()
    # The test runner is currently only manually updated.

    testProject = auto_config.PROJECT_PATH
    sys.path.insert(0, testProject)
    print 'Tests are running in', testProject
    oldDir = os.getcwd()
    os.chdir(testProject)

    # try:
    session = create_db_session(testProject)
    test_project(testProject, session)
    # except Exception as e:
    #     os.chdir(oldDir)
    #     raise e

    os.chdir(oldDir)
