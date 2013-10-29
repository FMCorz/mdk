#!/bin/bash
#
# Compile the Less files of Bootstrap base.
#

P=`mdk info -v path`
if [[ -z "$(which lessc)" ]]; then
    echo "lessc could not be found. Aborting..."
    echo "Try install it with npm install less -g"
    exit 1
fi

DIR="$P/theme/bootstrapbase/less"
if [[ ! -d "$DIR" ]]; then
    echo "Could not find theme/bootstrapbase. Aborting..."
    exit 2
fi

echo "Compiling theme/bootstrapbase CSS"
cd "$DIR"
lessc --source-map-map-inline moodle.less ../style/moodle.css
lessc --source-map-map-inline editor.less ../style/editor.css
echo "Complete - please do not check these files in. You *must* use mdk run less for production compilation"
