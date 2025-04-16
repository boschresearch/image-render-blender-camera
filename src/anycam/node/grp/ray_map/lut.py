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
from anybase.cls_anyexcept import CAnyExcept

from anyblend.node import align as nalign
from anyblend.node import shader as nsh

from anyblend.node.grp import polynomial as modGrpPoly
from anyblend.node.grp import ray_to_dir_v2 as modGrpRayToDir
from anyblend.node.shader import tex

from . import incident_ray_ex2 as modGrpIncidentRay
from .. import poly_vignetting as modGrpVignetting


#################################################################################
def CreateName(*, sSensorName, iVignettingCoefCnt):
    # Create the name for the sensor specs shade node tree
    if iVignettingCoefCnt == 0:
        sGrpName = "AnyCam.Ray.Lut.v1_{}".format(sSensorName)
    else:
        sGrpName = "AnyCam.Ray.Lut.Vig_{}.v1_{}".format(iVignettingCoefCnt, sSensorName)
    # endif

    return sGrpName


# endddef


#################################################################################
def Create(
    *,
    sSensorName,
    sImgLut,
    lCenter_mm,
    lSenSizeXY_pix,
    fPixSize_mm,
    fVignettingNormRadius_mm,
    lVignettingCoef,
    bForce=False
):
    """
    Create shader node group for single center ray splitter bsdf.
    Optional Parameters:
        Force: Renew node tree even if group already exists.
    """

    # if bForce:
    #     print("LUT: Force")
    # # endif

    if isinstance(lVignettingCoef, list):
        iVignettingCoefCnt = len(lVignettingCoef)
    else:
        iVignettingCoefCnt = 0
    # endif

    # Create name of node group
    sGrpName = CreateName(sSensorName=sSensorName, iVignettingCoefCnt=iVignettingCoefCnt)

    # Try to get ray splitter specification node group
    ngMain = bpy.data.node_groups.get(sGrpName)

    # ###!!! Debug
    # bpy.data.node_groups.remove(ngMain)
    # ngMain = None
    # ###!!!

    if ngMain is None:
        ngMain = bpy.data.node_groups.new(sGrpName, "ShaderNodeTree")
        bUpdate = True
    else:
        bUpdate = bForce
    # endif

    if bUpdate is True:

        tNodeSpace = (70, 25)
        tNodeSpaceSmall = (30, 15)

        # Remove all nodes that may be present
        for nod in ngMain.nodes:
            ngMain.nodes.remove(nod)
        # endfor

        # Try to get render parameter node group
        ngRenderPars = bpy.data.node_groups.get("AnyCam.RenderPars_v01")
        nodRenderPars = nsh.utils.Group(ngMain, ngRenderPars)
        skBUperMM = nodRenderPars.outputs[1]

        # Define inputs
        sOriginX_mm = "Origin X (mm)"
        sOriginY_mm = "Origin Y (mm)"
        sPixSize_mm = "Pixel Size (mm)"
        sPixCntX = "Pixel Count X"
        sPixCntY = "Pixel Count Y"

        lInputs = [
            [sOriginX_mm, "NodeSocketFloat", lCenter_mm[0]],
            [sOriginY_mm, "NodeSocketFloat", lCenter_mm[1]],
            [sPixSize_mm, "NodeSocketFloat", fPixSize_mm],
            [sPixCntX, "NodeSocketFloat", lSenSizeXY_pix[0]],
            [sPixCntY, "NodeSocketFloat", lSenSizeXY_pix[1]],
        ]

        if iVignettingCoefCnt > 0:
            sVigNormRadius_mm = "Vig. Norm. Radius (mm)"
            lVigCoefNames = ["Vignetting Coef. {0:d}".format(i + 1) for i in range(iVignettingCoefCnt)]

            lInputs.append([sVigNormRadius_mm, "NodeSocketFloat", fVignettingNormRadius_mm])
            lInputs.extend(
                [[lVigCoefNames[i], "NodeSocketFloat", lVignettingCoef[i]] for i in range(iVignettingCoefCnt)]
            )
            # print(lInputs)
        # endif

        # Define Output
        sBSDF = "BSDF"

        lOutputs = [[sBSDF, "NodeSocketShader"]]

        # Add group inputs if necessary and set default values
        nodIn = nsh.utils.ProvideNodeTreeInputs(ngMain, lInputs)

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, lOutputs)

        nodIn.location = (-400, 0)
        nodIn.width *= 2

        if iVignettingCoefCnt > 0:
            skVigNormRadius_mm = nodIn.outputs[sVigNormRadius_mm]
            lskVigCoef = [nodIn.outputs[sName] for sName in lVigCoefNames]
        # endif

        # ###############################################################

        nalign.Relative(nodIn, (1, 0), nodRenderPars, (1, 1), tNodeSpace)

        if iVignettingCoefCnt > 0:
            skVigNormRadius_bu = nsh.math.Multiply(ngMain, "Poly Norm Radius (bu)", skBUperMM, skVigNormRadius_mm)
            nalign.Relative(nodRenderPars, (1, 1), skVigNormRadius_bu, (0, 1), tNodeSpace)
            nodX = skVigNormRadius_bu
        else:
            nodX = nodRenderPars
        # endif

        skPixSize_bu = nsh.math.Multiply(ngMain, "Pixel Size (bu)", skBUperMM, nodIn.outputs[sPixSize_mm])
        nalign.Relative(nodX, (1, 1), skPixSize_bu, (0, 1), tNodeSpace)

        skOriginY_bu = nsh.math.Multiply(ngMain, "Origin Y (bu)", skBUperMM, nodIn.outputs[sOriginY_mm])
        nalign.Relative(skPixSize_bu, (0, 0), skOriginY_bu, (0, 1), tNodeSpace)

        skOriginX_bu = nsh.math.Multiply(ngMain, "Origin X (bu)", skBUperMM, nodIn.outputs[sOriginX_mm])
        nalign.Relative(skOriginY_bu, (0, 0), skOriginX_bu, (0, 1), tNodeSpace)

        # Incident Ray Group
        ngIncidentRay = nsh.utils.Group(ngMain, modGrpIncidentRay.Create(bForce=bForce))
        nalign.Relative(skOriginX_bu, (1, 0), ngIncidentRay, (0, 0), tNodeSpace)

        ngMain.links.new(skOriginX_bu, ngIncidentRay.inputs["Origin X (bu)"])
        ngMain.links.new(skOriginY_bu, ngIncidentRay.inputs["Origin Y (bu)"])
        ngMain.links.new(skPixSize_bu, ngIncidentRay.inputs["Pixel Size (bu)"])
        ngMain.links.new(nodIn.outputs[sPixCntX], ngIncidentRay.inputs["Pixel Count X"])
        ngMain.links.new(nodIn.outputs[sPixCntY], ngIncidentRay.inputs["Pixel Count Y"])

        if iVignettingCoefCnt > 0:
            skNormRadius = nsh.math.Divide(
                ngMain,
                "Nomalized Radius",
                ngIncidentRay.outputs["Radius (bu)"],
                skVigNormRadius_bu,
            )
            nalign.Relative(skVigNormRadius_bu, (1, 0), skNormRadius, (0, 0), tNodeSpaceSmall)

            iPolyCoefCnt = iVignettingCoefCnt * 2 + 1
            ngPoly = nsh.utils.Group(ngMain, modGrpPoly.Create(iCoefCnt=iPolyCoefCnt, bForce=bForce))
            nalign.Relative(skNormRadius, (1, 1), ngPoly, (0, 0), tNodeSpace)

            ngPoly.inputs[1].default_value = 1.0

            ngMain.links.new(skNormRadius, ngPoly.inputs[0])
            for iIdx, skPolyCoef in enumerate(lskVigCoef):
                ngMain.links.new(skPolyCoef, ngPoly.inputs[2 * iIdx + 3])
            # endfor

            skVigFac = nsh.math.Divide(ngMain, "Vignetting Factor", 1.0, ngPoly.outputs[0])
            nalign.Relative(ngPoly, (1, 0), skVigFac, (0, 0), tNodeSpaceSmall)
        # endif

        # Evaluate outgoing ray direction from LUT texture
        skTexImg = nsh.tex.Image(
            ngMain,
            "LUT",
            ngIncidentRay.outputs["UV Coord"],
            sImgLut,
            eExtension=tex.EExtension.EXTEND
        )
        nalign.Relative(ngIncidentRay, (1, 1), skTexImg, (0, 0), tNodeSpace)

        # BSDF
        skBsdfRayToDir = nsh.utils.Group(ngMain, modGrpRayToDir.Create(bForce=bForce))
        skBsdfRayToDir.name = "Ray"
        ngMain.links.new(
            ngIncidentRay.outputs["Incoming (local)"],
            skBsdfRayToDir.inputs["Incoming (local)"],
        )
        ngMain.links.new(skTexImg["Color"], skBsdfRayToDir.inputs["Outgoing (local)"])
        nalign.Relative(skTexImg, (1, 1), skBsdfRayToDir, (0, 0), tNodeSpace)

        skBsdfTransparent = nsh.bsdf.Transparent(ngMain, "Transparent", (1, 1, 1, 1))
        nalign.Relative(skBsdfRayToDir, (1, 0), skBsdfTransparent, (1, 1), (5, 5))

        lskLightPath = nsh.utils.LightPath(ngMain)
        nalign.Relative(skBsdfTransparent, (0, 0), lskLightPath, (0, 1), tNodeSpace)

        skBsdfMix = nsh.bsdf.Mix(
            ngMain,
            "Mix",
            lskLightPath["Is Camera Ray"],
            skBsdfTransparent,
            skBsdfRayToDir.outputs["BSDF"],
        )
        nalign.Relative(skBsdfTransparent, (1, 0), skBsdfMix, (0, 0), tNodeSpace)

        ngMain.links.new(skBsdfMix, nodOut.inputs[0])
        nalign.Relative(skBsdfMix, (1, 0), nodOut, (0, 0), tNodeSpace)

        if iVignettingCoefCnt > 0:
            ngMain.links.new(skVigFac, skBsdfRayToDir.inputs["Vignetting Correction"])
        # endif
    # endif

    return ngMain


# enddef
