#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \incident_ray.py
# Created Date: Tuesday, March 23rd 2021, 4:58:28 pm
# Author: Christian Perwass (CR/AEC5)
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


def Create(*, bForce=False):
    """
    Create shader node group to calculate the radius position and angle of incident ray.
    Optional Parameters:
        Force: Renew node tree even if group already exists.
    """

    # Create the name for the sensor specs shade node tree
    sGrpName = "AnyCam.Refractor.IndicentRayDataEx"

    # Try to get ray splitter specification node group
    ngMain = bpy.data.node_groups.get(sGrpName)

    ####!!! Debug
    # if ngMain is not None:
    #     bpy.data.node_groups.remove(ngMain)
    #     ngMain = None
    # # endif
    # bForce = Truen
    ####!!!

    if ngMain is None:
        ngMain = bpy.data.node_groups.new(sGrpName, "ShaderNodeTree")
        bUpdate = True
    else:
        bUpdate = bForce
    # endif

    if bUpdate == True:
        tNodeSpace = (50, 25)
        tNodeSpaceSmall = (25, 15)

        # Remove all nodes that may be present
        for nod in ngMain.nodes:
            ngMain.nodes.remove(nod)
        # endfor

        # Define inputs
        sOrigX_bu = "Origin X (bu)"
        sOrigY_bu = "Origin Y (bu)"
        lInputs = [
            [sOrigX_bu, "NodeSocketFloat", 0.0],
            [sOrigY_bu, "NodeSocketFloat", 0.0],
        ]

        # Define Output
        sIncidentAngle_rad = "Incident Angle (rad)"
        sRadius_bu = "Radius (bu)"
        sNormal = "Normal (local)"
        sTangent = "Tangent (local)"
        sIncoming = "Incoming (local)"

        lOutputs = [
            [sRadius_bu, "NodeSocketFloat"],
            [sIncidentAngle_rad, "NodeSocketFloat"],
            [sNormal, "NodeSocketVector"],
            [sTangent, "NodeSocketVector"],
            [sIncoming, "NodeSocketVector"],
        ]

        # Add group inputs if necessary and set default values
        nodIn = nsh.utils.ProvideNodeTreeInputs(ngMain, lInputs)

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, lOutputs)

        nodIn.location = (-400, 0)

        skOrigin = nsh.vector.CombineXYZ(ngMain, "Origin", nodIn.outputs[sOrigX_bu], nodIn.outputs[sOrigY_bu], 0.0)
        nalign.Relative(nodIn, (1, 0), skOrigin, (0, 0), tNodeSpace)

        # Add Geometry Info Shader
        lGeoInfo = nsh.utils.Geometry(ngMain)
        nalign.Relative(nodIn, (1, 1), lGeoInfo, (1, 0), tNodeSpace)

        skNormal = nsh.vector.TransformWorldToObject(ngMain, "Normal (local)", lGeoInfo["Normal"])
        nalign.Relative(lGeoInfo, (1, 1), skNormal, (0, 0), tNodeSpace)

        skIncoming = nsh.vector.TransformWorldToObject(ngMain, "Incoming (local)", lGeoInfo["Incoming"])
        nalign.Relative(skNormal, (0, 1), skIncoming, (0, 0), tNodeSpace)

        ngMain.links.new(skNormal, nodOut.inputs[sNormal])
        ngMain.links.new(skIncoming, nodOut.inputs[sIncoming])

        skPntObj = nsh.vector.TransformPointWorldToObject(ngMain, "Point on Object", lGeoInfo["Position"])
        nalign.Relative(lGeoInfo, (1, 0), skPntObj, (0, 0), tNodeSpace)

        skRelPnt = nsh.vector.Subtract(ngMain, "Point rel. to Origin", skPntObj, skOrigin)
        nalign.Relative(skPntObj, (1, 0), skRelPnt, (0, 0), tNodeSpaceSmall)

        skRad2 = nsh.vector.Dot(ngMain, "Radius^2", skRelPnt, skRelPnt)
        nalign.Relative(skRelPnt, (1, 0), skRad2, (0, 0), tNodeSpaceSmall)

        skRad = nsh.math.Sqrt(ngMain, "Radius", skRad2)
        nalign.Relative(skRad2, (1, 0), skRad, (0, 0), tNodeSpaceSmall)

        skCosAngle = nsh.vector.Dot(ngMain, "cos(Angle)", skNormal, skIncoming)
        nalign.Relative(skNormal, (1, 0), skCosAngle, (0, 0), tNodeSpace)

        skAngle = nsh.math.ArcCos(ngMain, "Angle", skCosAngle)
        nalign.Relative(skCosAngle, (1, 0), skAngle, (0, 0), tNodeSpaceSmall)

        # Evaluate tangent
        skProjIncNorm = nsh.vector.Project(ngMain, "Project Inc. on Norm.", skIncoming, skNormal)
        nalign.Relative(skIncoming, (0, 1), skProjIncNorm, (0, 0), tNodeSpace)

        skProjIncPlane = nsh.vector.Subtract(ngMain, "Project Inc. on Plane", skIncoming, skProjIncNorm)
        nalign.Relative(skProjIncNorm, (1, 0), skProjIncPlane, (0, 0), tNodeSpaceSmall)

        skTangent = nsh.vector.Normalize(ngMain, "Tangent", skProjIncPlane)
        nalign.Relative(skProjIncPlane, (1, 0), skTangent, (0, 0), tNodeSpaceSmall)

        ngMain.links.new(skTangent, nodOut.inputs[sTangent])

        # ###############################################################
        # # Links to output

        ngMain.links.new(skRad, nodOut.inputs[sRadius_bu])
        ngMain.links.new(skAngle, nodOut.inputs[sIncidentAngle_rad])

        nalign.Relative(skRad, (1, 1), nodOut, (0, 0), tNodeSpace)

    # endif

    return ngMain


# enddef
