#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /ray_splitter.py
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
# Ray Splitter Materials
import bpy
from anyblend.node import align as nalign
from anyblend.node import shader as nsh
from anyblend.node.grp import ray_to_dir_v2 as modGrpRayToDir

from ..node.grp.ray_splitter import hex0 as modGrpHex0
from ..node.grp import render_pars as modGrpRenderPars

# Hexagonal sampling grid
def Hex(iHexRingCnt, sSensorName, sObjectiveName, bForce=False):

    sMatName = "AnyCam.RaySplitter.Hex{0:d}.v2_".format(int(iHexRingCnt))
    sMatName += sSensorName
    sMatName += "_"
    sMatName += sObjectiveName

    matRS = bpy.data.materials.get(sMatName)

    if matRS is None:
        matRS = bpy.data.materials.new(name=sMatName)
        matRS.diffuse_color = (0.9, 0.1, 0.1, 1.0)
        bUpdate = True
    else:
        bUpdate = bForce
    # endif

    if bUpdate == True:

        # Select appropriate Hex node group
        if iHexRingCnt == 0:
            modGrpHex = modGrpHex0
        else:
            return None
        # endif

        # Try to get sensor parameter node group
        sSenParsName = "AnyCam.SensorPars." + sSensorName
        ngSenPars = bpy.data.node_groups.get(sSenParsName)

        if ngSenPars is None:
            return None
        # endif

        # Try to get objective pars node group
        sObjectiveParsName = "AnyCam.ObjectivePars." + sObjectiveName
        ngObjectivePars = bpy.data.node_groups.get(sObjectiveParsName)

        if ngObjectivePars is None:
            return None
        # endif

        tNodeSpace = (50, 25)

        matRS.use_nodes = True
        ngMain = matRS.node_tree

        for node in ngMain.nodes:
            ngMain.nodes.remove(node)
        # endfor

        lMatOut = nsh.utils.Material(ngMain)

        # Sensor Pars
        nodSenPars = nsh.utils.Group(ngMain, ngSenPars)
        nodSenPars.location = (-400, 0)

        # Objective Pars
        nodObjPars = nsh.utils.Group(ngMain, ngObjectivePars)
        nalign.Relative(nodSenPars, (1, 0), nodObjPars, (1, 1), tNodeSpace)

        # Hex Grid
        nodHex = nsh.utils.Group(ngMain, modGrpHex.Create(bForce=bForce))
        nalign.Relative(nodSenPars, (1, 1), nodHex, (0, 1.5), tNodeSpace)

        sPupilDia_mm = "Pupil Diameter (mm)"
        sPupilDistZ_mm = "Pupil Distance Z (mm)"
        sPixCntX = "Pixel Count X"
        sPixCntY = "Pixel Count Y"
        sPixSize = "Pixel Size (um)"

        sRenderPupilDia_mm = "Render Pupil Diameter (mm)"
        sRenderPupilDistZ_mm = "Render Pupil Distance Z (mm)"

        ngMain.links.new(nodObjPars.outputs[sRenderPupilDia_mm], nodHex.inputs[sPupilDia_mm])
        ngMain.links.new(nodObjPars.outputs[sRenderPupilDistZ_mm], nodHex.inputs[sPupilDistZ_mm])

        ngMain.links.new(nodSenPars.outputs[sPixCntX], nodHex.inputs[sPixCntX])
        ngMain.links.new(nodSenPars.outputs[sPixCntY], nodHex.inputs[sPixCntY])
        ngMain.links.new(nodSenPars.outputs[sPixSize], nodHex.inputs[sPixSize])

        # Suppress zero pixel fraction rays
        skEmitBlack = nsh.bsdf.Emission(ngMain, "Black", (0, 0, 0, 1), 1.0)
        nalign.Relative(nodHex, (1, 1.2), skEmitBlack, (1, 0), tNodeSpace)

        skAllowRay = nsh.bsdf.Mix(
            ngMain,
            "Allow Ray",
            nodHex.outputs["Is Center Ray"],
            nodHex.outputs["BSDF"],
            skEmitBlack,
        )
        nalign.Relative(nodHex, (1, 0), skAllowRay, (0, 0), tNodeSpace)

        # Make Ray Splitter appear transparent for non-camera rays
        skTransparent = nsh.bsdf.Transparent(ngMain, "Transparent", (1, 1, 1, 1))
        nalign.Relative(skAllowRay, (1, 0), skTransparent, (1, 0.8), tNodeSpace)

        lLightPath = nsh.utils.LightPath(ngMain)
        nalign.Relative(skTransparent, (1, 0), lLightPath, (1, 1.2), tNodeSpace)

        skCamRay = nsh.bsdf.Mix(ngMain, "Camera Ray", lLightPath["Is Camera Ray"], skTransparent, skAllowRay)
        nalign.Relative(skAllowRay, (1, 0), skCamRay, (0, 0), tNodeSpace)

        ngMain.links.new(skCamRay, lMatOut["Surface"])
        nalign.Relative(skCamRay, (1, 0), lMatOut, (0, 0), tNodeSpace)

    # endif

    return matRS


