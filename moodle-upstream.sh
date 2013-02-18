#!/bin/bash
# Returns the upstream branch of the current, or specified branch
#
# 1st argument      the branch (optional)

if ! moodle info -q; then
    exit 32;
fi

BRANCH="$1"
if [ -z "$BRANCH" ]; then
    BRANCH=`moodle current-branch`
fi

# 1st attempt to get the upstream branch
UB=$(git config --get branch.$BRANCH.merge)
UB=${UB##refs/heads/}

# 2nd attempt to get the upstream branch
if [ -z "$UB" ]; then
    V=`echo "$BRANCH" | sed -n -e 's/MDL-[0-9]\+-\([0-9a-zA-Z]\+\).*/\1/p'`
    UB='master'
    if [ "$V" != "master" ]; then
        UB="MOODLE_${V}_STABLE"
    fi
fi

echo "$UB"