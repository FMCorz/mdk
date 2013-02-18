#!/bin/bash
#
# Automatically rebases an issue, and pushes it to Github
# /!\ The Github push will be forced
#
# 1st argument      the issue
# other arguments   the branches (testing_22, stable_master, ...)

if ! moodle environment; then
    exit 32;
fi

MDL="$1"
LENGTH=$(($#-1))
INST=${@:2:$LENGTH}

for I in $INST
do
    echo "> $I <"

    DIR="$MOODLE_DIR_REPOSITORIES/$I/moodle"
    if [ ! -d "$DIR" ]; then
        echo "Could not find directory for $I"
        continue
    fi
    cd "$DIR"

    if ! git fix "$MDL" --checkout-only > /dev/null 2>&1; then
        echo "Error while checking out branch. Skipping!"
        continue
    fi

    echo "Rebasing..."
    git fetch origin > /dev/null

    if git rebase > /dev/null; then
        echo "Pushing to Github (force)..."
        moodle push-github -f > /dev/null 2>&1
    else
        echo "Rebase needs merging. Please manually rebase and push."
    fi
    echo
done