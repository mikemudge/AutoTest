from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

Base = declarative_base()

# A test run is a set of independent tests which were run together on the same code.
class TestRun(Base):
    __tablename__ = 'test_run'

    id = Column(Integer, primary_key=True)

    # Git branch which this test was run on.
    branch_id = Column(Integer, ForeignKey("branch.id"))
    branch = relationship('Branch', backref=backref('runs', lazy='dynamic'))

    # Git commit hash which this test was run on.
    commit_hash = Column(String)

    test_count = Column(Integer)
    error_count = Column(Integer)
    failure_count = Column(Integer)

    created_date = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "%s @ %s" % (self.branch, self.created_date.strftime("%Y-%m-%d %H:%M:%S"))

# A test result is the result of a single test.
class TestResult(Base):
    __tablename__ = 'test_result'

    id = Column(Integer, primary_key=True)

    test_run_id = Column(Integer, ForeignKey("test_run.id"))
    test_run = relationship('TestRun', backref=backref('results', lazy='dynamic'))
    # The path to the test which will be something like module.file.test
    path = Column(String)
    # one of success, failure or error
    result = Column(String)
    # The failure/error message if the test was not a success.
    message = Column(String)

    def __repr__(self):
        return "%s %s" % (self.path, self.result)

class Branch(Base):
    __tablename__ = 'branch'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    # If the branch has been merged, there will be no further tests run on it.
    merged = Column(Boolean, default=False)
