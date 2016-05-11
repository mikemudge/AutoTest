import sys
import os

# Include the parent folder so we can use python modules like "tests"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import models
from flask import abort
from tests.record_results import engine, Base, Branch, TestResult, TestRun, Session
from sqlalchemy import desc, func
from datetime import datetime

def show_test_results():
    session = Session()

    print datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    testRuns = session.query(TestRun).count()
    print "%r test runs" % testRuns

    latestTestRun = session.query(TestRun).order_by(desc(TestRun.created_date)).limit(1).first()
    if latestTestRun:
        print "Latest Run: %r" % latestTestRun
        for testResult in latestTestRun.results:
            print "{0:90} {1}".format(testResult.path, testResult.result)

    testProblems = session.query(TestResult.path, TestResult.result, func.count(TestResult.id)).filter(TestResult.result != "success").group_by(TestResult).all()

    print "%r failures" % len(testProblems)
    for testResult in testProblems:
        print testResult[0], testResult[1], testResult[2], testResult[3].strftime("%Y-%m-%d %H:%M:%S")

def getTestRuns():
    session = Session()
    # TODO query grouped on branch?
    branches = session.query(Branch).all()
    result = []
    for branch in branches:
        b = models.simpleSerialize(branch)
        b['runs'] = [models.simpleSerialize(t) for t in branch.runs]
        result.append(b)
    return result

def getTestRun(test_run_id):
    session = Session()
    testRun = session.query(TestRun).get(test_run_id) or abort(404)

    data = models.simpleSerialize(testRun)
    data['results'] = [models.simpleSerialize(t) for t in testRun.results]
    return data

if __name__ == '__main__':
    # Create table if it doesn't exist
    Base.metadata.create_all(engine)

    show_test_results()

# rsync -a /Users/mudge/projects/WebPlatform/ mudge@mudge.dev.8i.com:/home/mudge/projects/WebPlatformTest --exclude="*.log" --exclude="local_tests.sqlite"
