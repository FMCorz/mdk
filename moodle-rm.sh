#!/bin/bash

# Entirely remove an instance of Moodle
#
# First param is the name of the instance

if ! moodle environment check > /dev/null; then
    echo "You first have to set your environment."
    echo "Run moodle environment check"
    exit 10
fi

INSTANCE="$1"
ROOT="$MOODLE_DIR_REPOSITORIES/$INSTANCE"
DIR="$ROOT/moodle"

if [ -z "$INSTANCE" ] || [ ! -d "$ROOT" ]; then
    echo "Unknown instance name"
    exit 1
fi

echo "This will entirely the instance located in $ROOT"
echo -n "Are you sure (y/N)? "
read -n 1 AREYOUSURE
echo
if [ "$AREYOUSURE" != "y" ]; then
    echo "Exiting..."
    exit 0
fi

echo "Removing $INSTANCE"

DATAROOT=`moodle info $DIR dataroot 2>&1 /dev/null`
DBTYPE=`moodle info $DIR dbtype`
DBUSER=`moodle info $DIR dbuser`
DBPASS=`moodle info $DIR dbpass`
DBNAME=`moodle info $DIR dbname`

echo "Deleting $ROOT..."
rm -rf "$ROOT"
if [ -f "$MOODLE_DIR_WWW/$INSTANCE" ] || [ -h "$MOODLE_DIR_WWW/$INSTANCE" ]; then
    rm "$MOODLE_DIR_WWW/$INSTANCE"
fi

# Database
case "$DBTYPE" in

    "mysqli" )
        echo "Dropping database '$DBNAME'"
        mysql -u$DBUSER -p$DBPASS -e "DROP DATABASE $DBNAME" > /dev/null 2>&1
    ;;

    "pgsql" )
        echo "Database type '$DBTYPE' not supported"
        echo "Please manually remove '$DBNAME'"
    ;;

esac

exit 0