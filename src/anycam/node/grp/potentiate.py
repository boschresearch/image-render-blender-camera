#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \incident_ray.py
# Created Date: Tuesday, March 23rd 2021, 4:58:28 pm
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

##########################################################
# Node group to calculate polynomial
import bpy
from anybase.cls_anyexcept import CAnyExcept
from anyblend.node import align as nalign
from anyblend.node import shader as nsh

##########################################################
# Create powers of an input


def Create(*, iMaxPower, bForce=False):
    """
    Create shader node group to calculate a polynomial.
    Optional Parameters:
        Force: Renew node tree even if group already exists.
    """

    if iMaxPower < 1:
        raise CAnyExcept("The maximum power must be at least 1")
    # endif

    # Create the name for the sensor specs shade node tree
    sGrpName = "AnyCam.Potentiate.deg{0:d}".format(iMaxPower)

    # Try to get ray splitter specification node group
    ngMain = bpy.data.node_groups.get(sGrpName)

    ####!!! Debug
    # bpy.data.node_groups.remove(ngMain)
    # ngMain = None
    ####!!!

    if ngMain is None:
        ngMain = bpy.data.node_groups.new(sGrpName, "ShaderNodeTree")
        bUpdate = True
    else:
        bUpdate = bForce
    # endif

    if bUpdate == True:
        tNodeSpace = (50, 25)

        # Remove all nodes that may be present
        for nod in ngMain.nodes:
            ngMain.nodes.remove(nod)
        # endfor

        # Define inputs
        sValueIn = "Value"
        lInputs = [
            [sValueIn, "NodeSocketFloat", 0.0],
        ]

        # Define Output
        lPowerNames = ["X{0:d}".format(i + 1) for i in range(iMaxPower)]
        lOutputs = [[lPowerNames[i], "NodeSocketFloat", 0.0] for i in range(iMaxPower)]

        # Add group inputs if necessary and set default values
        nodIn = nsh.utils.ProvideNodeTreeInputs(ngMain, lInputs)

        # Add group outputs if necessary
        nodOut = nsh.utils.ProvideNodeTreeOutputs(ngMain, lOutputs)

        nodIn.location = (-400, 0)

        # ###############################################################
        lskX = [nodIn.outputs[0]]

        ngMain.links.new(lskX[0], nodOut.inputs[0])

        lskX.append(nsh.math.Multiply(ngMain, "X2", lskX[0], lskX[0]))
        lskX[1].node.hide = True
        nalign.Relative(nodIn, (1, 1), lskX[1], (0, 0), tNodeSpace)
        ngMain.links.new(lskX[1], nodOut.inputs[1])

        for iPower in range(2, iMaxPower):
            lskX.append(
                nsh.math.Multiply(
                    ngMain, "X{0:d}".format(iPower + 1), lskX[0], lskX[iPower - 1]
                )
            )
            lskX[iPower].node.hide = True
            # nalign.Relative(lskX[iPower-1], (1, 1), lskX[iPower], (1, 0), tNodeSpace)
            tLoc = lskX[iPower - 1].node.location
            lskX[iPower].node.location = (tLoc[0], tLoc[1] - 35)
            ngMain.links.new(lskX[iPower], nodOut.inputs[iPower])
        # endfor

        nalign.Relative(lskX[1], (1, 0), nodOut, (0, 0), tNodeSpace)
    # endif

    return ngMain


# enddef
