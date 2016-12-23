#!/bin/bash
#
# Minimal set-up for development.
#
# This turns on the minimal development options. Then creates some users,
# make a course and enrol the users in it.

echo "Setting up mindev mode..."
mdk run mindev > /dev/null 2>&1

echo "Creating a bunch of users..."
mdk run users > /dev/null 2>&1

echo "Creating a course..."
COURSENAME=`mdk run makecourse 2> /dev/null | grep 'http'`
if [ -n "$COURSENAME" ]; then
    echo "  $COURSENAME"
fi

echo "Enrolling users in the course..."
mdk run enrol > /dev/null 2>&1
