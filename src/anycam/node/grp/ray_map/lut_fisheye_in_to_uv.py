#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \lut_fisheye_in_to_uv.py
# Created Date: Thursday, January 12th 2023, 8:20:10 am
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

import bpy
from typing import NamedTuple, Any
from dataclasses import dataclass
from anyblend.node import align as nalign
from anyblend.node import shader as nsh

from anyblend.node.shader.utils import CNodeSocketCollection, CNodeSocketInfo


# Input Names
@dataclass(frozen=True)
class CInputs(CNodeSocketCollection):
    xIncoming: CNodeSocketInfo = CNodeSocketInfo(
        sName="Incoming (local)", typSocket=bpy.types.NodeSocketVector, xValue=(0.0, 0.0, 0.0)
    )

    xLutMinAngleX_deg: CNodeSocketInfo = CNodeSocketInfo(
        sName="LUT Min. Angle X (deg)", typSocket=bpy.types.NodeSocketFloat, xValue=0.0
    )

    xLutMaxAngleX_deg: CNodeSocketInfo = CNodeSocketInfo(
        sName="LUT Max. Angle X (deg)", typSocket=bpy.types.NodeSocketFloat, xValue=0.0
    )

    xLutMinAngleY_deg: CNodeSocketInfo = CNodeSocketInfo(
        sName="LUT Min. Angle Y (deg)", typSocket=bpy.types.NodeSocketFloat, xValue=0.0
    )

    xLutMaxAngleY_deg: CNodeSocketInfo = CNodeSocketInfo(
        sName="LUT Max. Angle Y (deg)", typSocket=bpy.types.NodeSocketFloat, xValue=0.0
    )


# endclass


@dataclass(frozen=True)
class COutputs(CNodeSocketCollection):
    xUV: CNodeSocketInfo = CNodeSocketInfo(sName="UV", typSocket=bpy.types.NodeSocketVector, xValue=(0.0, 0.0, 0.0))


# endclass


def GetInputs():
    return CInputs()


# enddef


def GetOutputs():
    return COutputs()


# enddef


#################################################################################
def CreateName(*, _sSensorName):
    return "AnyCam.Ray.Lut.Fisheye.InToUV.v1_{}".format(_sSensorName)


# endddef


