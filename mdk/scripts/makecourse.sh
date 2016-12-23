#!/bin/bash
#
# Creates a course.

PHP=`mdk config show php`
SHORTNAME="MDK101-$RANDOM"
FULLNAME="Moodle Development $RANDOM"
SIZE="S"
CLI="admin/tool/generator/cli/maketestcourse.php"

if [ ! -e "$CLI" ]; then
    echo "Cannot create a course: the CLI script to create test courses could not be found."
    exit 1
fi

$PHP $CLI --shortname="$SHORTNAME" --fullname="$FULLNAME" --size=$SIZE --bypasscheck
