#!/bin/bash

# Get PID and Kill it in one line
ps -ef | grep "funasr" | grep -v grep | awk '{print $2}' | xargs kill -9

cd /workspace/FunASR/runtime

bash run_server.sh --certfile 0 > /dev/stdout

tail -f /dev/stdout