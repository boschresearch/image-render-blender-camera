#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /rand_2d.py
# Created Date: Thursday, October 22nd 2020, 2:51:28 pm
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

##########################################################
# Functions for randomize 2D grid group
import bpy
from anyblend.node import align as nalign
from anyblend.node import shader as nsh
from .. import render_pars

##########################################################
# Create nodes for one position channel


def _ProcPosValue(ngMain, skIn, tAlignOuter, tAlignInner, tNodeSpace):

    skVal1 = nsh.math.Subtract(ngMain, "Subtract", skIn, 0.55)
    nalign.Relative(skIn, tAlignOuter, skVal1, tAlignInner, tNodeSpace)

    skVal2 = nsh.math.Multiply(ngMain, "Multiply", skVal1, 10.0)
    nalign.Relative(skVal1, (1, 0), skVal2, (0, 0), tNodeSpace)

    skVal3 = nsh.math.Subtract(ngMain, "Subtract", skVal2, 0.5)
    nalign.Relative(skVal2, (1, 0), skVal3, (0, 0), tNodeSpace)

    skVal4 = nsh.math.Power(ngMain, "Power", 4.0, skVal3)
    nalign.Relative(skVal3, (1, 0), skVal4, (0, 0), tNodeSpace)

    skVal5 = nsh.math.Multiply(ngMain, "Multiply", skVal4, 0.75)
    nalign.Relative(skVal4, (1, 0), skVal5, (0, 0), tNodeSpace)

    skVal6 = nsh.math.Modulo(ngMain, "Modulo", skVal5, 1.0)
    nalign.Relative(skVal5, (1, 0), skVal6, (0, 0), tNodeSpace)

    skVal7 = nsh.math.Subtract(ngMain, "Subtract", skVal6, 0.5)
    nalign.Relative(skVal6, (1, 0), skVal7, (0, 0), tNodeSpace)

    return skVal7


# enddef

##########################################################
# Create randomize 2d grid group


def Create(bForce=False):
    """
    Create shader node group to randomize 2D vector.
    Expect 2D vector to lie in range [-0.5, 0.5] for each component.
    Returns vector in same range.
    Optional Parameters:
        Force: Renew node tree even if group already exists.
    """

    # Create the name for the sensor specs shade node tree
    sGrpName = "AnyCam.RaySplitter.Randomize2"

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
        tNodeSpace = (30, 15)

        # Remove all nodes that may be present
        for nod in ngMain.nodes:
            ngMain.nodes.remove(nod)
        # endfor

        # Define inputs
        sValX = "Value X"
        sValY = "Value Y"

        lInputs = [[sValX, "NodeSocketFloat", 1.0], [sValY, "NodeSocketFloat", 1.0]]

        # Define Output
        sRandX = "Random X"
        sRandY = "Random Y"

        lOutputs = [[sRandX, "NodeSocketFloat"], [sRandY, "NodeSocketFloat"]]

        # Add group inputs if necessary and set default values
        nodIn = nsh.utils.ProvideNodeTreeInputs(ngMain, lInputs)

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, lOutputs)

        nodIn.location = (-400, 0)

        skValX = nodIn.outputs[sValX]
        skValY = nodIn.outputs[sValY]

        ###############################################################

        skSumXY = nsh.math.Add(ngMain, "X + Y", skValX, skValY)
        skDifXY = nsh.math.Subtract(ngMain, "X - Y", skValX, skValY)

        skPos = nsh.vector.CombineXYZ(ngMain, "Combine XY", skSumXY, skDifXY, 0.0)
        lNoise = nsh.tex.Noise(ngMain, "Noise Map", skPos, 200.0, 10.0, 0.0)

        lRGB = nsh.color.SeparateRGB(ngMain, "Separate RGB", lNoise["Color"])

        nalign.Relative(nodIn, (1, 0), skSumXY, (0, 1), tNodeSpace)
        nalign.Relative(nodIn, (1, 1), skDifXY, (0, 0), tNodeSpace)
        nalign.Relative(skSumXY, (1, 1), skPos, (0, 0), tNodeSpace)
        nalign.Relative(skPos, (1, 0), lNoise, (0, 0), tNodeSpace)
        nalign.Relative(lNoise, (1, 0), lRGB, (0, 0), tNodeSpace)

        skRandX = _ProcPosValue(ngMain, lRGB[0], (1, 0), (0, 1), tNodeSpace)
        skRandY = _ProcPosValue(ngMain, lRGB[1], (1, 1), (0, 0), tNodeSpace)

        ###############################################################
        # Links to output

        ngMain.links.new(skRandX, nodOut.inputs[sRandX])
        ngMain.links.new(skRandY, nodOut.inputs[sRandY])

        nalign.Relative(skRandX, (1, 1), nodOut, (0, 0), tNodeSpace)

    # endif

    return ngMain


# enddef
