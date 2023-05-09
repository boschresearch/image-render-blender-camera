#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /objective_pars.py
# Created Date: Thursday, October 22nd 2020, 2:51:22 pm
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
# Create node group that contains objective parameters

import bpy
from anyblend.node import align as nalign
from anyblend.node import shader as nsh

################################################################
#
# Creates a node group with a set of value nodes that contain
# sensor specification values.
#
def Create(_dicLensSys, bForce=False):
    """
    Expects _dicLensSys to contain the following elements:
        sName: The objective name
        fRenderPupilDia: The diameter of the rendering pupil in mm
        fRenderPupilDistZ: The distance of the rendering pupil along
                            optical axis from infinity focus point.
    """

    # Create the name for the sensor specs shade node tree
    sGrpName = "AnyCam.ObjectivePars." + _dicLensSys["sName"].replace(" ", "_")

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

        sRenderPupilDia_mm = "Render Pupil Diameter (mm)"
        sRenderPupilDistZ_mm = "Render Pupil Distance Z (mm)"

        # Define Output
        lOutputs = [
            [sRenderPupilDia_mm, "NodeSocketFloat"],
            [sRenderPupilDistZ_mm, "NodeSocketFloat"],
        ]

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, lOutputs)

        skRenderPupilDia_mm = nsh.utils.Value(
            ngMain, sRenderPupilDia_mm, _dicLensSys["fRenderPupilDia"]
        )
        skRenderPupilDistZ_mm = nsh.utils.Value(
            ngMain, sRenderPupilDistZ_mm, _dicLensSys["fRenderPupilDistZ"]
        )

        ngMain.links.new(skRenderPupilDia_mm, nodOut.inputs[sRenderPupilDia_mm])
        ngMain.links.new(skRenderPupilDistZ_mm, nodOut.inputs[sRenderPupilDistZ_mm])

        skRenderPupilDia_mm.node.location = (0, 0)
        nalign.Relative(
            skRenderPupilDia_mm, (1, 1), skRenderPupilDistZ_mm, (1, 0), tNodeSpace
        )
        nalign.Relative(skRenderPupilDia_mm, (1, 0), nodOut, (0, 0), tNodeSpace)

    # endif

    return ngMain


# enddef
