#!/bin/bash

# Sets various dev settings on a Moodle instance

if ! moodle environment check > /dev/null; then
	echo "You first have to set your environment."
	echo "Run moodle environment check"
	exit 10
fi

SETTING_DIR="$HOME/.moodle"
DIR=`pwd`

# Check that current directory is a Moodle instance
if ! moodle info -q; then
	exit $?
fi

# Database settings
if [ ! -f "$SETTING_DIR/install.sql" ]; then
	echo "Missing SQL file: $SETTING_DIR/install.sql"
	exit 1
fi

echo "Setting up developer mode..."
DBNAME=`moodle info dbname`
DBTYPE=`moodle info dbtype`
DBUSER=`moodle info dbuser`
DBPASS=`moodle info dbpass`
DEBUG_DEVELOPER=`cat lib/setuplib.php lib/moodlelib.php | grep -E "define ?\('DEBUG_DEVELOPER" | cut -d "," -f 2 | cut -d ")" -f 1`;
DEBUG_DEVELOPER=`php -r "echo $DEBUG_DEVELOPER;"`

case "$DBTYPE" in

	"mysqli" )
		cat "$SETTING_DIR/install.sql" | sed "s/DEBUG_DEVELOPER/$DEBUG_DEVELOPER/" | mysql -u$DBUSER -p$DBPASS $DBNAME
		;;

	* )
		echo "Database type not supported!"
		exit 2
		;;
esac