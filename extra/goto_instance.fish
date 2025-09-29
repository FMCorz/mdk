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

function gt -d "Go to the folder of a Moodle instance"
    if test (count $argv) -gt 0
        set DIR (mdk config show dirs.storage)
        set WWWDIR (mdk config show wwwDir)
        cd "$DIR/$argv[1]/$WWWDIR"
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
