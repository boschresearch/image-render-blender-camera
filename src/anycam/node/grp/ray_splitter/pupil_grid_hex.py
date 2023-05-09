#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /pupil_grid_hex.py
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
# Functions for pupil hexagonal grid group
import bpy
from anyblend.node import align as nalign
from anyblend.node import shader as nsh
from .. import render_pars

##########################################################
# Create pupil hexagonal grid group


def Create(bForce=False):
    """
    Create shader node group to calculate pupil grid hexagonal base.
    Optional Parameters:
        Force: Renew node tree even if group already exists.
    """

    # Create the name for the sensor specs shade node tree
    sGrpName = "AnyCam.RaySplitter.PupilGridHex.v2"

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
        sGridDia = "Grid Diameter (mm)"
        sGridDistZ = "Grid Distance Z (mm)"
        sHexRingCnt = "Hex Ring Count"

        lInputs = [
            [sGridDia, "NodeSocketFloat", 1.0],
            [sGridDistZ, "NodeSocketFloat", 1.0],
            [sHexRingCnt, "NodeSocketFloat", 1.0],
        ]

        # Define Output
        sHexBaseX = "Hex Base X"
        sHexBaseY = "Hex Base Y"
        sOrthoBaseY = "Ortho Base Y"
        sHexDirX = "Hex Dir X"
        sHexDirY = "Hex Dir Y"
        sOrthoDirY = "Ortho Dir Y"
        sGridOrig = "Grid Origin"
        sBaseLen = "Base Length (bu)"
        sGridRad = "Grid Radius (bu)"

        lOutputs = [
            [sHexBaseX, "NodeSocketVector"],
            [sHexBaseY, "NodeSocketVector"],
            [sOrthoBaseY, "NodeSocketVector"],
            [sHexDirX, "NodeSocketVector"],
            [sHexDirY, "NodeSocketVector"],
            [sOrthoDirY, "NodeSocketVector"],
            [sGridOrig, "NodeSocketVector"],
            [sBaseLen, "NodeSocketFloat"],
            [sGridRad, "NodeSocketFloat"],
        ]

        # Add group inputs if necessary and set default values
        nodIn = nsh.utils.ProvideNodeTreeInputs(ngMain, lInputs)

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, lOutputs)

        nodIn.location = (-400, 0)

        skGridDia = nodIn.outputs[sGridDia]
        skGridDistZ = nodIn.outputs[sGridDistZ]
        skHexRingCnt = nodIn.outputs[sHexRingCnt]

        # Add render pars groups node
        nodRndPars = nsh.utils.Group(ngMain, render_pars.Create())
        skBUperMM = nodRndPars.outputs["BU_per_MM"]
        nalign.Relative(nodIn, (1, 1), nodRndPars, (1, 0), tNodeSpace)

        # # Add Geometry Info Shader
        # lGeoInfo = nsh.utils.Geometry(ngMain)
        # nalign.Relative(nodRndPars, (1, 1), lGeoInfo, (1, 0), tNodeSpace)

        # # Add Object Info Shader
        # lObjInfo = nsh.utils.ObjectInfo(ngMain)
        # nalign.Relative(lGeoInfo, (1, 1), lObjInfo, (1, 0), tNodeSpace)

        # Add Ortho Dir Y (World)
        # skOrthoDirY = nsh.vector.TransformObjectToWorld(ngMain, "Ortho Dir Y (World)", (0, 1, 0))
        skOrthoDirY = nsh.vector.CombineXYZ(
            ngMain, "Ortho Dir Y (Local)", 0.0, 1.0, 0.0
        )
        nalign.Relative(nodIn, (1, 0), skOrthoDirY, (1, 1), tNodeSpace)

        # Add Hex Dir X (World)
        # skHexDirX = nsh.vector.TransformObjectToWorld(ngMain, "Hex Dir X (World)", (1, 0, 0))
        skHexDirX = nsh.vector.CombineXYZ(ngMain, "Hex Dir X (Local)", 1.0, 0.0, 0.0)
        nalign.Relative(skOrthoDirY, (1, 0), skHexDirX, (1, 1), tNodeSpace)

        ###############################################################
        # Grid Sizes

        skGridDia_bu = nsh.math.Multiply(
            ngMain, "Grid Diameter (bu)", skGridDia, skBUperMM
        )
        nalign.Relative(nodRndPars, (1, 0), skGridDia_bu, (0, 0), tNodeSpace)

        skGridRad_bu = nsh.math.Multiply(ngMain, "Grid Radius (bu)", skGridDia_bu, 0.5)
        nalign.Relative(skGridDia_bu, (1, 0), skGridRad_bu, (0, 0), tNodeSpace)

        skGridBaseLen_bu = nsh.math.Divide(
            ngMain, "Grid Base Len (bu)", skGridRad_bu, skHexRingCnt
        )
        nalign.Relative(skGridRad_bu, (0, 0), skGridBaseLen_bu, (0, 1), tNodeSpace)

        ngMain.links.new(skGridRad_bu, nodOut.inputs[sGridRad])
        ngMain.links.new(skGridBaseLen_bu, nodOut.inputs[sBaseLen])

        ###############################################################
        # Calc grid origin

        skGridDistZ_bu = nsh.math.Multiply(
            ngMain, "Grid Dist Z (bu)", skGridDistZ, skBUperMM
        )
        nalign.Relative(skGridDia_bu, (0, 1), skGridDistZ_bu, (0, 0), tNodeSpace)

        skGridDistNegZ_bu = nsh.math.Multiply(
            ngMain, "Grid Dist -Z (bu)", skGridDistZ_bu, -1.0
        )
        nalign.Relative(skGridDistZ_bu, (1, 0), skGridDistNegZ_bu, (0, 0), tNodeSpace)

        skGridOrigVec = nsh.vector.CombineXYZ(
            ngMain, "Grid Origin", 0.0, 0.0, skGridDistNegZ_bu
        )
        nalign.Relative(skGridDistNegZ_bu, (1, 0), skGridOrigVec, (0, 0), tNodeSpace)

        ngMain.links.new(skGridOrigVec, nodOut.inputs[sGridOrig])

        ###############################################################
        # Grid Vectors

        skHexDirY = nsh.vector.LinComb2(
            ngMain, "Hex Dir Y (world)", skHexDirX, 0.5, skOrthoDirY, 0.866025
        )
        nalign.Relative(skHexDirX, (1.5, 0), skHexDirY, (0, 1), tNodeSpace)

        skHexBaseX = nsh.vector.Scale(
            ngMain, "Hex Base X (world)", skHexDirX, skGridBaseLen_bu
        )
        nalign.Relative(skHexDirY, (1, 0), skHexBaseX, (0, 0), tNodeSpace)

        skHexBaseY = nsh.vector.Scale(
            ngMain, "Hex Base Y (world)", skHexDirY, skGridBaseLen_bu
        )
        nalign.Relative(skHexBaseX, (1, 1), skHexBaseY, (1, 0), tNodeSpace)

        skOrthoBaseY = nsh.vector.Scale(
            ngMain, "Ortho Base Y (world)", skOrthoDirY, skGridBaseLen_bu
        )
        nalign.Relative(skHexBaseY, (1, 1), skOrthoBaseY, (1, 0), tNodeSpace)

        ###############################################################
        # Re-align Geometry and Object Info

        # nalign.Relative(skGridDistZ_bu, (0, 0), lGeoInfo, (0, 1), tNodeSpace)
        # nalign.Relative(skGridRelOrigVec, (1, 0), lObjInfo, (1, 1), tNodeSpace)

        ###############################################################
        # Links to output

        ngMain.links.new(skHexDirX, nodOut.inputs[sHexDirX])
        ngMain.links.new(skHexDirY, nodOut.inputs[sHexDirY])
        ngMain.links.new(skOrthoDirY, nodOut.inputs[sOrthoDirY])

        ngMain.links.new(skHexBaseX, nodOut.inputs[sHexBaseX])
        ngMain.links.new(skHexBaseY, nodOut.inputs[sHexBaseY])
        ngMain.links.new(skOrthoBaseY, nodOut.inputs[sOrthoBaseY])

        nalign.Relative(skGridOrigVec, (1.5, 0), nodOut, (0, 1), tNodeSpace)

    # endif

    return ngMain


# enddef
