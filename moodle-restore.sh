#!/bin/bash

DIR=`pwd`
REALPATH=`readlink -f "$DIR"`
BACKUP_DIRECTORY="$HOME/.moodle/backup"
INFO_FILE="backup.txt"
DB_FILE="backup.db"
IDENTIFIER=$1
ACTION=$2
BACKUP_DIR="$BACKUP_DIRECTORY/$IDENTIFIER"
DO_RESTORE=false

# If identifier is empty, we leave
if [ -z "$IDENTIFIER" ]; then
    echo "You need to specify which backup to restore"
    exit 1
elif [ ! -d "$BACKUP_DIR" ]; then
    echo "This backup does not seem to exist"
    exit 2
fi

# Reading information from Backup
TIME=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^time=" | sed -n -e "s/\w*=\(.*\)$/\1/p"`
ORIGPATH=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^origpath=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
REALPATH=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^realpath=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
DATAROOT=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^dataroot=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
BRANCH=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^branch=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
VERSION=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^version=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
RELEASE=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^release=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
MATURITY=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^maturity=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
DBTYPE=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^dbtype=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
DBHOST=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^dbhost=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
DBUSER=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^dbuser=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
DBPASS=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^dbpass=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
DBNAME=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^dbname=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
GITBRANCH=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^gitbranch=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
GITORIGIN=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^gitorigin=" | sed -n -e "s/.*=\(.*\)$/\1/p"`
MODE=`cat "$BACKUP_DIR/$INFO_FILE" | grep -E "^mode=" | sed -n -e "s/.*=\(.*\)$/\1/p"`

# Action
case "$ACTION" in

    "info" )
        echo "Information about $IDENTIFIER"
        echo
        echo "Backed up at: $TIME"
        echo "Original path: $ORIGPATH"
        echo "Real path: $REALPATH"
        echo "Data root: $DATAROOT"
        echo "--"
        echo "Branch: $BRANCH"
        echo "Version: $VERSION"
        echo "Release: $RELEASE"
        echo "Maturity: $MATURITY"
        echo "--"
        echo "Database engine: $DBTYPE"
        echo "Database name: $DBNAME"
        echo "--"
        echo "Git origin: $GITORIGIN"
        echo "Git branch: $GITBRANCH"
        echo "Mode: $MODE"
    ;;

    "do" )
        DO_RESTORE=true
    ;;

    * )
        echo "Usage"
        echo ""
        echo "moodle restore IDENTIFIER info       Gives information about a backup"
        echo "moodle restore IDENTIFIER do         Restores the backup to original state"
    ;;

esac

if $DO_RESTORE; then

    # Do we support database?
    if [ "$DBTYPE" != 'mysqli' ]; then
        echo "Database type '$DBTYPE' is not supported"
        exit 5
    fi

    TO="$REALPATH"
    DATA="$DATAROOT"
    DB="$DBNAME"
    DBU="$DBUSER"
    DBP="$DBPASS"
    DBH="$DBHOST"

    echo "Restoring $IDENTIFIER"

    echo "  Web directory:  $TO"
    if [ -d "$TO" ]; then
        mkdir -p "/tmp/moodle-trash/"
        mv "$TO" "/tmp/moodle-trash/"
    fi
    rsync -a "$BACKUP_DIR/moodle/"* "$TO"

    echo "  Data directory: $DATA"
    if [ -d "$DATA" ]; then
        mkdir -p "/tmp/moodle-trash/"
        mv "$DATA" "/tmp/moodle-trash/"
    fi
    rsync -a "$BACKUP_DIR/moodledata/"* "$DATA"
    chmod 0777 "$DATA"

    echo "  Database: $DB ($DBTYPE)"
    case "$DBTYPE" in

        "mysqli" )
            DBEXISTS=`mysql -u$DBU -p$DBP -e "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '$DBN'"`
            if [ -n "$DBEXISTS" ]; then
                mysql -u$DBU -p$DBP -h $DBH -e "DROP DATABASE $DB" > /dev/null 2>&1
            fi
            mysql -u$DBU -p$DBP -h $DBH -e "CREATE DATABASE $DB DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;" > /dev/null 2>&1
            cat "$BACKUP_DIR/$DB_FILE" | mysql -u$DBU -p$DBP -h $DBH $DB
        ;;

    esac

    echo "Backup restored!"

fi

exit 0