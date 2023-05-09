#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \material\cls_plastic.py
# Created Date: Tuesday, May 4th 2021, 8:35:47 am
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
from anyblend.cls_material import CMaterial

from anyblend.node import align as nalign
from anyblend.node import shader as nsh
from anyblend.node.grp import input as ngInput

#####################################################################
# @staticmethod
def CreateName(sId):
    return "AnyCam.Plastic.{0}".format(sId)


# enddef

#####################################################################
# Plastic material class
class CPlastic(CMaterial):
    def __init__(self, sName="Default", bForce=False):
        super().__init__(sName=CreateName(sName), bForce=bForce)

        if self._bNeedUpdate:
            self._Create(sName=sName, bForce=bForce)
        # endif

    # enddef

    #####################################################################
    def _Create(self, sName="", bForce=False):

        tNodeSpace = (50, 25)

        self._nodPrince = self.GetNode("Principled BSDF")
        xP = self._nodPrince.inputs
        xP["Subsurface"].default_value = 0.98
        xP["Roughness"].default_value = 0.15

        lInputs = [["Color", "NodeSocketColor", (1.0, 1.0, 1.0, 1.0)]]

        # sInputName = "AnyCam.Input.Plastic.{0}".format(sName)
        sInputName = "AnyCam.Input.Plastic"
        ngColIn = ngInput.Create(sName=sInputName, lSockets=lInputs, bForce=bForce)
        nodColIn = nsh.utils.Group(self.xNodeTree, ngColIn)

        nalign.Relative(self._nodPrince, (0, 0), nodColIn, (1, 0), tNodeSpace)
        self.CreateLink(xOut=nodColIn.outputs[0], xIn=self._nodPrince.inputs["Base Color"])
        self.CreateLink(xOut=nodColIn.outputs[0], xIn=self._nodPrince.inputs["Subsurface Color"])
        self._bNeedUpdate = False

    # enddef


# endclass
