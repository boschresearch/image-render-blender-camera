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
from ..node.grp.ray_map import lut as modLut


# Hexagonal sampling grid


def Create(
    *,
    sId,
    sImgLut,
    lSenSizeXY_pix,
    fPixSize_mm,
    lCenter_mm,
    fVignettingNormRadius_mm=None,
    lVignettingCoef=None,
    bForce=False
):

    if len(lCenter_mm) != 2:
        raise CAnyExcept("Invalid number of elements in center position parameter")
    # endif

    if lVignettingCoef is not None:
        if fVignettingNormRadius_mm is None:
            fVignettingNormRadius_mm = 1.0
        # endif

        iVigCoefCnt = len(lVignettingCoef)
        sMatName = "AnyCam.Ray.Lut.Vig_{}.v1_{}".format(iVigCoefCnt, sId)
    else:
        sMatName = "AnyCam.Ray.Lut.v1_{}".format(sId)
    # endif

    matRF = bpy.data.materials.get(sMatName)

    sLutNodeGroupName = modLut.CreateName(
        sSensorName=sId, iVignettingCoefCnt=len(lVignettingCoef)
    )
    ngLut = bpy.data.node_groups.get(sLutNodeGroupName)

    if matRF is None or ngLut is None:
        if ngLut is not None:
            bpy.data.node_groups.remove(ngLut)
        # endif

        if matRF is not None:
            bpy.data.materials.remove(matRF)
        # endif

        matRF = bpy.data.materials.new(name=sMatName)
        matRF.diffuse_color = (0.9, 0.1, 0.1, 1.0)
        bUpdate = True
    else:
        bUpdate = bForce
    # endif

    if bUpdate is True:
        tNodeSpace = (50, 25)

        matRF.use_nodes = True
        ngMain = matRF.node_tree

        for node in ngMain.nodes:
            ngMain.nodes.remove(node)
        # endfor

        lMatOut = nsh.utils.Material(ngMain)

        ngLut = modLut.Create(
            sSensorName=sId,
            sImgLut=sImgLut,
            lCenter_mm=lCenter_mm,
            lSenSizeXY_pix=lSenSizeXY_pix,
            fPixSize_mm=fPixSize_mm,
            fVignettingNormRadius_mm=fVignettingNormRadius_mm,
            lVignettingCoef=lVignettingCoef,
            bForce=bForce,
        )
        nodLUT = nsh.utils.Group(ngMain, ngLut)

        nodLUT.location = (-400, 0)

        nalign.Relative(nodLUT, (1, 0), lMatOut, (0, 0), tNodeSpace)

        ngMain.links.new(nodLUT.outputs[0], lMatOut["Surface"])
    # endif

    return matRF, ngLut


# enddef
