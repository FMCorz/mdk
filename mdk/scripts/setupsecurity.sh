#!/bin/bash
#
# Script to setup a clone for testing against the security repository
#
# It removes existing origin remote and adds the security repository in
# read-only mode. It also adds a git hook to prevent pushes. The purpose is to
# prevent as much as possible that security issues are released to public
# repositories.

set -e

GIT=`mdk config show git`
REPOURL=`mdk config show remotes.security`
ORIGINREMOTE=`mdk config show upstreamRemote`
DIRROOT=`mdk info -v path`

# Remove origin remote.
echo "Deleting current origin remote..."
$GIT remote rm $ORIGINREMOTE

echo "Adding security repository remote as origin..."
${GIT} remote add $ORIGINREMOTE $REPOURL

# Pushes to an unexisting URL.
${GIT} remote set-url --push $ORIGINREMOTE no-pushes-allowed


# Git hook to prevent all pushes in case people is adding other remotes anyway.
content="#!/bin/sh

>&2 echo \"Sorry, pushes are not allowed. This clone is not supposed to be used
to push stuff as you may accidentally push security patches to public repos.\"
exit 1"

hookfile="$DIRROOT/.git/hooks/pre-push"

if [ -f "$hookfile" ]; then
    existingcontent=$(cat $hookfile)

    if [[ "$content" != "$existingcontent" ]]; then
        # Error if there is a hook we don't know about.
        echo "Error: Security repository setup adds a pre-push hook to "\
        "prevent accidental pushes to public repositories. You already have a "\
        "pre-push hook, please delete it or back it up and merge it once "\
        "security repository setup concluded."
        exit 1
    fi
else
    # Create the file.
    echo "Adding a git hook to prevent pushes from this clone..."
    cat > $hookfile << EOL
$content
EOL
    chmod +x $hookfile
fi

exit 0
