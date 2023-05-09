#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /hex0.py
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
# Functions for shader node group: Hex Ray Splitter with single center
import bpy
from anyblend.node import align as nalign
from anyblend.node import shader as nsh

from .. import sensor_dims as modGrpSensDims

from . import pupil_grid_hex as modGrpPupilGridHex
from . import refract_to_point as modGrpRefToPoint
from . import pixel_frac as modGrpPixelFrac

##########################################################
# Create group


def Create(bForce=False):
    """
    Create shader node group for single center ray splitter bsdf.
    Optional Parameters:
        Force: Renew node tree even if group already exists.
    """

    if bForce:
        print("Hex0: Force")

    # Create the name for the sensor specs shade node tree
    sGrpName = "AnyCam.RaySplitter.Hex0.v2"

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
        tNodeSpace = (70, 25)
        tNodeSpaceSmall = (30, 15)

        # Remove all nodes that may be present
        for nod in ngMain.nodes:
            ngMain.nodes.remove(nod)
        # endfor

        # Define inputs
        sPupilDia_mm = "Pupil Diameter (mm)"
        sPupilDistZ_mm = "Pupil Distance Z (mm)"
        sPixCntX = "Pixel Count X"
        sPixCntY = "Pixel Count Y"
        sPixSize_um = "Pixel Size (um)"

        lInputs = [
            [sPupilDia_mm, "NodeSocketFloat", 1.0],
            [sPupilDistZ_mm, "NodeSocketFloat", 1.0],
            [sPixCntX, "NodeSocketFloat", 1.0],
            [sPixCntY, "NodeSocketFloat", 1.0],
            [sPixSize_um, "NodeSocketFloat", 1.0],
        ]

        # Define Output
        sRayDir = "Ray Direction"
        sSensorNormal = "Sensor Normal"
        sIsCtrRay = "Is Center Ray"
        sBSDF = "BSDF"

        lOutputs = [
            [sRayDir, "NodeSocketVector"],
            [sSensorNormal, "NodeSocketVector"],
            [sIsCtrRay, "NodeSocketFloat"],
            [sBSDF, "NodeSocketShader"],
        ]

        # Add group inputs if necessary and set default values
        nodIn = nsh.utils.ProvideNodeTreeInputs(ngMain, lInputs)

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, lOutputs)

        nodIn.location = (-400, 0)
        nodIn.width *= 2

        skPupilDia_mm = nodIn.outputs[sPupilDia_mm]
        skPupilDistZ_mm = nodIn.outputs[sPupilDistZ_mm]
        skPixCntX = nodIn.outputs[sPixCntX]
        skPixCntY = nodIn.outputs[sPixCntY]
        skPixSize_um = nodIn.outputs[sPixSize_um]

        ###############################################################

        # Pupil Grid Hex
        ngPupilGridHex = nsh.utils.Group(
            ngMain, modGrpPupilGridHex.Create(bForce=bForce)
        )
        nalign.Relative(nodIn, (1, 0), ngPupilGridHex, (0, 1.3), tNodeSpace)

        ngMain.links.new(skPupilDia_mm, ngPupilGridHex.inputs[0])
        ngMain.links.new(skPupilDistZ_mm, ngPupilGridHex.inputs[1])
        ngPupilGridHex.inputs[2].default_value = 1.0

        # Sensor Pars
        ngSensDims = nsh.utils.Group(ngMain, modGrpSensDims.Create(bForce=bForce))
        nalign.Relative(nodIn, (1, 0), ngSensDims, (0, 0), tNodeSpace)

        ngMain.links.new(skPixCntX, ngSensDims.inputs[0])
        ngMain.links.new(skPixCntY, ngSensDims.inputs[1])
        ngMain.links.new(skPixSize_um, ngSensDims.inputs[2])

        # Evaluate Fraction Position
        ngPixFrac = nsh.utils.Group(ngMain, modGrpPixelFrac.Create(bForce=bForce))
        nalign.Relative(ngSensDims, (1, 0), ngPixFrac, (0, 0), tNodeSpace)

        ngMain.links.new(
            ngPupilGridHex.outputs["Hex Dir X"], ngPixFrac.inputs["Dir X (local)"]
        )
        ngMain.links.new(
            ngPupilGridHex.outputs["Ortho Dir Y"], ngPixFrac.inputs["Dir Y (local)"]
        )

        ngMain.links.new(
            ngSensDims.outputs["Pixel Size (bu)"], ngPixFrac.inputs["Pixels Size (bu)"]
        )
        ngMain.links.new(
            ngSensDims.outputs["Sensor Half Width (bu)"],
            ngPixFrac.inputs["Half Width (bu)"],
        )
        ngMain.links.new(
            ngSensDims.outputs["Sensor Half Height (bu)"],
            ngPixFrac.inputs["Half Height (bu)"],
        )

        # Refract to point
        ngRefToPnt = nsh.utils.Group(ngMain, modGrpRefToPoint.Create(bForce=bForce))
        nalign.Relative(ngPixFrac, (1, 0), ngRefToPnt, (0, 1.3), tNodeSpace)

        sFracPosX = "Frac Pos X"
        sFracPosY = "Frac Pos Y"
        sFracBaseX = "Frac Base X"
        sFracBaseY = "Frac Base Y"
        sFracBaseY = "Frac Base Y"
        sCtrPosX = "Ctr Pos X"
        sCtrPosY = "Ctr Pos Y"
        sPosBaseX = "Pos Base X"
        sPosBaseY = "Pos Base Y"
        sOrigin = "Origin (world)"
        sMaxRadius_bu = "Max Radius (bu)"

        ngMain.links.new(ngPixFrac.outputs[0], ngRefToPnt.inputs[sFracPosX])
        ngMain.links.new(ngPixFrac.outputs[1], ngRefToPnt.inputs[sFracPosY])
        ngMain.links.new(
            ngPupilGridHex.outputs["Hex Base X"], ngRefToPnt.inputs[sFracBaseX]
        )
        ngMain.links.new(
            ngPupilGridHex.outputs["Ortho Base Y"], ngRefToPnt.inputs[sFracBaseY]
        )

        ngRefToPnt.inputs[sCtrPosX].default_value = 0.0
        ngRefToPnt.inputs[sCtrPosY].default_value = 0.0
        ngMain.links.new(
            ngPupilGridHex.outputs["Hex Base X"], ngRefToPnt.inputs[sPosBaseX]
        )
        ngMain.links.new(
            ngPupilGridHex.outputs["Hex Base Y"], ngRefToPnt.inputs[sPosBaseY]
        )

        ngMain.links.new(
            ngPupilGridHex.outputs["Grid Origin"], ngRefToPnt.inputs[sOrigin]
        )
        ngMain.links.new(
            ngPupilGridHex.outputs["Grid Radius (bu)"], ngRefToPnt.inputs[sMaxRadius_bu]
        )

        ###############################################################
        # Evaluate "Is central ray"

        skAbsFracX = nsh.math.Absolute(ngMain, "Abs Frac X", ngPixFrac.outputs[0])
        nalign.Relative(ngPixFrac, (1, 0), skAbsFracX, (0, 0), tNodeSpace)

        skIsNonZeroFracX = nsh.math.IsGreaterThan(
            ngMain, "Is Frac X != 0", skAbsFracX, 0.003
        )
        nalign.Relative(skAbsFracX, (1, 0), skIsNonZeroFracX, (0, 0), tNodeSpaceSmall)

        skAbsFracY = nsh.math.Absolute(ngMain, "Abs Frac Y", ngPixFrac.outputs[1])
        nalign.Relative(skAbsFracX, (1, 1), skAbsFracY, (1, 0), tNodeSpaceSmall)

        skIsNonZeroFracY = nsh.math.IsGreaterThan(
            ngMain, "Is Frac Y != 0", skAbsFracY, 0.003
        )
        nalign.Relative(skAbsFracY, (1, 0), skIsNonZeroFracY, (0, 0), tNodeSpaceSmall)

        skIsNotCtrRay = nsh.math.Add(
            ngMain, "Frac X or Y != 0", skIsNonZeroFracX, skIsNonZeroFracY, bClamp=True
        )
        nalign.Relative(
            skIsNonZeroFracX, (1, 0), skIsNotCtrRay, (0, 0), tNodeSpaceSmall
        )

        skIsCtrRay = nsh.math.Subtract(
            ngMain, "Frac X and Y == 0", 1.0, skIsNotCtrRay, bClamp=True
        )
        nalign.Relative(skIsNotCtrRay, (1, 0), skIsCtrRay, (0, 0), tNodeSpaceSmall)

        ###############################################################
        # Links to output

        ngMain.links.new(ngRefToPnt.outputs[0], nodOut.inputs[sBSDF])
        ngMain.links.new(ngRefToPnt.outputs[sRayDir], nodOut.inputs[sRayDir])
        ngMain.links.new(
            ngRefToPnt.outputs[sSensorNormal], nodOut.inputs[sSensorNormal]
        )
        ngMain.links.new(skIsCtrRay, nodOut.inputs[sIsCtrRay])

        nalign.Relative(ngRefToPnt, (1, 0), nodOut, (0, 0), tNodeSpace)
    # endif

    return ngMain


# enddef
