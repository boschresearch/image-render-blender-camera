#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /__init__.py
# Created Date: Thursday, October 22nd 2020, 2:51:38 pm
# Author: Christian Perwass
# <LICENSE id="GPL-3.0">
#
#   Image-Render Blender Camera add-on module
#   Copyright (C) 2022 Robert Bosch GmbH and its subsidiaries
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#
# </LICENSE>
###
from . import camera

bHasBpy = False
try:
    import _bpy

    bHasBpy = True
except:
    bHasBpy = False
# endtry

if bHasBpy:
    from . import optics
    from . import camera_lft
    from . import camera_lut
    from . import camera_pano
    from . import camera_poly
    from . import camera_pinhole
    from . import camera_pin_gen
# endif
