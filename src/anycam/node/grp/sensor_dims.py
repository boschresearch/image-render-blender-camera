#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /sensor_dims.py
# Created Date: Thursday, October 22nd 2020, 2:51:23 pm
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
# Create node group to calculate sensor dimensions in blender units

import bpy
from anyblend.node import align as nalign
from anyblend.node import shader as nsh
from . import render_pars

################################################################
#
# Creates a node group with a set of value nodes that contain
# sensor specification values.
#
def Create(bForce=False):
    """
    Calculates sensor dimensions in blender units from sensor parameters.
    """

    # Create the name for the sensor specs shade node tree
    sGrpName = "AnyCam.SensorDims"

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
        tNodeSpace = (50, 25)

        # Remove all nodes that may be present
        for nod in ngMain.nodes:
            ngMain.nodes.remove(nod)
        # endfor

        sPixCntX = "Pixel Count X"
        sPixCntY = "Pixel Count Y"
        sPixSize = "Pixel Size (um)"

        # Define inputs
        lInputs = [
            [sPixCntX, "NodeSocketFloat", 1000],
            [sPixCntY, "NodeSocketFloat", 1000],
            [sPixSize, "NodeSocketFloat", 1],
        ]

        # Define Output
        lOutputs = [
            ["Sensor Width (bu)", "NodeSocketFloat"],
            ["Sensor Height (bu)", "NodeSocketFloat"],
            ["Sensor Half Width (bu)", "NodeSocketFloat"],
            ["Sensor Half Height (bu)", "NodeSocketFloat"],
            ["Pixel Size (bu)", "NodeSocketFloat"],
        ]

        # Add group inputs if necessary and set default values
        nodIn = nsh.utils.ProvideNodeTreeInputs(ngMain, lInputs)

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, lOutputs)

        nodIn.location = (0, 0)

        skPixSize_um = nodIn.outputs[sPixSize]
        skPixCntX = nodIn.outputs[sPixCntX]
        skPixCntY = nodIn.outputs[sPixCntY]

        # Calc pixel size in mm
        skPixSize_mm = nsh.math.Multiply(ngMain, "Pixel Size (mm)", skPixSize_um, 1e-3)
        nalign.Relative(nodIn, (1, 1), skPixSize_mm, (1, 0), tNodeSpace)

        # Add render pars groups node
        nodRndPars = nsh.utils.Group(ngMain, render_pars.Create())
        nalign.Relative(skPixSize_mm, (1, 1), nodRndPars, (1, 0), tNodeSpace)
        skBUperMM = nodRndPars.outputs["BU_per_MM"]

        skSensWidth_mm = nsh.math.Multiply(
            ngMain, "Sensor Width (mm)", skPixCntX, skPixSize_mm
        )
        nalign.Relative(nodIn, (1, 0), skSensWidth_mm, (0, 1), tNodeSpace)

        skSensHeight_mm = nsh.math.Multiply(
            ngMain, "Sensor Height (mm)", skPixCntY, skPixSize_mm
        )
        nalign.Relative(nodIn, (1, 0), skSensHeight_mm, (0, 0), tNodeSpace)

        skSensWidth_bu = nsh.math.Multiply(
            ngMain, "Sensor Width (bu)", skSensWidth_mm, skBUperMM
        )
        nalign.Relative(skSensWidth_mm, (1, 0), skSensWidth_bu, (0, 0), tNodeSpace)

        skSensHeight_bu = nsh.math.Multiply(
            ngMain, "Sensor Height (bu)", skSensHeight_mm, skBUperMM
        )
        nalign.Relative(skSensHeight_mm, (1, 0), skSensHeight_bu, (0, 0), tNodeSpace)

        skSensHalfW_bu = nsh.math.Multiply(
            ngMain, "Sensor W/2 (bu)", skSensWidth_bu, 0.5
        )
        nalign.Relative(skSensHeight_bu, (0, 1), skSensHalfW_bu, (0, 0), tNodeSpace)

        skSensHalfH_bu = nsh.math.Multiply(
            ngMain, "Sensor H/2 (bu)", skSensHeight_bu, 0.5
        )
        nalign.Relative(skSensHalfW_bu, (0, 1), skSensHalfH_bu, (0, 0), tNodeSpace)

        skPixSize_bu = nsh.math.Multiply(
            ngMain, "Pixel Size (bu)", skPixSize_mm, skBUperMM
        )
        nalign.Relative(skSensHalfH_bu, (0, 1), skPixSize_bu, (0, 0), tNodeSpace)

        nalign.Relative(skSensHeight_bu, (1, 0), nodOut, (0, 0), tNodeSpace)
        ngMain.links.new(skSensWidth_bu, nodOut.inputs["Sensor Width (bu)"])
        ngMain.links.new(skSensHeight_bu, nodOut.inputs["Sensor Height (bu)"])
        ngMain.links.new(skSensHalfW_bu, nodOut.inputs["Sensor Half Width (bu)"])
        ngMain.links.new(skSensHalfH_bu, nodOut.inputs["Sensor Half Height (bu)"])
        ngMain.links.new(skPixSize_bu, nodOut.inputs["Pixel Size (bu)"])

    # endif

    return ngMain


# enddef
