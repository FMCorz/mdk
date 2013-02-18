#!/bin/bash

# Shows information about a Moodle instance

if [ -z "$2" ]; then
    ARG="$1"
    DIR=`pwd`
else
    DIR="$1"
    ARG="$2"
    if [ -d "$MOODLE_DIR_WWW/$DIR" ]; then
        DIR="$MOODLE_DIR_WWW/$DIR"
    fi
fi

REALPATH=`readlink -f "$DIR"`
ARG=`echo $ARG | tr '[:lower:]' '[:upper:]'`

if [ ! -f "$DIR/version.php" ] || [ -z "`grep "MOODLE VERSION INFORMATION" \"$DIR/version.php\"`" ] ; then
    echo "$DIR does not appear to be the root of a Moodle installation directory" >&2
    exit 32;
fi

# Exit silently if first argunent is -q
if [ "$1" == "-q" ]; then
    exit 0;
fi

# Reading information from Moodle
cd "$DIR"
BRANCH=`grep -E "branch\s*=" "$DIR/version.php" | sed -n -e "s/.*= '\([0-9]\+\)'.*/\1/p"`
VERSION=`grep -E "version\s*=" "$DIR/version.php" | sed -n -e "s/.*= \([0-9.]\+\).*/\1/p"`
RELEASE=`grep -E "release\s*=" "$DIR/version.php" | sed -n -e "s/.*= '\(.\+\)'.*/\1/p"`
MATURITY=`grep -E "maturity\s*=" "$DIR/version.php" | sed -n -e "s/.*= MATURITY_\([A-Z]\+\).*/\1/p"`
DATAROOT=`grep -E "CFG->dataroot\s*=" "$DIR/config.php" | sed -n -e "s/.*= '\(.\+\)'.*/\1/p"`
DBTYPE=`grep -E "CFG->dbtype\s*=" "$DIR/config.php" | sed -n -e "s/.*= '\([a-z]\+\)'.*/\1/p"`
DBHOST=`grep -E "CFG->dbhost\s*=" "$DIR/config.php" | sed -n -e "s/.*= '\(.\+\)'.*/\1/p"`
DBUSER=`grep -E "CFG->dbuser\s*=" "$DIR/config.php" | sed -n -e "s/.*= '\(.\+\)'.*/\1/p"`
DBPASS=`grep -E "CFG->dbpass\s*=" "$DIR/config.php" | sed -n -e "s/.*= '\(.\+\)'.*/\1/p"`
DBNAME=`grep -E "CFG->dbname\s*=" "$DIR/config.php" | sed -n -e "s/.*= '\(.\+\)'.*/\1/p"`
GITBRANCH=`moodle current-branch`
GITORIGIN=`git config --get remote.origin.url 2> /dev/null`

if [[ $GITORIGIN = *'integration.git' ]]; then
    MODE='testing'
else
    MODE='stable'
fi

# If branch is not set, we generate it
if [ -z "$BRANCH" ]; then
    BRANCH=`echo "$RELEASE" | sed 's/\.//g' | cut -c 1-2`
fi

# Generates the stable branch
STABLEBRANCH="MOODLE_${BRANCH}_STABLE"
if ! git show-ref --verify --quiet refs/heads/$STABLEBRANCH; then
    STABLEBRANCH="master"
fi

# Outputs information
if [ ! -z "$ARG" ]; then
    echo ${!ARG}
else
    echo "origpath: $DIR"
    echo "realpath: $REALPATH"
    echo "dataroot: $DATAROOT"
    echo "branch: $BRANCH"
    echo "version: $VERSION"
    echo "release: $RELEASE"
    echo "maturity: $MATURITY"
    echo "dbtype: $DBTYPE"
    echo "dbhost: $DBHOST"
    echo "dbuser: $DBUSER"
    echo "dbpass: $DBPASS"
    echo "dbname: $DBNAME"
    echo "gitbranch: $GITBRANCH"
    echo "gitorigin: $GITORIGIN"
    echo "mode: $MODE"
    echo "stablebranch: $STABLEBRANCH"
fi

exit 0