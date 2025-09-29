#
# Moodle Development Kit
#
# Copyright (c) 2013 Frédéric Massart - FMCorz.net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# http://github.com/FMCorz/mdk
#

# This file defines a Fish function to quickly go to into an MDK instance.
#
# To install on Ubuntu, link it into ~/.config/fish/functions/
#
# Usage:
#   gt <instance> [component/subsystem]
#   gtd <instance>

#   gt sm block_xp
#   gt sm core_ai
#

function gt -d "Go to the folder of a Moodle instance"
    if test (count $argv) -gt 0
        set DIR (mdk config show dirs.storage)
        set WWWDIR (mdk config show wwwDir)
        set COMPONENT $argv[2]
        set ROOTDIR "$DIR/$argv[1]"
        set COMPONENTSFILE "$ROOTDIR/$WWWDIR/lib/components.json"
        set RELPATH ""

        if test -n "$COMPONENT"; and string match -q "*_*" "$COMPONENT"; and test -f "$COMPONENTSFILE"
            set PARTS (string split -f 1,2 -m 1 "_" "$COMPONENT")
            set TYPE $PARTS[1]
            set NAME $PARTS[2]
            set COMPPATH ""

            if test "$TYPE" = core
                set COMPPATH (cat $COMPONENTSFILE | jq -r ".subsystems.$NAME")
                if test -n "$COMPPATH"; and test "$COMPPATH" != null
                    set RELPATH "$COMPPATH"
                end
            else
                set COMPPATH (cat $COMPONENTSFILE | jq -r ".plugintypes.$TYPE")
                if test -n "$COMPPATH"; and test "$COMPPATH" != null
                    set RELPATH "$COMPPATH/$NAME"
                end
            end

        end
        cd "$ROOTDIR/$WWWDIR/$RELPATH"

    else
        echo "Could not resolve instance path"
    end
end

function gtd -d "Go to the data folder of a Moodle instance"
    if test (count $argv) -gt 0
        set DIR (mdk config show dirs.storage)
        set DATADIR (mdk config show dataDir)
        cd "$DIR/$argv[1]/$DATADIR"
    else
        echo "Could not resolve instance path"
    end
end

complete -f -c gt -a '(mdk list -n)'
complete -f -c gtd -a '(mdk list -n)'
