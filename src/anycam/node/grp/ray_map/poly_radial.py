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

from . import incident_ray_ex as modGrpIncidentRay
from .. import poly_vignetting as modGrpVignetting


def Create(*, sSensorName, fNormRadius_mm, lCoef, lCenter_mm, fMaxAngle_deg, lVignettingCoef, bForce=False):
    """
    Create shader node group for single center ray splitter bsdf.
    Optional Parameters:
        Force: Renew node tree even if group already exists.
    """

    if bForce:
        print("Poly-Radial: Force")
    # endif

    iCoefCnt = len(lCoef)
    if iCoefCnt < 1:
        raise CAnyExcept("No polynomial coefficients given")
    # endif
    iVignettingCoefCnt = len(lVignettingCoef)
    # if iVignettingCoefCnt < 1:
    #    raise CAnyExcept("No vignetting coefficients given")

    # Create the name for the sensor specs shade node tree
    sGrpName = "AnyCam.Ray.Poly.Radial{0}.v2_{1}".format(iCoefCnt, sSensorName)

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
        sMaxAngle_deg = "Max. Angle (deg)"
        sNormRadius_mm = "Poly. Norm. Radius (mm)"
        lPolyCeofNames = ["Poly. Coef. {0:d}".format(i + 1) for i in range(iCoefCnt)]
        lVignetting = ["Vignetting Coef. {0:d}".format(i + 1) for i in range(iVignettingCoefCnt)]

        lInputs = [
            [sOriginX_mm, "NodeSocketFloat", lCenter_mm[0]],
            [sOriginY_mm, "NodeSocketFloat", lCenter_mm[1]],
            [sMaxAngle_deg, "NodeSocketFloat", fMaxAngle_deg],
            [sNormRadius_mm, "NodeSocketFloat", fNormRadius_mm],
        ]

        lInputs.extend([[lPolyCeofNames[i], "NodeSocketFloat", lCoef[i]] for i in range(len(lCoef))])
        lInputs.extend([[lVignetting[i], "NodeSocketFloat", lVignettingCoef[i]] for i in range(iVignettingCoefCnt)])

        # Define Output
        sBSDF = "BSDF"

        lOutputs = [[sBSDF, "NodeSocketShader"]]

        # Add group inputs if necessary and set default values
        nodIn = nsh.utils.ProvideNodeTreeInputs(ngMain, lInputs)

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, lOutputs)

        nodIn.location = (-400, 0)
        nodIn.width *= 2

        skNormRadius_mm = nodIn.outputs[sNormRadius_mm]
        lskPolyCoef = [nodIn.outputs[sName] for sName in lPolyCeofNames]

        # ###############################################################

        nalign.Relative(nodIn, (1, 0), nodRenderPars, (1, 1), tNodeSpace)

        skPolyNormRadius_bu = nsh.math.Multiply(ngMain, "Poly Norm Radius (bu)", skBUperMM, skNormRadius_mm)
        nalign.Relative(nodRenderPars, (1, 1), skPolyNormRadius_bu, (0, 1), tNodeSpace)

        skOriginY_bu = nsh.math.Multiply(ngMain, "Origin Y (bu)", skBUperMM, nodIn.outputs[sOriginY_mm])
        nalign.Relative(skPolyNormRadius_bu, (0, 0), skOriginY_bu, (0, 1), tNodeSpace)

        skOriginX_bu = nsh.math.Multiply(ngMain, "Origin X (bu)", skBUperMM, nodIn.outputs[sOriginX_mm])
        nalign.Relative(skOriginY_bu, (0, 0), skOriginX_bu, (0, 1), tNodeSpace)

        # Incident Ray Group
        ngIncidentRay = nsh.utils.Group(ngMain, modGrpIncidentRay.Create(bForce=bForce))
        nalign.Relative(skOriginX_bu, (1, 0), ngIncidentRay, (0, 0), tNodeSpace)

        ngMain.links.new(skOriginX_bu, ngIncidentRay.inputs["Origin X (bu)"])
        ngMain.links.new(skOriginY_bu, ngIncidentRay.inputs["Origin Y (bu)"])

        skNormRadius = nsh.math.Divide(
            ngMain,
            "Nomalized Radius",
            ngIncidentRay.outputs["Radius (bu)"],
            skPolyNormRadius_bu,
        )
        nalign.Relative(skPolyNormRadius_bu, (1, 0), skNormRadius, (0, 0), tNodeSpaceSmall)

        ngPoly = nsh.utils.Group(ngMain, modGrpPoly.Create(iCoefCnt=iCoefCnt + 1, bForce=bForce))
        nalign.Relative(skNormRadius, (1, 1), ngPoly, (0, 0), tNodeSpace)

        ngMain.links.new(skNormRadius, ngPoly.inputs[0])
        for iIdx, skPolyCoef in enumerate(lskPolyCoef):
            ngMain.links.new(skPolyCoef, ngPoly.inputs[iIdx + 2])
        # endfor

        skAngleDeg = nsh.math.Degrees(ngMain, "Theta2 (deg)", ngPoly.outputs[0])
        nalign.Relative(ngPoly, (1, 0), skAngleDeg, (0, 0), tNodeSpace)

        skIsAngleInvalid = nsh.math.IsGreaterThan(ngMain, "Is Angle Invalid", skAngleDeg, nodIn.outputs[sMaxAngle_deg])
        nalign.Relative(skAngleDeg, (1, 0), skIsAngleInvalid, (0, 0), tNodeSpaceSmall)

        # Evaluate outgoing ray direction
        skCosTh2 = nsh.math.Cosine(ngMain, "Cos(theta2)", ngPoly.outputs[0])
        nalign.Relative(ngIncidentRay, (1, 0), skCosTh2, (0, 0), tNodeSpace)

        skSinTh2 = nsh.math.Sine(ngMain, "Sin(theta2)", ngPoly.outputs[0])
        nalign.Relative(skCosTh2, (0, 1), skSinTh2, (0, 0), tNodeSpaceSmall)

        skOutRayNeg = nsh.vector.LinComb2(
            ngMain,
            "Neg. Outgoing Ray",
            ngIncidentRay.outputs["Normal (local)"],
            skCosTh2,
            ngIncidentRay.outputs["Tangent (local)"],
            skSinTh2,
        )
        nalign.Relative(skCosTh2, (1, 0), skOutRayNeg, (0, 0), tNodeSpaceSmall)

        skOutRay = nsh.vector.Scale(ngMain, "Outgoing Ray", skOutRayNeg, -1.0)
        nalign.Relative(skOutRayNeg, (1, 0), skOutRay, (0, 0), tNodeSpaceSmall)

        # BSDF
        skBsdfRayToDir = nsh.utils.Group(ngMain, modGrpRayToDir.Create(bForce=bForce))
        skBsdfRayToDir.name = "Ray"
        ngMain.links.new(
            ngIncidentRay.outputs["Incoming (local)"],
            skBsdfRayToDir.inputs["Incoming (local)"],
        )
        ngMain.links.new(skOutRay, skBsdfRayToDir.inputs["Outgoing (local)"])
        nalign.Relative(skOutRay, (1, 1), skBsdfRayToDir, (0, 0), tNodeSpace)

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

        skBsdfBlack = nsh.bsdf.Transparent(ngMain, "Black", (0, 0, 0, 1))
        skBsdfValidMix = nsh.bsdf.Mix(ngMain, "Valid Mix", skIsAngleInvalid, skBsdfMix, skBsdfBlack)
        nalign.Relative(skBsdfMix, (0, 1), skBsdfValidMix, (0, 0), tNodeSpace)
        nalign.Relative(skBsdfValidMix, (0, 1), skBsdfBlack, (0, 0), tNodeSpaceSmall)

        ngMain.links.new(skBsdfValidMix, nodOut.inputs[0])
        nalign.Relative(skBsdfValidMix, (1, 0), nodOut, (0, 0), tNodeSpace)

        # Vignetting
        skVignetting = nsh.utils.Group(ngMain, modGrpVignetting.Create(bForce=bForce))
        # Links
        ngMain.links.new(skNormRadius, skVignetting.inputs["radius"])
        ngMain.links.new(
            nodIn.outputs["Vignetting Coef. 1"],
            skVignetting.inputs["Vignetting Coef 1"],
        )
        ngMain.links.new(
            nodIn.outputs["Vignetting Coef. 2"],
            skVignetting.inputs["Vignetting Coef 2"],
        )
        ngMain.links.new(
            nodIn.outputs["Vignetting Coef. 3"],
            skVignetting.inputs["Vignetting Coef 3"],
        )

        ngMain.links.new(
            skVignetting.outputs["Value"],
            skBsdfRayToDir.inputs["Vignetting Correction"],
        )

    # endif

    return ngMain


# enddef
