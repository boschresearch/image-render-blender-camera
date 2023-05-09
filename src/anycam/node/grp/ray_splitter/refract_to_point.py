#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /refract_to_point.py
# Created Date: Thursday, October 22nd 2020, 2:51:29 pm
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
# Functions for shader node group: Refract to Point
import bpy
from anyblend.node import align as nalign
from anyblend.node import shader as nsh
from .. import render_pars

# from . import rand_2d as modGrpRand2d

##########################################################
# Create group


def Create(bForce=False):
    """
    Create shader node group to refract incoming ray to a given point.
    Optional Parameters:
        Force: Renew node tree even if group already exists.
    """

    # Create the name for the sensor specs shade node tree
    sGrpName = "AnyCam.RaySplitter.RefractToPoint.v2"

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
        sFracPosX = "Frac Pos X"
        sFracPosY = "Frac Pos Y"
        sFracBaseX = "Frac Base X"
        sFracBaseY = "Frac Base Y"
        sCtrPosX = "Ctr Pos X"
        sCtrPosY = "Ctr Pos Y"
        sPosBaseX = "Pos Base X"
        sPosBaseY = "Pos Base Y"
        sOrigin = "Origin (world)"
        sMaxRadius_bu = "Max Radius (bu)"

        lInputs = [
            [sFracPosX, "NodeSocketFloat", 1.0],
            [sFracPosY, "NodeSocketFloat", 1.0],
            [sFracBaseX, "NodeSocketVector", (0, 0, 0)],
            [sFracBaseY, "NodeSocketVector", (0, 0, 0)],
            [sCtrPosX, "NodeSocketFloat", 1.0],
            [sCtrPosY, "NodeSocketFloat", 1.0],
            [sPosBaseX, "NodeSocketVector", (0, 0, 0)],
            [sPosBaseY, "NodeSocketVector", (0, 0, 0)],
            [sOrigin, "NodeSocketVector", (0, 0, 0)],
            [sMaxRadius_bu, "NodeSocketFloat", 1.0],
        ]

        # Define Output
        sBSDF = "BSDF"
        sRayDir = "Ray Direction"
        sNormal = "Sensor Normal"
        lOutputs = [
            [sBSDF, "NodeSocketShader"],
            [sRayDir, "NodeSocketVector"],
            [sNormal, "NodeSocketVector"],
        ]

        # Add group inputs if necessary and set default values
        nodIn = nsh.utils.ProvideNodeTreeInputs(ngMain, lInputs)

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, lOutputs)

        nodIn.location = (-400, 0)

        skCtrPosX = nodIn.outputs[sCtrPosX]
        skCtrPosY = nodIn.outputs[sCtrPosY]
        skFracPosX = nodIn.outputs[sFracPosX]
        skFracPosY = nodIn.outputs[sFracPosY]

        skPosBaseX = nodIn.outputs[sPosBaseX]
        skPosBaseY = nodIn.outputs[sPosBaseY]
        skFracBaseX = nodIn.outputs[sFracBaseX]
        skFracBaseY = nodIn.outputs[sFracBaseY]

        skOrigin = nodIn.outputs[sOrigin]

        skMaxRadius_bu = nodIn.outputs[sMaxRadius_bu]

        # Add Geometry Info Shader
        lGeoInfo = nsh.utils.Geometry(ngMain)
        nalign.Relative(nodIn, (1, 2), lGeoInfo, (1, 0), tNodeSpace)

        ###############################################################

        ## Randomize 2d fraction position
        # ngRand2d = nsh.utils.Group(ngMain, modGrpRand2d.Create())
        # nalign.Relative(nodIn, (2, 0), ngRand2d, (0, 2), tNodeSpace)
        # ngMain.links.new(skFracPosX, ngRand2d.inputs[0])
        # ngMain.links.new(skFracPosY, ngRand2d.inputs[1])

        # Calculate fraction position
        skFracVec = nsh.vector.LinComb2(ngMain, "Frac Vector", skFracBaseX, skFracPosX, skFracBaseY, skFracPosY)
        nalign.Relative(nodIn, (1, 0), skFracVec, (0, 1), tNodeSpace)

        # Calculate relative central position
        skRelCtrVec = nsh.vector.LinComb2(ngMain, "Rel Ctr Vec", skPosBaseX, skCtrPosX, skPosBaseY, skCtrPosY)
        nalign.Relative(skFracVec, (1, 1), skRelCtrVec, (1, 0), tNodeSpace)

        ###############################################################
        # Refraction Normal

        skRelPos = nsh.vector.Add(ngMain, "Rel Pos", skFracVec, skRelCtrVec)
        nalign.Relative(skRelCtrVec, (1, 0), skRelPos, (0, 0), tNodeSpace)

        skPos = nsh.vector.Add(ngMain, "Abs Pos", skRelPos, skOrigin)
        nalign.Relative(skRelPos, (1, 1), skPos, (1, 0), tNodeSpace)

        skLocalPos = nsh.vector.TransformPointWorldToObject(ngMain, "Local Position", lGeoInfo["Position"])
        nalign.Relative(lGeoInfo, (1, 0), skLocalPos, (0, 0), tNodeSpace)

        skLocalNorm = nsh.vector.TransformNormalWorldToObject(ngMain, "Local Normal", lGeoInfo["Normal"])
        nalign.Relative(skLocalPos, (0, 1), skLocalNorm, (0, 0), tNodeSpace)
        ngMain.links.new(skLocalNorm, nodOut.inputs[sNormal])

        skLocalIncoming = nsh.vector.TransformNormalWorldToObject(ngMain, "Local Incoming", lGeoInfo["Incoming"])
        nalign.Relative(skLocalNorm, (0, 1), skLocalIncoming, (0, 0), tNodeSpace)

        skVecToPos = nsh.vector.Subtract(ngMain, "Vector to Pos", skPos, skLocalPos)
        nalign.Relative(skPos, (1, 1), skVecToPos, (1, 0), tNodeSpace)

        skDirToPos = nsh.vector.Normalize(ngMain, "Direction to Pos", skVecToPos)
        nalign.Relative(skVecToPos, (1, 1), skDirToPos, (1, 0), tNodeSpace)

        skRefVec = nsh.vector.LinComb2(ngMain, "Refraction Vector", skDirToPos, -1.0, skLocalIncoming, -0.1)
        nalign.Relative(skDirToPos, (1, 1), skRefVec, (1, 0), tNodeSpace)

        skRefNorm = nsh.vector.Normalize(ngMain, "Refraction Normal", skRefVec)
        nalign.Relative(skRefVec, (1, 0), skRefNorm, (0, 0), tNodeSpace)

        skRefNormWorld = nsh.vector.TransformNormalObjectToWorld(ngMain, "Ref. Norm. World", skRefNorm)
        nalign.Relative(skRefNorm, (1, 0), skRefNormWorld, (0, 0), tNodeSpace)

        skRefBsdf = nsh.bsdf.RefractionSharp(ngMain, "Refraction BSDF", (1, 1, 1, 1), 10.0, skRefNormWorld)
        nalign.Relative(skRefNormWorld, (1, 0), skRefBsdf, (0, 0), tNodeSpace)

        ###############################################################
        # Within aperture?

        skRelRad2 = nsh.vector.Dot(ngMain, "Rel Radus Squared", skRelPos, skRelPos)
        nalign.Relative(skRelPos, (1, 0), skRelRad2, (0, 0), tNodeSpace)

        skRelRad = nsh.math.Power(ngMain, "Rel Radius", skRelRad2, 0.5)
        nalign.Relative(skRelRad2, (1, 1), skRelRad, (1, 0), tNodeSpace)

        skIsInside = nsh.math.IsLessThan(ngMain, "Is Inside", skRelRad, skMaxRadius_bu)
        nalign.Relative(skRelRad, (1, 1), skIsInside, (1, 0), tNodeSpace)

        ###############################################################
        # Output BSDF

        skBlackBsdf = nsh.bsdf.Transparent(ngMain, "Aperture", (0, 0, 0, 1))
        nalign.Relative(skRefBsdf, (1, 0), skBlackBsdf, (1, 1), tNodeSpace)

        skMixBsdf = nsh.bsdf.Mix(ngMain, "Mix", skIsInside, skBlackBsdf, skRefBsdf)
        nalign.Relative(skBlackBsdf, (1, 0), skMixBsdf, (0, 1), tNodeSpace)

        ###############################################################
        # Links to output

        ngMain.links.new(skMixBsdf, nodOut.inputs[sBSDF])
        ngMain.links.new(skDirToPos, nodOut.inputs[sRayDir])
        # ngMain.links.new(lGeoInfo['Normal'], nodOut.inputs[sNormal])

        nalign.Relative(skMixBsdf, (1, 0), nodOut, (0, 0), tNodeSpace)
    # endif

    return ngMain


# enddef
