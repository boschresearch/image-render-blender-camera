#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \poly_radial.py
# Created Date: Tuesday, March 23rd 2021, 3:29:04 pm
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
from anybase.cls_any_error import CAnyError_Message
from dataclasses import dataclass

from anyblend.node import align as nalign
from anyblend.node import shader as nsh

# from anyblend.node.grp import polynomial as modGrpPoly
from anyblend.node.grp import ray_to_dir_v2 as modGrpRayToDir
from . import lut_fisheye_in_to_uv as modGrpInToUv

from anyblend.node.shader.utils import CNodeSocketCollection, CNodeSocketInfo


# Input Names
@dataclass(frozen=True)
class CInputs(CNodeSocketCollection):
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

    xVignettingInfluence: CNodeSocketInfo = CNodeSocketInfo(
        sName="Vignetting Influence", typSocket=bpy.types.NodeSocketFloat, xValue=1.0
    )


# endclass


@dataclass(frozen=True)
class COutputs(CNodeSocketCollection):
    xBSDF: CNodeSocketInfo = CNodeSocketInfo(sName="BSDF", typSocket=bpy.types.NodeSocketShader, xValue=None)


# endclass


def GetInputs():
    return CInputs()


# enddef


def GetOutputs():
    return COutputs()


# enddef


#################################################################################
def CreateName(*, _sSensorName):
    return "AnyCam.Ray.Lut.Fisheye.v1_{}".format(_sSensorName)


# endddef


#################################################################################
def Create(
    *,
    _sSensorName: str,
    _sImgLut: str,
    _bForce=False,
):
    """
    Create shader node group for shader of fisheye LUT.
    """

    # if bForce:
    #     print("LUT: Force")
    # # endif

    # Create name of node group
    sGrpName = CreateName(_sSensorName=_sSensorName)

    # Try to get ray splitter specification node group
    ngMain = bpy.data.node_groups.get(sGrpName)

    # ##!!! DEBUG
    # if ngMain is not None:
    #     print(f"DEBUG: removing node group '{ngMain.name}'")
    #     bpy.data.node_groups.remove(ngMain)
    #     ngMain = None
    # # endif
    # ##!!!

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
        for nod in ngMain.nodes:
            ngMain.nodes.remove(nod)
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

        try:
            ntToUV = modGrpInToUv.Create(_sSensorName=_sSensorName, _bForce=_bForce)
        except Exception as xEx:
            raise CAnyError_Message(sMsg="Error creating 'Incoming to UV' shader node group", xChildEx=xEx)
        # endtry

        xToUv_In = modGrpInToUv.GetInputs()
        xToUv_Out = modGrpInToUv.GetOutputs()

        # ###############################################################

        nosGeometry = nsh.utils.Geometry(ngMain)
        nalign.Relative(nodIn, (1, 0), nosGeometry, (1, 1), tNodeSpace)

        skVecIncoming = nsh.vector.TransformNormalWorldToObject(ngMain, "Incoming (local)", nosGeometry["Incoming"])
        nalign.Relative(nosGeometry, (1, 0), skVecIncoming, (0, 0), tNodeSpaceSmall)

        ngToUV = nsh.utils.Group(ngMain, ntToUV)
        nalign.Relative(skVecIncoming, (1, 1), ngToUV, (0, 0), tNodeSpaceSmall)

        ngMain.links.new(skVecIncoming, ngToUV.inputs[xToUv_In.xIncoming.sName])
        ngMain.links.new(nodIn.outputs[xIn.xLutMinAngleX_deg.sName], ngToUV.inputs[xToUv_In.xLutMinAngleX_deg.sName])
        ngMain.links.new(nodIn.outputs[xIn.xLutMaxAngleX_deg.sName], ngToUV.inputs[xToUv_In.xLutMaxAngleX_deg.sName])
        ngMain.links.new(nodIn.outputs[xIn.xLutMinAngleY_deg.sName], ngToUV.inputs[xToUv_In.xLutMinAngleY_deg.sName])
        ngMain.links.new(nodIn.outputs[xIn.xLutMaxAngleY_deg.sName], ngToUV.inputs[xToUv_In.xLutMaxAngleY_deg.sName])

        # Evaluate outgoing ray direction from LUT texture
        skTexImg = nsh.tex.Image(
            ngMain,
            "LUT",
            ngToUV.outputs[xToUv_Out.xUV.sName],
            _sImgLut,
            eExtension=nsh.tex.EExtension.EXTEND,
            eProjection=nsh.tex.EProjection.FLAT,
            eInterpolation=nsh.tex.EInterpolation.CUBIC,
            eColorSpace=nsh.tex.EColorSpace.NON_COLOR,
            eAlphaMode=nsh.tex.EAlphaMode.STRAIGHT,
        )
        nalign.Relative(ngToUV, (1, 0), skTexImg, (0, 0), tNodeSpace)

        skVigMix = nsh.math.MixFloat(
            ngMain, "Vig. Influence", nodIn.outputs[xIn.xVignettingInfluence.sName], 1.0, skTexImg["Alpha"]
        )
        nalign.Relative(skTexImg, (1, 1), skVigMix, (0, 1), tNodeSpaceSmall)

        skBSDF = nsh.bsdf.RayToDir(ngMain, "Ray To Direction", skVecIncoming, skTexImg["Color"], skVigMix)
        nalign.Relative(skTexImg, (1, 0), skBSDF, (0, 1), tNodeSpaceSmall)

        ngMain.links.new(skBSDF, nodOut.inputs[xOut.xBSDF.sName])
        nalign.Relative(skBSDF, (1, 0), nodOut, (0, 0), tNodeSpace)

    # endif

    return ngMain


# enddef
