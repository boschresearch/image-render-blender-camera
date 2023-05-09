#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /ac_pref.py
# Created Date: Thursday, October 22nd 2020, 2:51:41 pm
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

# LFT AddOn Preferences

import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty


class AcAddonPreferences(AddonPreferences):
    bl_idname = __package__

    sAcDataPath: StringProperty(
        name="AnyCam Data Path",
        subtype="FILE_PATH",
        default="//",
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="AnyCam addon preferences")
        layout.prop(self, "sAcDataPath")

    # enddef


# endclass


###############################################################
# Register
def register():
    bpy.utils.register_class(AcAddonPreferences)


# enddef

###############################################################
# Unregister
def unregister():
    bpy.utils.unregister_class(AcAddonPreferences)


# enddef
