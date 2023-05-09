#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /ray_poly_radial.py
# Created Date: Thursday, October 22nd 2020, 2:51:16 pm
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

############################################################
# Refractor Materials
import bpy
from anybase.cls_anyexcept import CAnyExcept
from anyblend.node import align as nalign
from anyblend.node import shader as nsh
from ..node.grp.ray_map import poly_radial as modPolyRadial


# Hexagonal sampling grid


def Create(
    *,
    sId,
    fNormRadius_mm,
    lCoef,
    lCenter_mm,
    fMaxAngle_deg,
    lVignetting=None,
    bForce=False
):

    iCoefCnt = len(lCoef)
    if iCoefCnt < 1:
        raise CAnyExcept(
            "Unsupported polynomial coefficient count: {0}".format(iCoefCnt)
        )
    # endif

    if len(lCenter_mm) != 2:
        raise CAnyExcept("Invalid number of elements in center position parameter")
    # endif

    sMatName = "AnyCam.Ray.Poly.Radial{0}_{1}".format(iCoefCnt, sId)
    matRF = bpy.data.materials.get(sMatName)

    if matRF is None:
        matRF = bpy.data.materials.new(name=sMatName)
        matRF.diffuse_color = (0.9, 0.1, 0.1, 1.0)
        bUpdate = True
    else:
        bUpdate = bForce
    # endif

    if lVignetting is None:
        lVignetting = [0.0, 0.0, 0.0]  # assume no vignetting in current model

    if bUpdate is True:

        tNodeSpace = (50, 25)

        matRF.use_nodes = True
        ngMain = matRF.node_tree

        for node in ngMain.nodes:
            ngMain.nodes.remove(node)
        # endfor

        lMatOut = nsh.utils.Material(ngMain)

        nodPolyRadial = nsh.utils.Group(
            ngMain,
            modPolyRadial.Create(
                sSensorName=sId,
                fNormRadius_mm=fNormRadius_mm,
                lCoef=lCoef,
                lCenter_mm=lCenter_mm,
                fMaxAngle_deg=fMaxAngle_deg,
                lVignettingCoef=lVignetting,
                bForce=bForce,
            ),
        )

        nodPolyRadial.location = (-400, 0)

        nalign.Relative(nodPolyRadial, (1, 0), lMatOut, (0, 0), tNodeSpace)

        ngMain.links.new(nodPolyRadial.outputs[0], lMatOut["Surface"])
    # endif

    return matRF


# enddef
