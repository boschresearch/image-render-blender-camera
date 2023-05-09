#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /util.py
# Created Date: Thursday, October 22nd 2020, 2:51:14 pm
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

import sys
import pyjson5 as json

###############################################################################
# Unload all anycam modules
def UnloadModules():
    # Unload anycam modules when the addon is unregistered to enable debugging.
    lUnloadMods = []
    for sModName in sys.modules:
        #    print(sModName)
        if "anycam" in sModName or "PkgAnyCam" in sModName:
            lUnloadMods.append(sModName)
        # endif
    # endfor

    for sModName in lUnloadMods:
        # print("Unloading: " + sModName)
        del sys.modules[sModName]
    # endfor


# enddef

###############################################################################
# Load a JSON file
def LoadJson(_sFilePath):

    with open(_sFilePath, "r") as xFile:
        dicData = json.load(xFile)
    # endwith

    return dicData


# enddef

###############################################################################
# Save data as JSON file
def SaveJson(_sFilePath, _dicData):

    with open(_sFilePath, "w") as xFile:
        json.dump(_dicData, xFile)
    # endwith


# enddef
