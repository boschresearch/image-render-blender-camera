#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /camera_pinhole.py
# Created Date: Thursday, October 22nd 2020, 2:51:36 pm
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

import bpy
import json

from anybase import config

from . import camera_pin_gen_opencv

#####################################################################
# Create the camera name
def CreateName(_sName):
    return "Cam.PinGen.{0}".format(_sName)


# enddef


#####################################################################
# Create Light Field Trace Cameras
def Create(
    _sName,
    _dicCamera,
    bOverwrite=False,
    bForce=False,
    fScale=1.0,
    bCreateFrustum=False,
    dicAnyCamEx=None,
):

    #####################################################
    # Get camera data
    dicProject = _dicCamera.get("dicProject")

    dicPrjType = config.SplitDti(dicProject.get("sDTI"))
    lPrjType = dicPrjType.get("lType")
    iPrjTypeCnt = len(lPrjType)

    if iPrjTypeCnt < 5 or lPrjType[3] != "pingen":
        raise RuntimeError(
            "Unsupported generalized pinhole camera type: {}".format(
                _dicCamera.get("sDTI")
            )
        )
    # endif

    sGenType = lPrjType[4]
    if sGenType == "opencv":
        return camera_pin_gen_opencv.Create(
            _sName,
            _dicCamera,
            bOverwrite=bOverwrite,
            bForce=bForce,
            fScale=fScale,
            bCreateFrustum=bCreateFrustum,
            dicAnyCamEx=dicAnyCamEx,
        )
    else:
        raise RuntimeError(
            "Unsupported generalized pinhole camera type: {}".format(
                _dicCamera.get("sDTI")
            )
        )
    # endif


# enddef