#################################################################################
def Create(
    *,
    _sSensorName: str,
    _bForce=False,
):
    """
    Create shader node group to calculate UV coordinates
    from incoming ray for fisheye LUT.
    """

    # if bForce:
    #     print("LUT: Force")
    # # endif

    # Create name of node group
    sGrpName: str = CreateName(_sSensorName=_sSensorName)

    # Try to get ray splitter specification node group
    ngMain: bpy.types.NodeTree = bpy.data.node_groups.get(sGrpName)

    # ##!!! DEBUG
    if ngMain is not None:
        print(f"DEBUG: removing node group '{ngMain.name}'")
        bpy.data.node_groups.remove(ngMain)
        ngMain = None
    # endif
    # ##!!!

    bUpdate: bool = None
    if ngMain is None:
        ngMain = bpy.data.node_groups.new(sGrpName, "ShaderNodeTree")
        bUpdate = True
    else:
        bUpdate = _bForce
    # endif

    if bUpdate is True:

        tNodeSpace = (70, 25)
        tNodeSpaceSmall = (30, 15)

        # Remove all nodes that may be present
        for nodX in ngMain.nodes:
            ngMain.nodes.remove(nodX)
        # endfor

        # Define inputs
        xIn = GetInputs()

        # Define Output
        xOut = GetOutputs()

        # Add group inputs if necessary and set default values
        nodIn = nsh.utils.ProvideNodeTreeInputs(ngMain, xIn)

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, xOut)

        nodIn.location = (-400, 0)
        nodIn.width *= 2

        # ###############################################################

        skLutAngleMinX_rad = nsh.math.Radians(ngMain, "LUT Min. X (rad)", nodIn.outputs[xIn.xLutMinAngleX_deg.sName])
        nalign.Relative(nodIn, (1, 1), skLutAngleMinX_rad, (0, 0), tNodeSpace)

        skLutAngleMaxX_rad = nsh.math.Radians(ngMain, "LUT Max. X (rad)", nodIn.outputs[xIn.xLutMaxAngleX_deg.sName])
        nalign.Relative(skLutAngleMinX_rad, (1, 1), skLutAngleMaxX_rad, (1, 0), tNodeSpaceSmall)

        skLutAngleMinY_rad = nsh.math.Radians(ngMain, "LUT Min. Y (rad)", nodIn.outputs[xIn.xLutMinAngleY_deg.sName])
        nalign.Relative(skLutAngleMaxX_rad, (1, 1), skLutAngleMinY_rad, (1, 0), tNodeSpaceSmall)

        skLutAngleMaxY_rad = nsh.math.Radians(ngMain, "LUT Max. Y (rad)", nodIn.outputs[xIn.xLutMaxAngleY_deg.sName])
        nalign.Relative(skLutAngleMinY_rad, (1, 1), skLutAngleMaxY_rad, (1, 0), tNodeSpaceSmall)

        # ############

        skLutAngleRangeX_rad = nsh.math.Subtract(ngMain, "LUT Range X (rad)", skLutAngleMaxX_rad, skLutAngleMinX_rad)
        nalign.Relative(skLutAngleMaxX_rad, (1, 0), skLutAngleRangeX_rad, (0, 0), tNodeSpaceSmall)

        skLutAngleRangeY_rad = nsh.math.Subtract(ngMain, "LUT Range Y (rad)", skLutAngleMaxY_rad, skLutAngleMinY_rad)
        nalign.Relative(skLutAngleMaxY_rad, (1, 0), skLutAngleRangeY_rad, (0, 0), tNodeSpaceSmall)

        # ############

        skIncomingRev = nsh.vector.Scale(ngMain, "Incoming Reverse", nodIn.outputs[xIn.xIncoming.sName], -1.0)
        nalign.Relative(nodIn, (1, 0), skIncomingRev, (0, 1), tNodeSpace)

        nosIncomingRevSep = nsh.vector.SeparateXYZ(ngMain, "In. Rev. Sep.", skIncomingRev)
        nalign.Relative(skIncomingRev, (1, 0), nosIncomingRevSep, (0, 0), tNodeSpaceSmall)

        skInZ = nsh.math.Multiply(ngMain, "Incoming Z", nosIncomingRevSep["Z"], -1.0)
        nalign.Relative(nosIncomingRevSep, (1, 0), skInZ, (0, 0), tNodeSpaceSmall)

        # ############

        skRayRadial = nsh.vector.CombineXYZ(ngMain, "Ray Radial", nosIncomingRevSep["X"], nosIncomingRevSep["Y"], 0.0)
        nalign.Relative(skIncomingRev, (1, 0), skRayRadial, (1, 1), tNodeSpace)

        skRayRadLen = nsh.vector.Length(ngMain, "Ray Radial Len.", skRayRadial)
        nalign.Relative(skRayRadial, (1, 0), skRayRadLen, (0, 0), tNodeSpaceSmall)

        skRayRadAngle = nsh.math.ArcTan2(ngMain, "Ray Radial Angle", skRayRadLen, skInZ)
        nalign.Relative(skRayRadLen, (1, 0), skRayRadAngle, (0, 0), tNodeSpaceSmall)

        skRayRadScale = nsh.math.Divide(ngMain, "Ray Radial Scale", skRayRadAngle, skRayRadLen)
        nalign.Relative(skRayRadAngle, (1, 0), skRayRadScale, (0, 0), tNodeSpaceSmall)

        skRayRadAngleXY = nsh.vector.Scale(ngMain, "Ray Radial Angle XY", skRayRadial, skRayRadScale)
        nalign.Relative(skRayRadScale, (1, 0), skRayRadAngleXY, (0, 0), tNodeSpaceSmall)

        nosRayRadAngleXYSep = nsh.vector.SeparateXYZ(ngMain, "Ray Rad. Angle. XY Sep", skRayRadAngleXY)
        nalign.Relative(skRayRadAngleXY, (1, 0), nosRayRadAngleXYSep, (0, 0), tNodeSpaceSmall)

        # ############

        skRayAngleRelToMinX = nsh.math.Subtract(
            ngMain, "Ray Angel Rel. to Min. X", nosRayRadAngleXYSep["X"], skLutAngleMinX_rad
        )
        nalign.Relative(nosRayRadAngleXYSep, (1, 1), skRayAngleRelToMinX, (0, 0), tNodeSpace)

        skRayU = nsh.math.Divide(ngMain, "Ray U", skRayAngleRelToMinX, skLutAngleRangeX_rad)
        nalign.Relative(skRayAngleRelToMinX, (1, 0), skRayU, (0, 0), tNodeSpaceSmall)

        skRayAngleRelToMinY = nsh.math.Subtract(
            ngMain, "Ray Angel Rel. to Min. Y", nosRayRadAngleXYSep["Y"], skLutAngleMinY_rad
        )
        nalign.Relative(skRayAngleRelToMinX, (1, 1), skRayAngleRelToMinY, (1, 0), tNodeSpaceSmall)

        skRayV = nsh.math.Divide(ngMain, "Ray V", skRayAngleRelToMinY, skLutAngleRangeY_rad)
        nalign.Relative(skRayAngleRelToMinY, (1, 0), skRayV, (0, 0), tNodeSpaceSmall)

        skUV = nsh.vector.CombineXYZ(ngMain, "UV", skRayU, skRayV, 0.0)
        nalign.Relative(skRayU, (1, 0), skUV, (0, 0), tNodeSpaceSmall)

        ngMain.links.new(skUV, nodOut.inputs[xOut.xUV.sName])
        nalign.Relative(skUV, (1, 0), nodOut, (0, 0), tNodeSpace)

    # endif

    return ngMain


# enddef
