#!/bin/bash

cd /Users/mudge/projects/AutoTest
# This has to happen in a bash script, python subprocess doesn't support source.
source /Users/mudge/projects/virtualenv/WebPlatform/bin/activate > /dev/null 2>&1

# Optionally could pull here so we always run the most up to date version of the test runner.

python record_tests.py >> automatic_tests.log 2>&1
STATUS_CODE=$?

if [ $STATUS_CODE -ne 0 ]
then
  echo "It all went horribly wrong" $STATUS_CODE >&2
  cat automatic_tests.log >&2
fi
