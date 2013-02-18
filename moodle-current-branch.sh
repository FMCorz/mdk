#!/bin/sh
echo $(b=$(git symbolic-ref -q HEAD 2> /dev/null); { [ -n "$b" ] && echo ${b##refs/heads/}; } || echo HEAD)
