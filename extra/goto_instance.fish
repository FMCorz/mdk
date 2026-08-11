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
        set -l COMPONENT $argv[2]
        set -l DIR

        if test -n "$COMPONENT"
            set DIR (mdk path --component "$COMPONENT" --exists "$argv[1]" 2> /dev/null)
        else
            set DIR (mdk path --exists "$argv[1]" 2> /dev/null)
        end

        if test -z "$DIR"; or not test -d "$DIR"
            echo "Could not resolve instance path"
            return 1
        end

        cd "$DIR"

    else
        echo "Could not resolve instance path"
        return 1
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

function __gt_list_instances
    mdk info -ln 2> /dev/null
end

function __gt_list_components
    set -l cmd (commandline -opc)
    set -l instance $cmd[2]
    if test -z "$instance"
        return
    end

    mdk path --list-components "$instance" 2> /dev/null | string replace -r ' .*' ''
end

complete -f -c gt -n 'test (count (commandline -opc)) -le 1' -a '(__gt_list_instances)'
complete -f -c gt -n 'test (count (commandline -opc)) -eq 2' -a '(__gt_list_components)'
complete -f -c gtd -a '(__gt_list_instances)'
