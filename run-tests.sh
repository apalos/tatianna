#!/bin/bash

# Run tests
TEST_ENV=tests-env
if [ -d "${TEST_ENV}" ]; then
        echo tests-exists
else
        virtualenv ${TEST_ENV}
        ${TEST_ENV}/bin/pip install -r test-requirements.txt
fi
# clear old tests
rm -f *.xml

${TEST_ENV}/bin/nosetests --with-xunit

