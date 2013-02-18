#!/bin/bash

# First param is:
# - <empty>         current directory is updated
# - 'all'           all Moodle instances are updated
# - dir             only that instance is updated

MODE="$1"

if [ "$MODE" == "all" ]; then
    if ! moodle environment > /dev/null; then
        echo "Moodle environment not set!"
        exit 2;
    fi;
    DIRS=`ls "$MOODLE_DIR_WWW"`
elif moodle environment && [ -n "$MODE" ] && [ -d "$MOODLE_DIR_WWW/$MODE" ]; then
    DIRS="$MOODLE_DIR_WWW/$MODE"
elif [ -d "`readlink -f \"$MODE\"`" ]; then
    DIRS="`readlink -f \"$MODE\"`"
else
    DIRS=`pwd`
fi

for DIR in $DIRS
do

    if [ "$MODE" == "all" ]; then
        DIR="$MOODLE_DIR_WWW/$DIR"
    fi

    if [ ! -d "$DIR" ]; then
        continue
    fi

    # Change directory
    cd "$DIR"

    BRANCH=`moodle info stablebranch 2> /dev/null`
    if [ $? != 0 ]; then
        if [ "$MODE" != 'all' ]; then
            # Exits when we were not updating all
            exit 1;
        fi
        # Skip silently when updating all
        continue
    fi

    echo "Updating $DIR..."

    if [ "`moodle info gitbranch`" != "$BRANCH" ]; then
        git checkout "$BRANCH"
    fi

    git pull # -q

    if [ -f "$DIR/admin/cli/upgrade.php" ]; then
        php "$DIR/admin/cli/upgrade.php" --non-interactive --allow-unstable
    fi

    if [ "$MODE" == "all" ]; then
        echo
    fi

done

if [ "$MODE" == "all" ]; then
    echo "Update complete!"
fi

exit 0;