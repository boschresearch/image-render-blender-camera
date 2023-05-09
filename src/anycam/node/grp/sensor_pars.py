#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /sensor_pars.py
# Created Date: Thursday, October 22nd 2020, 2:51:24 pm
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
# Create node group for that contains sensor specs

import bpy
from anyblend.node import align as nalign
from anyblend.node import shader as nsh

################################################################
#
# Creates a node group with a set of value nodes that contain
# sensor specification values.
#
def Create(_dicSensorData, bForce=False):
    """
    Expects dicSensorData to contain the following elements:
        sName: The sensor name
        fPixSize: The pixel pitch in microns
        iPixCntX: The number of pixels along the horizontal
        iPixCntY: The number of pixels along the vertical
    """

    # Create the name for the sensor specs shade node tree
    sGrpName = "AnyCam.SensorPars." + _dicSensorData["sName"].replace(" ", "_")

    # Try to get ray splitter specification node group
    ngMain = bpy.data.node_groups.get(sGrpName)

    ####!!! Debug
    # bpy.data.node_groups.remove(ngMain)
    # ngMain = None
    ####!!!

    if ngMain is None:
        ngMain = bpy.data.node_groups.new(sGrpName, "ShaderNodeTree")
        bUpdate = True
    else:
        bUpdate = bForce
    # endif

    if bUpdate == True:
        tNodeSpace = (50, 5)

        # Remove all nodes that may be present
        for nod in ngMain.nodes:
            ngMain.nodes.remove(nod)
        # endfor

        sPixCntX = "Pixel Count X"
        sPixCntY = "Pixel Count Y"
        sPixSize = "Pixel Size (um)"

        # Define Output
        lOutputs = [
            [sPixCntX, "NodeSocketFloat"],
            [sPixCntY, "NodeSocketFloat"],
            [sPixSize, "NodeSocketFloat"],
        ]

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, lOutputs)

        skPixCntX = nsh.utils.Value(ngMain, "Pixel Count X", _dicSensorData["iPixCntX"])
        skPixCntY = nsh.utils.Value(ngMain, "Pixel Count Y", _dicSensorData["iPixCntY"])
        skPixSize = nsh.utils.Value(
            ngMain, "Pixel Size (um)", _dicSensorData["fPixSize"]
        )

        ngMain.links.new(skPixCntX, nodOut.inputs[sPixCntX])
        ngMain.links.new(skPixCntY, nodOut.inputs[sPixCntY])
        ngMain.links.new(skPixSize, nodOut.inputs[sPixSize])

        skPixCntX.node.location = (0, 0)
        nalign.Relative(skPixCntX, (1, 1), skPixCntY, (1, 0), tNodeSpace)
        nalign.Relative(skPixCntY, (1, 1), skPixSize, (1, 0), tNodeSpace)
        nalign.Relative(skPixCntX, (1, 0), nodOut, (0, 0), tNodeSpace)

    # endif

    return ngMain


# enddef
