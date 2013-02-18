#!/bin/bash
# This script creates a branch based on the issue number and version to be fixed
#
# 1st argument      the issue number
# 2nd argument      the version to fix (master, 22, 21, ...)
# 3rd argument      a suffix to the branch name

if ! moodle info -q; then
    exit 32;
fi

if [ $# -lt 1 ]; then
    echo "Missing arguments"
    exit 1
fi

MDL="${1##MDL-}"
ISSUE="MDL-${MDL}"
EXTRA="$2"

# Checkout only?
CHECKOUTONLY=false
if [[ "$@" == *"--checkout-only"* ]]; then
    CHECKOUTONLY=true
fi

VERSION=`moodle info stablebranch 2> /dev/null`
if [ -z "$VERSION" ]; then
    echo "Could not identify Moodle stable branch"
    exit 3
fi

if [ "$VERSION" == "master" ]; then
    BRANCH="master"
else
    BRANCH=`moodle info branch 2> /dev/null`
fi

if [ -z "$BRANCH" ]; then
    echo "Could not identify Moodle branch"
    exit 4
fi
BRANCH="${ISSUE}-${BRANCH}"


if [ -n "$EXTRA" ] && [[ "$EXTRA" != "--"* ]]; then
    BRANCH="$BRANCH-$EXTRA"
fi

REMOTE="origin/$VERSION"

# Create branch if it does not exist
if ! `git show-ref --verify --quiet "refs/heads/$BRANCH"` && ! $CHECKOUTONLY; then
    git branch --track "$BRANCH" "$REMOTE"
fi

git checkout "$BRANCH"
exit $?