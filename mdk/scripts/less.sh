#!/bin/bash
#
# Compile the Less files of Bootstrap base.
#
# Deprecated script, please refer to the CSS command.

echo "This script is deprecated, please use:"
echo "  mdk css --compile"
echo ""

P=`mdk info -v path`
if [[ -z "$(which recess)" ]]; then
    echo "Recess could not be found. Aborting..."
    exit 1
fi

DIR="$P/theme/bootstrapbase/less"
if [[ ! -d "$DIR" ]]; then
    echo "Could not find theme/boostrapbase. Aborting..."
    exit 2
fi

echo "Compiling theme/bootstrapbase CSS"
cd "$DIR"
recess --compile --compress moodle.less > ../style/moodle.css
recess --compile --compress editor.less > ../style/editor.css
