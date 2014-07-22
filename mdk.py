#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2013 Frédéric Massart - FMCorz.net

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

http://github.com/FMCorz/mdk
"""

"""
This file executes MDK as a package.

It is intended to be used by those who are not using MDK as a package,
they can make this file executable and execute it directly.

Is also provides backwards compatibility to those who had set up MDK manually
by cloning the repository and linked to mdk.py as an executable.

Please note that using this method is not advised, using `python -m mdk` or the
executable installed with the package is recommended.
"""

import runpy
a = runpy.run_module('mdk', None, '__main__')
