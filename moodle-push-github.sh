#!/bin/bash
# Pushes the current branch to Github
# If found pushes the upstream branch too

if ! moodle info -q; then
    exit 32;
fi

CB=`moodle current-branch`
echo "Pushing $CB to github"
git push github $CB $1

UB=`moodle upstream $CB`
if [ ! -z "$UB" ]; then
    echo "Pushing upstream branch $UB to github"
    git push github $UB
fi