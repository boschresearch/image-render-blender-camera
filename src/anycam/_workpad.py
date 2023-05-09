#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \_workpad.py
# Created Date: Wednesday, June 9th 2021, 6:00:36 pm
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

# %%
import numpy as np

aA = np.arange(4 * 2)
aA.shape = (4, 2)

# print(aA)
# print("")
# print(aA[np.argmin(aA[:, 0], axis=0)])

lA = aA.tolist()
# print(lA)

aB = np.array([(x[0], x[1]) for x in lA], dtype=[("x", "f4"), ("y", "f4")])
print(aB)
# print([[x["x"], x["y"]] for x in aB])
np.append([aB["x"]], [aB["y"]], axis=0).transpose()

# aD = np.array([0, 0])
# aS = np.array([2, 3])

# print(aA)

# aX = (aA + aD) * aS
# print(aX)

# for aX in aA:
# 	print(aX)
# # endfor
# print(np.append(aA, np.array([[1, 2, 3]]), axis=0))
# print(np.empty((0, 3)).shape)

# aX = np.empty((2, 3))
# aX[0] = np.array([1, 2, 3])
# print(aX)
