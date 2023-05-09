#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /pixel_frac.py
# Created Date: Thursday, October 22nd 2020, 2:51:27 pm
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
# Functions for pixel fraction calculation
import bpy
from anyblend.node import align as nalign
from anyblend.node import shader as nsh
from .. import render_pars

##########################################################
# Create pixel fraction grid group


def Create(bForce=False):
    """
    Create shader node group to calculate pixel fraction.
    Optional Parameters:
        Force: Renew node tree even if group already exists.
    """

    # Create the name for the sensor specs shade node tree
    sGrpName = "AnyCam.RaySplitter.PixelFrac.v2"

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

        # Define inputs
        sDirX = "Dir X (local)"
        sDirY = "Dir Y (local)"
        sHalfW_bu = "Half Width (bu)"
        sHalfH_bu = "Half Height (bu)"
        sPixSize_bu = "Pixels Size (bu)"

        lInputs = [
            [sDirX, "NodeSocketVector", (0, 0, 0)],
            [sDirY, "NodeSocketVector", (0, 0, 0)],
            [sHalfW_bu, "NodeSocketFloat", 1.0],
            [sHalfH_bu, "NodeSocketFloat", 1.0],
            [sPixSize_bu, "NodeSocketFloat", 1.0],
        ]

        # Define Output
        sFracX = "Frac X"
        sFracY = "Frac Y"

        lOutputs = [[sFracX, "NodeSocketFloat"], [sFracY, "NodeSocketFloat"]]

        # Add group inputs if necessary and set default values
        nodIn = nsh.utils.ProvideNodeTreeInputs(ngMain, lInputs)

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, lOutputs)

        nodIn.location = (-400, 0)

        skDirX = nodIn.outputs[sDirX]
        skDirY = nodIn.outputs[sDirY]
        skPixelSize_bu = nodIn.outputs[sPixSize_bu]
        skHalfW_bu = nodIn.outputs[sHalfW_bu]
        skHalfH_bu = nodIn.outputs[sHalfH_bu]

        # Add Object Info Shader
        # lObjInfo = nsh.utils.ObjectInfo(ngMain)
        # nalign.Relative(nodIn, (1, 0), lObjInfo, (1, 1), tNodeSpace)

        # Add Geometry Info Shader
        lGeoInfo = nsh.utils.Geometry(ngMain)
        nalign.Relative(nodIn, (1, 0), lGeoInfo, (1, 1), tNodeSpace)

        ###############################################################

        # Relative Vector from Origin
        # skRelVecCtr = nsh.vector.Subtract(ngMain, "Rel Vec from Ctr", lGeoInfo['Position'], lObjInfo['Location'])
        skRelVecCtr = nsh.vector.TransformPointWorldToObject(
            ngMain, "Rel Vec from Ctr", lGeoInfo["Position"]
        )
        nalign.Relative(lGeoInfo, (1, 0), skRelVecCtr, (0, 0), tNodeSpace)

        skCompX = nsh.vector.Dot(ngMain, "Component X", skRelVecCtr, skDirX)
        nalign.Relative(skRelVecCtr, (1, 0), skCompX, (0, 0), tNodeSpace)

        skCompY = nsh.vector.Dot(ngMain, "Component Y", skRelVecCtr, skDirY)
        nalign.Relative(skCompX, (1, 1), skCompY, (1, 0), tNodeSpace)

        skPosX = nsh.math.Add(ngMain, "Pos X", skCompX, skHalfW_bu)
        nalign.Relative(skCompX, (1, 0), skPosX, (0, 0), tNodeSpace)

        skPosY = nsh.math.Add(ngMain, "Pos Y", skCompY, skHalfH_bu)
        nalign.Relative(skCompY, (1, 0), skPosY, (0, 0), tNodeSpace)

        skPixIdxX = nsh.math.Divide(ngMain, "Pixel Idx X", skPosX, skPixelSize_bu)
        nalign.Relative(skPosX, (1, 0), skPixIdxX, (0, 0), tNodeSpace)

        skPixIdxY = nsh.math.Divide(ngMain, "Pixel Idx Y", skPosY, skPixelSize_bu)
        nalign.Relative(skPosY, (1, 0), skPixIdxY, (0, 0), tNodeSpace)

        skPixFracX = nsh.math.Modulo(ngMain, "Pixel Frac X", skPixIdxX, 1.0)
        nalign.Relative(skPixIdxX, (1, 0), skPixFracX, (0, 0), tNodeSpace)

        skPixFracY = nsh.math.Modulo(ngMain, "Pixel Frac Y", skPixIdxY, 1.0)
        nalign.Relative(skPixIdxY, (1, 0), skPixFracY, (0, 0), tNodeSpace)

        skPixFracCtrX = nsh.math.Subtract(ngMain, "Pixel Frac Ctr X", skPixFracX, 0.5)
        nalign.Relative(skPixFracX, (1, 0), skPixFracCtrX, (0, 0), tNodeSpace)

        skPixFracCtrY = nsh.math.Subtract(ngMain, "Pixel Frac Ctr Y", skPixFracY, 0.5)
        nalign.Relative(skPixFracY, (1, 0), skPixFracCtrY, (0, 0), tNodeSpace)

        skPixFullFracCtrX = nsh.math.Multiply(
            ngMain, "Pixel Full Frac Ctr X", skPixFracCtrX, 2.0
        )
        nalign.Relative(skPixFracCtrX, (1, 0), skPixFullFracCtrX, (0, 0), tNodeSpace)

        skPixFullFracCtrY = nsh.math.Multiply(
            ngMain, "Pixel Full Frac Ctr Y", skPixFracCtrY, 2.0
        )
        nalign.Relative(skPixFracCtrY, (1, 0), skPixFullFracCtrY, (0, 0), tNodeSpace)

        ###############################################################
        # Links to output

        ngMain.links.new(skPixFullFracCtrX, nodOut.inputs[sFracX])
        ngMain.links.new(skPixFullFracCtrY, nodOut.inputs[sFracY])

        nalign.Relative(skPixFullFracCtrX, (1, 0), nodOut, (0, 0), tNodeSpace)

    # endif

    return ngMain


# enddef