# enddef


##############################################################################################################
# Simple Ray Splitter
def Simple(sSensorName, sObjectiveName, bForce=False):

    ### DEBUG ###
    # bForce = True
    #############

    sMatName = "AnyCam.RaySplitter.Simple.v1_"
    sMatName += sSensorName
    sMatName += "_"
    sMatName += sObjectiveName

    matRS = bpy.data.materials.get(sMatName)

    if matRS is None:
        matRS = bpy.data.materials.new(name=sMatName)
        matRS.diffuse_color = (0.9, 0.1, 0.1, 1.0)
        bUpdate = True
    else:
        bUpdate = bForce
    # endif

    if bUpdate == True:

        # Try to get sensor parameter node group
        sSenParsName = "AnyCam.SensorPars." + sSensorName
        ngSenPars = bpy.data.node_groups.get(sSenParsName)

        if ngSenPars is None:
            return None
        # endif

        # Try to get objective pars node group
        sObjectiveParsName = "AnyCam.ObjectivePars." + sObjectiveName
        ngObjectivePars = bpy.data.node_groups.get(sObjectiveParsName)

        if ngObjectivePars is None:
            return None
        # endif

        # Create or get render pars group
        ngRenderPars = modGrpRenderPars.Create()

        # Ray To Dir Group
        ngRayToDir = modGrpRayToDir.Create()

        tNodeSpaceS = (30, 20)
        tNodeSpace = (50, 25)
        tNodeSpaceXL = (100, 35)

        matRS.use_nodes = True
        ngMain = matRS.node_tree

        for node in ngMain.nodes:
            ngMain.nodes.remove(node)
        # endfor

        lMatOut = nsh.utils.Material(ngMain)

        # Sensor Pars
        nodSenPars = nsh.utils.Group(ngMain, ngSenPars)
        nodSenPars.location = (-400, 0)

        # Objective Pars
        nodObjPars = nsh.utils.Group(ngMain, ngObjectivePars)
        nalign.Relative(nodSenPars, (1, 0), nodObjPars, (1, 1), tNodeSpace)

        # Render Pars
        nodRndPars = nsh.utils.Group(ngMain, ngRenderPars)
        nalign.Relative(nodObjPars, (1, 0), nodRndPars, (1, 1), tNodeSpace)

        sPixCntX = "Pixel Count X"
        sPixCntY = "Pixel Count Y"
        sPixSize = "Pixel Size (um)"

        sRenderPupilDia_mm = "Render Pupil Diameter (mm)"
        sRenderPupilDistZ_mm = "Render Pupil Distance Z (mm)"

        # ########################################################
        # Evaluate pixel size in BU
        skPixSize_mm = nsh.math.Multiply(ngMain, "Pixel Size (mm)", nodSenPars.outputs[sPixSize], 0.001)
        nalign.Relative(nodSenPars, (1, 0), skPixSize_mm, (0, 0), tNodeSpace)

        skPixSize_bu = nsh.math.Multiply(ngMain, "Pixel Size (bu)", skPixSize_mm, nodRndPars.outputs["BU_per_MM"])
        nalign.Relative(skPixSize_mm, (1, 0), skPixSize_bu, (0, 0), tNodeSpaceS)

        skPixSizeHalf_bu = nsh.math.Multiply(ngMain, "Half Pixel Size (bu)", skPixSize_bu, 0.5)
        nalign.Relative(skPixSize_bu, (0, 1), skPixSizeHalf_bu, (0, 0), tNodeSpaceS)

        # ########################################################
        # Position Vector
        skGeo = nsh.utils.Geometry(ngMain)
        nalign.Relative(nodSenPars, (0, 1), skGeo, (0, 0), tNodeSpace)

        skPosObj = nsh.vector.TransformPointWorldToObject(ngMain, "Pos. on Splitter", skGeo["Position"])
        nalign.Relative(skGeo, (1, 0), skPosObj, (0, 0), tNodeSpaceS)

        skPosObjSep = nsh.vector.SeparateXYZ(ngMain, "Pos. Coords.", skPosObj)
        nalign.Relative(skPosObj, (0, 1), skPosObjSep, (0, 0), tNodeSpaceS)

        # ########################################################
        # Pupil Measures in BU
        skPupilDist_bu = nsh.math.Multiply(
            ngMain,
            "Pupil dist. (bu)",
            nodRndPars.outputs["BU_per_MM"],
            nodObjPars.outputs[sRenderPupilDistZ_mm],
        )
        nalign.Relative(nodRndPars, (1, 0), skPupilDist_bu, (0, 1), tNodeSpace)

        skPupilDia_bu = nsh.math.Multiply(
            ngMain,
            "Pupil dia. (bu)",
            nodRndPars.outputs["BU_per_MM"],
            nodObjPars.outputs[sRenderPupilDia_mm],
        )
        nalign.Relative(skPupilDist_bu, (0, 1), skPupilDia_bu, (0, 0), tNodeSpaceS)

        # ########################################################
        # Outgoing Coord. X
        skPixCtrX_S1 = nsh.math.Add(ngMain, "Pix.Ctr.X Step 1", skPosObjSep["X"], skPixSizeHalf_bu)
        nalign.Relative(skPixSize_bu, (1, 0), skPixCtrX_S1, (0, 0), tNodeSpaceXL)

        skPixCtrX_S2 = nsh.math.Divide(ngMain, "Pix.Ctr.X Step 2", skPixCtrX_S1, skPixSize_bu)
        nalign.Relative(skPixCtrX_S1, (0, 1), skPixCtrX_S2, (0, 0), tNodeSpaceS)

        skPixCtrX_S3 = nsh.math.Floor(ngMain, "Pix.Ctr.X Step 3", skPixCtrX_S2)
        nalign.Relative(skPixCtrX_S2, (0, 1), skPixCtrX_S3, (0, 0), tNodeSpaceS)

        skPixCtrX_bu = nsh.math.Multiply(ngMain, "Pix.Ctr.X (bu)", skPixCtrX_S3, skPixSize_bu)
        nalign.Relative(skPixCtrX_S3, (0, 1), skPixCtrX_bu, (0, 0), tNodeSpaceS)

        skPixFracX_bu = nsh.math.Subtract(ngMain, "Pix.Frac.X (bu)", skPixCtrX_bu, skPosObjSep["X"])
        nalign.Relative(skPixCtrX_bu, (0, 1), skPixFracX_bu, (0, 0), tNodeSpace)

        skPixRelFracX = nsh.math.Divide(ngMain, "Pix.Rel.Frac.X", skPixFracX_bu, skPixSize_bu)
        nalign.Relative(skPixFracX_bu, (0, 1), skPixRelFracX, (0, 0), tNodeSpaceS)

        skPupilRelX_bu = nsh.math.Multiply(ngMain, "Pupil Rel.X (bu)", skPixRelFracX, skPupilDia_bu)
        nalign.Relative(skPixRelFracX, (0, 1), skPupilRelX_bu, (0, 0), tNodeSpaceS)

        # ########################################################
        # Outgoing Coord. Y
        skPixCtrY_S1 = nsh.math.Add(ngMain, "Pix.Ctr.Y Step 1", skPosObjSep["Y"], skPixSizeHalf_bu)
        nalign.Relative(skPixCtrX_S1, (1, 0), skPixCtrY_S1, (0, 0), tNodeSpaceXL)

        skPixCtrY_S2 = nsh.math.Divide(ngMain, "Pix.Ctr.Y Step 2", skPixCtrY_S1, skPixSize_bu)
        nalign.Relative(skPixCtrY_S1, (0, 1), skPixCtrY_S2, (0, 0), tNodeSpaceS)

        skPixCtrY_S3 = nsh.math.Floor(ngMain, "Pix.Ctr.Y Step 3", skPixCtrY_S2)
        nalign.Relative(skPixCtrY_S2, (0, 1), skPixCtrY_S3, (0, 0), tNodeSpaceS)

        skPixCtrY_bu = nsh.math.Multiply(ngMain, "Pix.Ctr.Y (bu)", skPixCtrY_S3, skPixSize_bu)
        nalign.Relative(skPixCtrY_S3, (0, 1), skPixCtrY_bu, (0, 0), tNodeSpaceS)

        skPixFracY_bu = nsh.math.Subtract(ngMain, "Pix.Frac.Y (bu)", skPixCtrY_bu, skPosObjSep["Y"])
        nalign.Relative(skPixCtrY_bu, (0, 1), skPixFracY_bu, (0, 0), tNodeSpace)

        skPixRelFracY = nsh.math.Divide(ngMain, "Pix.Rel.Frac.Y", skPixFracY_bu, skPixSize_bu)
        nalign.Relative(skPixFracY_bu, (0, 1), skPixRelFracY, (0, 0), tNodeSpaceS)

        skPupilRelY_bu = nsh.math.Multiply(ngMain, "Pupil Rel.Y (bu)", skPixRelFracY, skPupilDia_bu)
        nalign.Relative(skPixRelFracY, (0, 1), skPupilRelY_bu, (0, 0), tNodeSpaceS)

        # ########################################################
        # Outgoing Coord. Z
        skPupilPosZ = nsh.math.Subtract(ngMain, "Pupil Pos. Z", skPosObjSep["Z"], skPupilDist_bu)
        nalign.Relative(skPupilDist_bu, (1, 0), skPupilPosZ, (0, 0), tNodeSpace)

        # ########################################################
        # Final Outgoing vector
        skVecOutRel = nsh.vector.CombineXYZ(ngMain, "Rel. Out. Vec.", skPupilRelX_bu, skPupilRelY_bu, skPupilPosZ)
        nalign.Relative(skPupilPosZ, (1, 0), skVecOutRel, (0, 0), tNodeSpace)

        skVecOut = nsh.vector.Subtract(ngMain, "Out. Vec.", skVecOutRel, skPosObj)
        nalign.Relative(skVecOutRel, (1, 0), skVecOut, (0, 0), tNodeSpaceS)

        skVecOutDir = nsh.vector.Normalize(ngMain, "Out. Vec. Dir.", skVecOut)
        nalign.Relative(skVecOut, (1, 0), skVecOutDir, (0, 0), tNodeSpaceS)

        # ########################################################
        # Incoming Vector
        skVecIn = nsh.vector.TransformWorldToObject(ngMain, "Vec. In.", skGeo["Incoming"])
        nalign.Relative(skVecOut, (0, 0), skVecIn, (0, 1), tNodeSpace)

        skVecInDir = nsh.vector.Normalize(ngMain, "Vec. In. Dir.", skVecIn)
        nalign.Relative(skVecIn, (1, 0), skVecInDir, (0, 0), tNodeSpaceS)

        # ########################################################
        # Output Shader
        nodRayToDir = nsh.utils.Group(ngMain, ngRayToDir)
        ngMain.links.new(skVecInDir, nodRayToDir.inputs["Incoming (local)"])
        ngMain.links.new(skVecOutDir, nodRayToDir.inputs["Outgoing (local)"])
        nalign.Relative(skVecInDir, (1, 0), nodRayToDir, (0, 0), tNodeSpace)

        ngMain.links.new(nodRayToDir.outputs["BSDF"], lMatOut["Surface"])
        nalign.Relative(nodRayToDir, (1, 0), lMatOut, (0, 0), tNodeSpace)

        # ngMain.links.new(nodObjPars.outputs[sRenderPupilDia_mm], nodHex.inputs[sPupilDia_mm])
        # ngMain.links.new(nodObjPars.outputs[sRenderPupilDistZ_mm], nodHex.inputs[sPupilDistZ_mm])

        # ngMain.links.new(nodSenPars.outputs[sPixCntX], nodHex.inputs[sPixCntX])
        # ngMain.links.new(nodSenPars.outputs[sPixCntY], nodHex.inputs[sPixCntY])
        # ngMain.links.new(nodSenPars.outputs[sPixSize], nodHex.inputs[sPixSize])

        # # Suppress zero pixel fraction rays
        # skEmitBlack = nsh.bsdf.Emission(ngMain, "Black", (0, 0, 0, 1), 1.0)
        # nalign.Relative(nodHex, (1, 1.2), skEmitBlack, (1, 0), tNodeSpace)

        # skAllowRay = nsh.bsdf.Mix(ngMain, "Allow Ray", nodHex.outputs['Is Center Ray'], nodHex.outputs['BSDF'], skEmitBlack)
        # nalign.Relative(nodHex, (1, 0), skAllowRay, (0, 0), tNodeSpace)

        # # Make Ray Splitter appear transparent for non-camera rays
        # skTransparent = nsh.bsdf.Transparent(ngMain, "Transparent", (1, 1, 1, 1))
        # nalign.Relative(skAllowRay, (1, 0), skTransparent, (1, 0.8), tNodeSpace)

        # lLightPath = nsh.utils.LightPath(ngMain)
        # nalign.Relative(skTransparent, (1, 0), lLightPath, (1, 1.2), tNodeSpace)

        # skCamRay = nsh.bsdf.Mix(ngMain, "Camera Ray", lLightPath['Is Camera Ray'], skTransparent, skAllowRay)
        # nalign.Relative(skAllowRay, (1, 0), skCamRay, (0, 0), tNodeSpace)

        # ngMain.links.new(skCamRay, lMatOut['Surface'])
        # nalign.Relative(skCamRay, (1, 0), lMatOut, (0, 0), tNodeSpace)

    # endif

    return matRS


# enddef
