#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /ray_poly_radial.py
# Created Date: Wednesday, January 11th 2023, 10:52:55 am
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
from ..node.grp.ray_map import lut_fisheye as modLut


def Create(
    *,
    _sId: str,
    _sImgLut: str,
    _tLutAngleRangeX_deg: tuple[float, float],
    _tLutAngleRangeY_deg: tuple[float, float],
    _bForce: bool = False
):

    sMatName = "AnyCam.Ray.Lut.Fisheye.v1_{}".format(_sId)

    matRF = bpy.data.materials.get(sMatName)

    sLutNodeGroupName = modLut.CreateName(_sSensorName=_sId)
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
        bUpdate = _bForce
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
            _sSensorName=_sId,
            _sImgLut=_sImgLut,
            _bForce=_bForce,
        )
        nodLUT = nsh.utils.Group(ngMain, ngLut)
        nodLUT.location = (-400, 0)

        xLutIn = modLut.GetInputs()
        nodLUT.inputs[xLutIn.xLutMinAngleX_deg.sName].default_value = _tLutAngleRangeX_deg[0]
        nodLUT.inputs[xLutIn.xLutMaxAngleX_deg.sName].default_value = _tLutAngleRangeX_deg[1]
        nodLUT.inputs[xLutIn.xLutMinAngleY_deg.sName].default_value = _tLutAngleRangeY_deg[0]
        nodLUT.inputs[xLutIn.xLutMaxAngleY_deg.sName].default_value = _tLutAngleRangeY_deg[1]
        nodLUT.inputs[xLutIn.xVignettingInfluence.sName].default_value = 1.0

        # print(ngLut.inputs[xLutIn.xLutMinAngleX_deg.sName].default_value)
        # print(ngLut.inputs[xLutIn.xLutMaxAngleX_deg.sName].default_value)
        # print(ngLut.inputs[xLutIn.xLutMinAngleY_deg.sName].default_value)
        # print(ngLut.inputs[xLutIn.xLutMaxAngleY_deg.sName].default_value)

        nalign.Relative(nodLUT, (1, 0), lMatOut, (0, 0), tNodeSpace)

        ngMain.links.new(nodLUT.outputs[0], lMatOut["Surface"])
    # endif

    return matRF, ngLut


# enddef
