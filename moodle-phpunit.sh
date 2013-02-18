#!/bin/bash

# Installs PHPUnit requirements for a Moodle instance

DIR=`pwd`
PHPCLI="/usr/bin/php"

if ! moodle info -q; then
    exit 32;
fi

DATAROOT=`moodle info dataroot`
PHPUROOT="${DATAROOT}_phpu"

TEST=`grep 'CFG->phpunit_prefix' $DIR/config.php`
if [ -n "$TEST" ]; then
    echo 'Notice: $CFG->phpunit_dataroot already in config file.'
    echo '  Assuming $CFG->phpunit_dataroot = "php_u"'
else
    echo -e "\n" >> "$DIR/moodle/config.php"
    echo -e "\n\$CFG->phpunit_prefix = 'phpu_';" >> "$DIR/config.php"
fi

TEST=`grep 'CFG->phpunit_dataroot' $DIR/config.php`
if [ -n "$TEST" ]; then
    echo 'Notice: $CFG->phpunit_dataroot already in config file.'
    echo '  Assuming $CFG->phpunit_dataroot = $CFG->dataroot . "_phpu"'
else
    echo -e "\n\$CFG->phpunit_dataroot = \$CFG->dataroot . '_phpu';" >> "$DIR/config.php"
fi

if [ ! -d "$PHPUROOT" ]; then
    mkdir "$PHPUROOT"
    chmod 0777 "$PHPUROOT"
fi

cd "$DIR"
$PHPCLI ${DIR}/admin/tool/phpunit/cli/init.php