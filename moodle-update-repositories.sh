#!/bin/bash

#
# Updates the cached repositories
#

if ! moodle environment > /dev/null; then
    echo "Moodle environment not set!"
    exit 2;
fi;

STABLE="$HOME/.moodle/moodle.git"
INTEGRATION="$HOME/.moodle/integration.git"
if [ ! -d "$STABLE" ] || [ ! -d "$INTEGRATION" ]; then
    echo "Missing repositories in ~/.moodle/"
    exit 1;
fi

for D in "$STABLE" "$INTEGRATION"
do
    cd $D
    echo "Updating $D..."
    git fetch origin #> /dev/null
    BRANCHES=`git show-ref | grep 'origin/' | cut -d ' ' -f 2`

    for B in $BRANCHES
    do
        B="${B##refs/remotes/origin/}"
        if [[ $B == "HEAD" ]]; then
            continue
        fi

        # Creating the branch if not exist
        if ! git show-ref --verify --quiet refs/heads/$B; then
            git branch --track $B origin/$B #> /dev/null
        fi

        # Checkout and update
        git checkout $B #> /dev/null 2>&1
        git reset --hard origin/$B #> /dev/null
    done

done

exit 0;