#!/bin/bash

ACTION=$1

if [ -z "$ACTION" ] || [ -z `which moodle-$ACTION` ]; then
    echo "Unknown command"
    exit 1;
fi

moodle-$ACTION ${@:2}
