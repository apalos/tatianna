#!/bin/bash

# This is a sticky sha of python-ircd that is known and tested
SHA=0c70c0475ff0659f185660e49feb29a58042e42b

if [ ! -d "tests-env" ]; then 
    echo create tests-env first by running "run-tests.sh"
    exit 1
fi

if [ ! -d tests-env/python-ircd ]; then 
    git clone https://github.com/abesto/python-ircd.git tests-env/python-ircd
    pushd tests-env/python-ircd
        git checkout -b tatianna-sticky $SHA

        ../bin/pip install -r requirements_python2.txt
        ../bin/pip install -r requirements_common.txt
    popd
fi

pushd tests-env/python-ircd
    echo Starting server, redirecting logs to tests-env/python-ircd/server.log
    ../bin/python application.py | while read x; do printf "[31m%s\n[0;0m[36;1m" "$x"   ; done & 
popd

echo "Start your IRC client on localhost 6667 (sleep 15s)"
sleep 15
echo Starting bot
sleep 5
tput setaf 2
tests-env/bin/python core/bot.py --server localhost -p 6667 -c test  

kill %
echo '[0m;0m'


