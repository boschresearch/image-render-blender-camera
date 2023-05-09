#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \mesh\test_frustum_ed.py
# Created Date: Tuesday, April 27th 2021, 1:19:16 pm
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

# Test creating an equidistant frustum

import bpy
from anycam.mesh import solids

fPixSize_mm = 0.003
iPixCntX = 2880
iPixCntY = 2000
lFov_deg = [193, 0]
fRayLen = 2.0
iResolution = 20

fSenSizeX_mm = fPixSize_mm * iPixCntX
fSenSizeY_mm = fPixSize_mm * iPixCntY
fFovMax_deg = max(lFov_deg)

colF = bpy.data.collections.get("Collection")
objF = solids.CreateFrustumPanoEquidist(
    "Test.Frustum",
    fSenSizeX_mm=fSenSizeX_mm,
    fSenSizeY_mm=fSenSizeY_mm,
    fFov_deg=fFovMax_deg,
    iResolution=iResolution,
    fRayLen=fRayLen,
)

colF.objects.link(objF)
