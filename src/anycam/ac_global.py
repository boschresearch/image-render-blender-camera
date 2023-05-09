#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /ac_global.py
# Created Date: Thursday, October 22nd 2020, 2:51:40 pm
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

###################################################
# Global variables

dicAnyCamDb = {}

dicRenderParsDef = {
    "render": {"_values_": ["engine"]},
    "cycles": {
        "_values_": [
            "progressive",
            "samples",
            "preview_samples",
            "aa_samples",
            "preview_aa_samples",
            "use_square_samples",
            "max_bounces",
            "diffuse_bounces",
            "glossy_bounces",
            "transparent_max_bounces",
            "transmission_bounces",
            "volume_bounces",
            "blur_glossy",
            "blur_glossy",
            "caustics_reflective",
            "caustics_refractive",
        ]
    },
}
