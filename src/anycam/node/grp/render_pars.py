#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /render_pars.py
# Created Date: Thursday, October 22nd 2020, 2:51:23 pm
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

################################################################
# Create global parameter node group
# Creates a node group with a set of value nodes that contain global rendering parameters.
def Create(bForce=False, iWavelength=None, fScale=None):
    """
    Create render parameters. Only those paramters that are given in kwargs are also modified.

    Named Parameters:
        Wavelength (float, [300, 800]):
            The wavelength of light in nano meters.

        Scale (float):
            It is assumed that all values in the lens system dictionary are given in millimeters.
            The unit settings in the current scene are used to calculate the correct scale factor
            from millimeters to blender units. The scale given here is multiplied with this internal scale.
    """

    # Try to get render parameter node group
    ngPars = bpy.data.node_groups.get("AnyCam.RenderPars_v01")

    if ngPars is None:
        ngPars = bpy.data.node_groups.new("AnyCam.RenderPars_v01", "ShaderNodeTree")
        bUpdate = True
    else:
        bUpdate = bForce
    # endif

    if bUpdate == True:
        tNodeSpace = (100, 15)

        for nod in ngPars.nodes:
            ngPars.nodes.remove(nod)
        # endfor

        nodOut = ngPars.nodes.new("NodeGroupOutput")
        nodOut.location = (300, 0)
        if ngPars.outputs.get("Wavelength") is None:
            ngPars.outputs.new("NodeSocketFloat", "Wavelength")
        # endif

        if ngPars.outputs.get("BU_per_MM") is None:
            ngPars.outputs.new("NodeSocketFloat", "BU_per_MM")
        # endif

        nodPar1 = ngPars.nodes.new("ShaderNodeValue")
        nalign.SetNodePosToLeftOf(nodOut, nodPar1, tNodeSpace)
        nodPar1.label = "Wavelength"
        nodPar1.name = "Wavelength"
        nodPar1.outputs[0].default_value = 520
        ngPars.links.new(nodPar1.outputs[0], nodOut.inputs["Wavelength"])

        nodPar2 = ngPars.nodes.new("ShaderNodeValue")
        nalign.SetNodePosToBelowOf(nodPar1, nodPar2, tNodeSpace)
        nodPar2.label = "BU_per_MM"
        nodPar2.name = "BU_per_MM"
        nodPar2.outputs[0].default_value = 1e-3 / bpy.context.scene.unit_settings.scale_length
        ngPars.links.new(nodPar2.outputs[0], nodOut.inputs["BU_per_MM"])
    # endif

    # Update Values if given
    if iWavelength is not None:
        nodWave = ngPars.nodes["Wavelength"]
        nodWave.outputs[0].default_value = iWavelength
    # endif

    if fScale is not None:
        nodPar = ngPars.nodes["BU_per_MM"]
        nodPar.outputs[0].default_value = fScale * 1e-3 / bpy.context.scene.unit_settings.scale_length
    # endif

    return ngPars


# enddef

################################################################
# Set node group parameters


def SetValues(iWavelength=None, fScale=None):

    # Try to get render parameter node group
    ngPars = bpy.data.node_groups.get("AnyCam.RenderPars_v01")
    if ngPars is None:
        return False
    # endif

    # Update Values if given
    if iWavelength is not None:
        nodWave = ngPars.nodes["Wavelength"]
        nodWave.outputs[0].default_value = iWavelength
    # endif

    if fScale is not None:
        nodPar = ngPars.nodes["BU_per_MM"]
        nodPar.outputs[0].default_value = fScale * 1e-3 / bpy.context.scene.unit_settings.scale_length
    # endif

    return True


# enddef

################################################################
# Get Wavelength


def GetWavelength():

    # Try to get render parameter node group
    ngPars = bpy.data.node_groups.get("AnyCam.RenderPars_v01")
    if ngPars is None:
        return False
    # endif

    nodWave = ngPars.nodes["Wavelength"]
    return nodWave.outputs[0].default_value


# enddef

################################################################
# Set Wavelength
def SetWavelength(iWavelength):

    # Try to get render parameter node group
    ngPars = bpy.data.node_groups.get("AnyCam.RenderPars_v01")
    if ngPars is None:
        return False
    # endif

    nodWave = ngPars.nodes["Wavelength"]
    nodWave.outputs[0].default_value = float(iWavelength)


# enddef
