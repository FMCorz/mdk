#!/bin/bash

DIR=`pwd`
REALPATH=`readlink -f "$DIR"`
BACKUP_DIRECTORY="$HOME/.moodle/backup"
INFO_FILE="backup.txt"
DB_FILE="backup.db"
IDENTIFIER=$1;

if ! moodle info -q; then
    exit 32;
fi

# Reading information from Moodle
BRANCH=`moodle info branch`
VERSION=`moodle info version`
RELEASE=`moodle info release`
MATURITY=`moodle info maturity`
DATAROOT=`moodle info dataroot`
DBTYPE=`moodle info dbtype`
DBHOST=`moodle info dbhost`
DBUSER=`moodle info dbuser`
DBPASS=`moodle info dbpass`
DBNAME=`moodle info dbname`
GITBRANCH=`git cb`
GITORIGIN=`git config --get remote.origin.url`
MODE=`moodle info mode`

# If identifier is empty, we create it
if [ -z "$IDENTIFIER" ]; then
    IDENTIFIER="$MODE-$BRANCH-$MATURITY-${VERSION}_$(date +%Y-%m-%d-%H-%M-%I)"
fi

# Do we support database?
if [ "$DBTYPE" != 'mysqli' ]; then # && [ "$DBTYPE" != 'pgsql' ]; then
    echo "Database type '$DBTYPE' is not supported"
    exit 5;
fi

# Does the data root exist?
if [ ! -d "$DATAROOT" ]; then
    echo "Could not find data directory: $DATAROOT"
    exit 6;
fi

# Creating backup directory
BACKUP_DIR="$BACKUP_DIRECTORY/$IDENTIFIER"
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
else
    echo -n "Backup '$IDENTIFIER' already exist, would you like to delete it (y/N)? "
    read -n 1 CONFIRM
    echo
    if [ "$CONFIRM" == "y" ]; then
        rm -r "$BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    else
        echo "Aborting!"
        exit 10;
    fi
fi

echo "Backuping Moodle $RELEASE $MATURITY $DBTYPE ($MODE)"
echo "  [$IDENTIFIER]"

# Saving information
echo "time=$(date +"%Y-%m-%d %H:%M:%I")" > "$BACKUP_DIR/$INFO_FILE"
echo "origpath=$DIR" >> "$BACKUP_DIR/$INFO_FILE"
echo "realpath=$REALPATH" >> "$BACKUP_DIR/$INFO_FILE"
echo "dataroot=$DATAROOT" >> "$BACKUP_DIR/$INFO_FILE"
echo "branch=$BRANCH" >> "$BACKUP_DIR/$INFO_FILE"
echo "version=$VERSION" >> "$BACKUP_DIR/$INFO_FILE"
echo "release=$RELEASE" >> "$BACKUP_DIR/$INFO_FILE"
echo "maturity=$MATURITY" >> "$BACKUP_DIR/$INFO_FILE"
echo "dbtype=$DBTYPE" >> "$BACKUP_DIR/$INFO_FILE"
echo "dbhost=$DBHOST" >> "$BACKUP_DIR/$INFO_FILE"
echo "dbuser=$DBUSER" >> "$BACKUP_DIR/$INFO_FILE"
echo "dbpass=$DBPASS" >> "$BACKUP_DIR/$INFO_FILE"
echo "dbname=$DBNAME" >> "$BACKUP_DIR/$INFO_FILE"
echo "gitbranch=$GITBRANCH" >> "$BACKUP_DIR/$INFO_FILE"
echo "gitorigin=$GITORIGIN" >> "$BACKUP_DIR/$INFO_FILE"
echo "mode=$MODE" >> "$BACKUP_DIR/$INFO_FILE"

# Backing up database
case "$DBTYPE" in

    "mysqli" )
        echo "Dumping MySQL Data..."
        mysqldump -u$DBUSER -p$DBPASS -h $DBHOST $DBNAME > "$BACKUP_DIR/$DB_FILE"
    ;;

    "pgsql" )
    ;;

esac

# Saving directory
echo "Saving Moodle file system..."
rsync -a "$REALPATH/"* "$BACKUP_DIR/moodle"
rsync -a "$DATAROOT/"* "$BACKUP_DIR/moodledata"

echo "Backup complete!"
exit 0;