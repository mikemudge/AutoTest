import auto_config
import os
import sys
import test_models

from flask import abort
from test_models import Branch, TestRun
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

testProject = os.path.join(auto_config.PROJECT_PATH, auto_config.TEST_DB_FILE)
engine = create_engine('sqlite:///' + testProject)
Session = sessionmaker(bind=engine)

def getTestRuns():
    session = Session()
    # TODO query grouped on branch?
    branches = session.query(Branch).filter_by(merged=False).all()
    result = []
    for branch in branches:
        b = test_models.simpleSerialize(branch)
        b['runs'] = [test_models.simpleSerialize(t) for t in branch.runs]
        result.append(b)
    return result

def getTestRun(test_run_id):
    session = Session()
    testRun = session.query(TestRun).get(test_run_id) or abort(404)

    data = test_models.simpleSerialize(testRun)
    data['results'] = [test_models.simpleSerialize(t) for t in testRun.results]
    return data

# TODO this is getting overwritten by the version on my local machine, so its not helping?
def saveBranch(branch_id, updateData):
    session = Session()
    branch = session.query(Branch).get(branch_id) or abort(404)
    # Only updatable field.
    branch.force_run = updateData['force_run']
    session.merge(branch)
    session.commit()
    session.flush()
    session.refresh(branch)
    result = test_models.simpleSerialize(branch)
    return result

def show_test_results():
    session = Session()
    print 'Displaying results in', testProject

    branches = session.query(Branch).filter_by().all()
    print "%r Branches" % len(branches)

    for branch in branches:
        if branch.merged:
            continue
        latestTestRun = branch.runs.order_by(desc(TestRun.created_date)).first()
        print "Branch: %s - %r test runs" % (branch.name, branch.runs.count())
        print "force_run", branch.id, branch.force_run
        print "latest run - failures: %r, errors: %r" % (latestTestRun.failure_count, latestTestRun.error_count)
        print ""

if __name__ == '__main__':
    if 'force_run' in sys.argv:
        saveBranch(2, {'force_run': True})
    show_test_results()
