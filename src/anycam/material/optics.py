#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /optics.py
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
# Materials for optical elements
import bpy
from anyblend.node import align as nalign

#################################################################
# Create Lens Aperture material
def GetAperture():

    matAperture = bpy.data.materials.get("AnyCam.LensAperture")

    # Create aperture material if it is not available
    if matAperture is None:
        matAperture = bpy.data.materials.new(name="AnyCam.LensAperture")
        matAperture.diffuse_color = (0.1, 0.1, 0.2, 1.0)

        matAperture.use_nodes = True
        lNodes = matAperture.node_tree.nodes
        for node in lNodes:
            lNodes.remove(node)

        nodTrans = lNodes.new(type="ShaderNodeBsdfTransparent")
        nodTrans.inputs[0].default_value = (0, 0, 0, 1)
        nodTrans.location = (0, 0)

        nodOut = lNodes.new(type="ShaderNodeOutputMaterial")
        nodOut.location = (400, 0)

        lLinks = matAperture.node_tree.links
        lLinks.new(nodTrans.outputs[0], nodOut.inputs[0])

    # endif

    return matAperture


# enddef

#################################################################
# Create Lens refraction material
# _fRefIdxOut: Refrective index for outside, i.e. region to which surface normals point.
# _fRefIdxIn: Refractive index for inside, i.e. region from which surface normals point away.


def GetRefract(_fRefIdxOut, _fRefIdxIn):

    fRefIdx = _fRefIdxIn / _fRefIdxOut
    sName = "AnyCam.LensRefract_{0:04d}".format(int(math.floor(fRefIdx * 1e3)))

    matRef = bpy.data.materials.get(sName)

    # Create aperture material if it is not available
    if matRef is None:
        matRef = bpy.data.materials.new(name=sName)
        matRef.diffuse_color = (0.9, 0.8, 0.8, 1.0)

        matRef.use_nodes = True
        lNodes = matRef.node_tree.nodes
        for node in lNodes:
            lNodes.remove(node)

        nodRef = lNodes.new(type="ShaderNodeBsdfRefraction")
        nodRef.distribution = "SHARP"
        nodRef.inputs[2].default_value = fRefIdx
        nodRef.location = (0, 0)

        nodOut = lNodes.new(type="ShaderNodeOutputMaterial")
        nodOut.location = (400, 0)

        lLinks = matRef.node_tree.links
        lLinks.new(nodRef.outputs[0], nodOut.inputs[0])

    # endif

    return matRef


# enddef

#################################################################
# Create Lens refraction material with dispersion
# _sMediumOut: Medium for outside, i.e. region to which surface normals point.
# _sMediumIn: Medium for inside, i.e. region from which surface normals point away.
# Number of refractive indices (IOR) given determines type of dispersion.
# IORs are paired up for inside and outside values.
# If single IOR is given, it is applied to all color channels.
# If three IORs are given, they are applied to RGB in this order.
# If four IORs are given, they are applied to RGBA in this order.


def GetRefractMedium(_sMediumOut, _sMediumIn):

    sName = "AnyCam.LensRefract_" + _sMediumIn + "_" + _sMediumOut

    # Calculate effective refractive indices for shader
    #    for iIdx in range(0, iRefIdxCnt):
    #        fRefIdx = _lRefIdxIn[iIdx] / _lRefIdxOut[iIdx]
    #        iRefIdxID = int(math.floor(fRefIdx * 1e3))
    #        lRefIdx.append(fRefIdx)
    #        sName += "_{0:04d}".format(iRefIdxID)
    #    # endfor

    matRef = bpy.data.materials.get(sName)

    #### !!! Debug: Always create material anew
    #    if matRef is not None:
    #        bpy.data.materials.remove(matRef)
    #        matRef = None
    #    # endif

    # Create aperture material if it is not available
    if matRef is None:

        # Try to get the render parameter node group
        xGrpPars = bpy.data.node_groups.get("AnyCam.RenderPars_v01")
        if xGrpPars is None:
            return None
        # endif

        xGrpMedIn = bpy.data.node_groups.get("AnyCam.RefractMedium." + _sMediumIn)
        if xGrpMedIn is None:
            return None
        # endif

        xGrpMedOut = bpy.data.node_groups.get("AnyCam.RefractMedium." + _sMediumOut)
        if xGrpMedOut is None:
            return None
        # endif

        # Create material
        matRef = bpy.data.materials.new(name=sName)

        matRef.use_nodes = True
        matRef.diffuse_color = (0.9, 0.8, 0.8, 1.0)

        lNodes = matRef.node_tree.nodes
        for node in lNodes:
            lNodes.remove(node)
        # endfor

        lLinks = matRef.node_tree.links
        for link in lLinks:
            lLinks.remove(link)
        # endfor

        tNodSpace = (50, 25)

        nodPars = lNodes.new("ShaderNodeGroup")
        nodPars.node_tree = xGrpPars
        nodPars.width *= 2
        nodPars.location = (0, 0)

        nodMedIn = lNodes.new("ShaderNodeGroup")
        nodMedIn.node_tree = xGrpMedIn
        nodMedIn.width *= 2
        nalign.SetNodePosToRightOf(nodPars, nodMedIn, tNodSpace)
        lLinks.new(nodPars.outputs[0], nodMedIn.inputs[0])

        nodMedOut = lNodes.new("ShaderNodeGroup")
        nodMedOut.node_tree = xGrpMedOut
        nodMedOut.width *= 2
        nalign.SetNodePosToBelowOf(nodMedIn, nodMedOut, tNodSpace)
        lLinks.new(nodPars.outputs[0], nodMedOut.inputs[0])

        nodMath1 = lNodes.new("ShaderNodeMath")
        nodMath1.operation = "DIVIDE"
        nalign.SetNodePosToRightOf(nodMedIn, nodMath1, tNodSpace)
        lLinks.new(nodMedIn.outputs[0], nodMath1.inputs[0])
        lLinks.new(nodMedOut.outputs[0], nodMath1.inputs[1])

        nodRef = lNodes.new(type="ShaderNodeBsdfRefraction")
        nodRef.distribution = "SHARP"
        nodRef.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        nalign.SetNodePosToRightOf(nodMath1, nodRef, tNodSpace)
        lLinks.new(nodMath1.outputs[0], nodRef.inputs["IOR"])

        nodOut = lNodes.new(type="ShaderNodeOutputMaterial")
        nalign.SetNodePosToRightOf(nodRef, nodOut, tNodSpace)
        lLinks.new(nodRef.outputs[0], nodOut.inputs[0])

    # endif

    return matRef


# enddef
