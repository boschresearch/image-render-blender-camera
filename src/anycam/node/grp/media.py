#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /media.py
# Created Date: Thursday, October 22nd 2020, 2:51:21 pm
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

import bpy
from anyblend.node import align as nalign

#################################################################
# Create/Update node groups for refractive media
# Creates node groups that return the refractive index of a medium
# depending on the wavelength stored in the render parameters node group.
#
def Update(_dicGlassCatalog):

    # Try to get the render parameter node group
    #    xGrpPars = bpy.data.node_groups.get('RenderPars_v01')
    #    if xGrpPars is None:
    #        return
    #    # endif

    for sGlass in _dicGlassCatalog:
        dicGlass = _dicGlassCatalog[sGlass]
        # print(dicGlass)
        sName = sGlass
        dicRefIdx = dicGlass["mRefIdx"]

        # Sort IORs by wavelength
        lWaves = sorted(dicRefIdx.keys())
        # print(lWaves)

        c_iWaveMin = 300
        c_iWaveMax = 1200

        # if there is only a single element, then use this IOR as constant value
        # for all wavelengths
        iWaveCnt = len(lWaves)
        if iWaveCnt == 1:
            if dicRefIdx.get(c_iWaveMin) is None:
                dicRefIdx[c_iWaveMin] = dicRefIdx[lWaves[0]]
            # endif
            if dicRefIdx.get(c_iWaveMax) is None:
                dicRefIdx[c_iWaveMax] = dicRefIdx[lWaves[0]]
            # endif
        else:
            # Extrapolate IOR at wavelength 300nm
            iWave0 = lWaves[0]
            iWave1 = lWaves[1]
            fRef0 = dicRefIdx[iWave0]
            fRef1 = dicRefIdx[iWave1]
            fSlope = (fRef1 - fRef0) / (iWave1 - iWave0)
            dicRefIdx[c_iWaveMin] = fSlope * (c_iWaveMin - iWave0) + fRef0

            # Extrapolate IOR at wavelength 800nm
            iWave0 = lWaves[iWaveCnt - 2]
            iWave1 = lWaves[iWaveCnt - 1]
            fRef0 = dicRefIdx[iWave0]
            fRef1 = dicRefIdx[iWave1]
            fSlope = (fRef1 - fRef0) / (iWave1 - iWave0)
            dicRefIdx[c_iWaveMax] = fSlope * (c_iWaveMax - iWave0) + fRef0
        # endif

        lWaves = sorted(dicRefIdx.keys())
        fRefMin = dicRefIdx[c_iWaveMin]
        fRefMax = dicRefIdx[c_iWaveMax]
        fRefRange = fRefMax - fRefMin
        fWaveRange = float(c_iWaveMax - c_iWaveMin)

        sName = "AnyCam.RefractMedium." + sName
        xGrp = bpy.data.node_groups.get(sName)

        # Add medium node group if it does not already exist
        if xGrp is None:
            # Create node group
            xGrp = bpy.data.node_groups.new(sName, "ShaderNodeTree")

            # Create output node
            xGrp.outputs.new("NodeSocketFloat", "IOR")
            xGrp.inputs.new("NodeSocketFloat", "Wavelength")
        # endif

        # Remove all nodes to ensure proper update
        for node in xGrp.nodes:
            xGrp.nodes.remove(node)
        # endfor

        tNodSpace = (50, 25)

        nodIn = xGrp.nodes.new("NodeGroupInput")
        nodIn.location = (0, 0)

        # Subtract c_iWaveMin from input Wavelength
        nodMath1 = xGrp.nodes.new("ShaderNodeMath")
        nalign.SetNodePosToRightOf(nodIn, nodMath1, tNodSpace)
        nodMath1.operation = "SUBTRACT"
        nodMath1.inputs[1].default_value = c_iWaveMin
        xGrp.links.new(nodIn.outputs["Wavelength"], nodMath1.inputs[0])

        # Divide by wavelength range
        nodMath2 = xGrp.nodes.new("ShaderNodeMath")
        nalign.SetNodePosToBelowOf(nodMath1, nodMath2, tNodSpace)
        nodMath2.operation = "DIVIDE"
        nodMath2.use_clamp = True
        nodMath2.inputs[1].default_value = fWaveRange
        xGrp.links.new(nodMath1.outputs[0], nodMath2.inputs[0])

        # Add color map to map wavelength to refractive index
        nodColMap = xGrp.nodes.new("ShaderNodeValToRGB")
        nalign.SetNodePosToRightOf(nodMath1, nodColMap, tNodSpace)
        xGrp.links.new(nodMath2.outputs[0], nodColMap.inputs[0])

        xColRamp = nodColMap.color_ramp
        xColRamp.color_mode = "RGB"
        xColRamp.interpolation = "LINEAR"

        iElCnt = len(xColRamp.elements)
        iElIdx = 0
        for iWave in lWaves:
            fWaveVal = (iWave - c_iWaveMin) / fWaveRange
            if abs(fRefRange) < 1e-7:
                fRefVal = 0.0
            else:
                fRefVal = (dicRefIdx[iWave] - fRefMin) / fRefRange

            if iElIdx >= iElCnt:
                xColEl = xColRamp.elements.new(fWaveVal)
            else:
                xColEl = xColRamp.elements[iElIdx]
                xColEl.position = fWaveVal
            # endif
            xColEl.color = (1.0, 1.0, 1.0, fRefVal)

            iElIdx += 1
        # endfor

        # Multiply color ramp alpha channel result with refractive range
        nodMath3 = xGrp.nodes.new("ShaderNodeMath")
        nalign.SetNodePosToRightOf(nodColMap, nodMath3, tNodSpace)
        nodMath3.operation = "MULTIPLY"
        nodMath3.inputs[1].default_value = fRefRange
        xGrp.links.new(nodColMap.outputs["Alpha"], nodMath3.inputs[0])

        # Add minimal refractive index
        nodMath4 = xGrp.nodes.new("ShaderNodeMath")
        nalign.SetNodePosToBelowOf(nodMath3, nodMath4, tNodSpace)
        nodMath4.operation = "ADD"
        nodMath4.inputs[1].default_value = fRefMin
        xGrp.links.new(nodMath3.outputs[0], nodMath4.inputs[0])

        # Group output
        nodOut = xGrp.nodes.new("NodeGroupOutput")
        nalign.SetNodePosToRightOf(nodMath3, nodOut, tNodSpace)
        xGrp.links.new(nodMath4.outputs[0], nodOut.inputs[0])

    # endfor


# enddef
