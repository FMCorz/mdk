#!/bin/bash

# Check or sets up the environment values for Moodle scripts
#
# MOODLE_HOSTNAME="fred.moodle.local"
# MOODLE_DIR_WWW="/var/www"
# MOODLE_DIR_REPOSITORIES="/var/www/repositories"
# MOODLE_GITHUB="git@github.com:FMCorz/moodle.git"
# MOODLE_STABLE="git://git.moodle.org/moodle.git"
# MOODLE_INTEGRATION="git://git.moodle.org/integration.git"
# MOODLE_DB_MYSQL_HOST="localhost"
# MOODLE_DB_MYSQL_USER="root"
# MOODLE_DB_MYSQL_PWD="root"
# MOODLE_ADMIN_USER="admin"
# MOODLE_ADMIN_PWD="test"
# MOODLE_PREFIX_STABLE="stable_"
# MOODLE_PREFIX_INTEGRATION="testing_"

MODE="$1"

if [ -z "$MODE" ] || [ "$MODE" == "check" ]; then
    MISSING=false

    if [ -z "$MOODLE_HOSTNAME" ]; then
        echo "Missing MOODLE_HOSTNAME setting"
        MISSING=true
    fi
    if [ -z "$MOODLE_DIR_WWW" ]; then
        echo "Missing MOODLE_DIR_WWW setting"
        MISSING=true
    fi
    if [ -z "$MOODLE_DIR_REPOSITORIES" ]; then
        echo "Missing MOODLE_DIR_REPOSITORIES setting"
        MISSING=true
    fi
    if [ -z "$MOODLE_GITHUB" ]; then
        echo "Missing MOODLE_GITHUB setting"
        MISSING=true
    fi
    if [ -z "$MOODLE_STABLE" ]; then
        echo "Missing MOODLE_STABLE setting"
        MISSING=true
    fi
    if [ -z "$MOODLE_INTEGRATION" ]; then
        echo "Missing MOODLE_INTEGRATION setting"
        MISSING=true
    fi
    if [ -z "$MOODLE_DB_MYSQL_HOST" ]; then
        echo "Missing MOODLE_DB_MYSQL_HOST setting"
        MISSING=true
    fi
    if [ -z "$MOODLE_DB_MYSQL_USER" ]; then
        echo "Missing MOODLE_DB_MYSQL_USER setting"
        MISSING=true
    fi
    if [ -z "$MOODLE_DB_MYSQL_PWD" ]; then
        echo "Missing MOODLE_DB_MYSQL_PWD setting"
        MISSING=true
    fi
    if [ -z "$MOODLE_ADMIN_USER" ]; then
        echo "Missing MOODLE_ADMIN_USER setting"
        MISSING=true
    fi
    if [ -z "$MOODLE_ADMIN_PWD" ]; then
        echo "Missing MOODLE_ADMIN_PWD setting"
        MISSING=true
    fi
    if [ -z "$MOODLE_PREFIX_STABLE" ]; then
        echo "Missing MOODLE_PREFIX_STABLE setting"
        MISSING=true
    fi
    if [ -z "$MOODLE_PREFIX_INTEGRATION" ]; then
        echo "Missing MOODLE_PREFIX_INTEGRATION setting"
        MISSING=true
    fi

    if $MISSING; then
        exit 1;
    fi

elif [ $MODE == "show" ]; then

    echo "MOODLE_HOSTNAME=$MOODLE_HOSTNAME"
    echo "MOODLE_DIR_WWW=$MOODLE_DIR_WWW"
    echo "MOODLE_DIR_REPOSITORIES=$MOODLE_DIR_REPOSITORIES"
    echo "MOODLE_GITHUB=$MOODLE_GITHUB"
    echo "MOODLE_STABLE=$MOODLE_STABLE"
    echo "MOODLE_INTEGRATION=$MOODLE_INTEGRATION"
    echo "MOODLE_DB_MYSQL_HOST=$MOODLE_DB_MYSQL_HOST"
    echo "MOODLE_DB_MYSQL_USER=$MOODLE_DB_MYSQL_USER"
    echo "MOODLE_DB_MYSQL_PWD=$MOODLE_DB_MYSQL_PWD"
    echo "MOODLE_ADMIN_USER=$MOODLE_ADMIN_USER"
    echo "MOODLE_ADMIN_PWD=$MOODLE_ADMIN_PWD"
    echo "MOODLE_PREFIX_STABLE=$MOODLE_PREFIX_STABLE"
    echo "MOODLE_PREFIX_INTEGRATION=$MOODLE_PREFIX_INTEGRATION"

fi

exit 0;