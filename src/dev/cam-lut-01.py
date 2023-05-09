#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cam-lut-01.py
# Created Date: Monday, January 9th 2023, 9:39:31 am
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

import sys
from pathlib import Path
from anycam.model.cls_camera_lut import CCameraLut

sPath = sys.argv[1]
print(sPath)

xCamLut = CCameraLut()
xCamLut.FromFile(_xFilePath=sPath, _iLutBorderPixel=0, _iLutSuperSampling=1)


print("End")
