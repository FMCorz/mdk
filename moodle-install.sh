#!/bin/bash

# Installs a new instance of Moodle
#
# First param is the type of instance (stable/testing)
# Second param is the version to checkout (21, 22, ..., master)
# Third param is a suffix for the directory name(psql, MDL-12345, ...)

if ! moodle environment check > /dev/null; then
	echo "You first have to set your environment."
	echo "Run moodle environment check"
	exit 10
fi

ERASE_OLD_DIR=false
ERASE_OLD_DB=false
INTERACTIVE=true
INSTALL=true
PHPUNIT_INIT=false
GEN_CTAGS=true
SET_DEVMOVE=true

CTAGS="ctags -R --languages=php --exclude='CVS' --php-kinds=f --regex-PHP='/abstract class ([^ ]*)/\1/c/' --regex-PHP='/class ([^ ]+)/\1/c/' --regex-PHP='/interface ([^ ]*)/\1/c/' --regex-PHP='/(public |static |abstract |protected |private )+function ([^ (]*)/\2/f/'"
PHPCLI="/usr/bin/php"

# End of configuration

if [ $# -lt 2 ]; then
	echo "Missing arguments"
	exit 2
fi

SETTING_DIR="$HOME/.moodle"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TYPE=$1
VERSION=$2
LOCAL_VERSION=$3

# Cloning Git repositories to prevent long cloning in the future
if [ ! -d "$SETTING_DIR/moodle.git" ]; then
	echo "Cloning Moodle Git repository <$MOODLE_STABLE>"
	cd "$SETTING_DIR"
	git clone "$MOODLE_STABLE" "moodle.git"
	cd "$SETTING_DIR/moodle.git"
	echo "Adding Github remote <$MOODLE_GITHUB>"
	git remote add github $MOODLE_GITHUB
fi
if [ ! -d "$SETTING_DIR/integration.git" ]; then
	echo "Cloning Integration Git repository <$MOODLE_INTEGRATION>"
	cd "$SETTING_DIR"
	git clone "$MOODLE_INTEGRATION" "integration.git"
	cd "$SETTING_DIR/integration.git"
	echo "Adding Github remote <$MOODLE_GITHUB>"
	git remote add github $MOODLE_GITHUB
fi

case "$TYPE" in

	"stable" )

		NAME="stable_${VERSION}"
		FULLNAME="Stable ${VERSION}"
		if [ -n "$LOCAL_VERSION" ]; then
			NAME="${NAME}_${LOCAL_VERSION}"
			FULLNAME="${NAME} (${LOCAL_VERSION})"
		fi
		REPOSITORY="$SETTING_DIR/moodle.git"

		;;

	"testing" )

		NAME="testing_${VERSION}"
		FULLNAME="Testing ${VERSION}"
		if [ -n "$LOCAL_VERSION" ]; then
			NAME="${NAME}_${LOCAL_VERSION}"
			FULLNAME="${NAME} (${LOCAL_VERSION})"
		fi
		REPOSITORY="$SETTING_DIR/integration.git"

		;;

	* )

		echo "Unknown installation type. Exiting..."
		exit 10;

		;;

esac

INSTALL_DIR="$MOODLE_DIR_REPOSITORIES/$NAME"
if [ -d "$INSTALL_DIR" ]; then
	echo "Installation directory exists"
	if $INTERACTIVE; then
		echo -n "Would you like to delete '$INSTALL_DIR' (y/N)? "
		read -n 1 DELETE_OLD
		echo
		if [ "$DELETE_OLD" == "y" ]; then
			ERASE_OLD_DIR=true
		fi
	fi
	if $ERASE_OLD_DIR; then
		echo "Removing directory..."
		rm -rf "$INSTALL_DIR"
		rm "$MOODLE_DIR_WWW/$NAME"
	else
		echo "Exiting"
		exit 1
	fi
fi

DBEXISTS=`mysql -u$MOODLE_DB_MYSQL_USER -p$MOODLE_DB_MYSQL_PWD -e "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '$NAME'"`
if [ -n "$DBEXISTS" ]; then
	echo "Database already exists"
	if $INTERACTIVE; then
		echo -n "Would you like to delete '$NAME' (y/N)? "
		read -n 1 DELETE_OLD
		echo
		if [ "$DELETE_OLD" == "y" ]; then
			$ERASE_OLD_DB=false
		fi
	fi
	if $ERASE_OLD_DB; then
		echo "Removing database..."
		mysql -u$MOODLE_DB_MYSQL_USER -p$MOODLE_DB_MYSQL_PWD -e "DROP DATABASE $NAME" > /dev/null 2>&1
	else
		echo "Exiting"
		exit 1
	fi
fi

echo "Installing $NAME..."

mkdir -p "$INSTALL_DIR/moodledata"
chmod 0777 "$INSTALL_DIR/moodledata"
cp -r "$REPOSITORY" "$INSTALL_DIR/moodle"
cd "$INSTALL_DIR/moodle"
ln -s "$INSTALL_DIR/moodle" "$MOODLE_DIR_WWW/$NAME"

git fetch origin > /dev/null 2>&1
if [ "$VERSION" == "master" ]; then
	git checkout -b master "origin/master" > /dev/null 2>&1
else
	git checkout -b "MOODLE_${VERSION}_STABLE" "origin/MOODLE_${VERSION}_STABLE" > /dev/null 2>&1
fi
git pull > /dev/null 2>&1

# Passively generating CTags
if $GEN_CTAGS; then
	echo "Generating CTags..."
	cd "$INSTALL_DIR/moodle"
	$CTAGS 2>&1 /dev/null
fi

# Launching installation process
if $INSTALL; then

	cd "$INSTALL_DIR/moodle"
	$PHPCLI admin/cli/install.php --wwwroot="http://$MOODLE_HOSTNAME/$NAME/" --dataroot="$INSTALL_DIR/moodledata" --dbtype="mysqli" --dbname="$NAME" --dbuser="$MOODLE_DB_MYSQL_USER" --dbpass="$MOODLE_DB_MYSQL_PWD" --dbhost="$MOODLE_DB_MYSQL_HOST" --fullname="$FULLNAME" --shortname="$NAME" --adminuser="$MOODLE_ADMIN_USER" --adminpass="$MOODLE_ADMIN_PWD" --allow-unstable --agree-license --non-interactive
	echo -e "\n\$CFG->sessioncookiepath = '/$NAME/';" >> "$INSTALL_DIR/moodle/config.php"
	chmod +r "$INSTALL_DIR/moodle/config.php"
	echo "Installation complete!"

	# Post-installation set dev mode
	if $SET_DEVMOVE; then
		moodle dev
	fi

fi

# Initialise PHPUnit
if $PHPUNIT_INIT; then
	echo "Initiating PHPUnit..."
	cd $INSTALL_DIR/moodle
	moodle phpunit 2>&1 /dev/null
fi
