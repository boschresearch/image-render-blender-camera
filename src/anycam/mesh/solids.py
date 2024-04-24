#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /solids.py
# Created Date: Thursday, October 22nd 2020, 2:51:18 pm
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
import bmesh
import math
import mathutils
import numpy as np

#####################################################################################
# Create a pyramid mesh with origin at the tip
def CreatePyramid(_sName, _fSizeX, _fSizeY, _fSizeZ, fOffX=0.0, fOffY=0.0):

    meshF = bpy.data.meshes.new(_sName + "_mesh")  # add a new mesh
    objF = bpy.data.objects.new(_sName, meshF)  # add a new object using the mesh

    # Ensure lens object is initially at origin, so that mesh vertices
    # can be places relative to origin.
    objF.location = (0, 0, 0)

    fXh = _fSizeX / 2.0
    fYh = _fSizeY / 2.0
    fZ = _fSizeZ

    lVex = [
        (0.0, 0.0, 0.0),
        (-fXh + fOffX, fYh + fOffY, fZ),
        (-fXh + fOffX, -fYh + fOffY, fZ),
        (fXh + fOffX, -fYh + fOffY, fZ),
        (fXh + fOffX, fYh + fOffY, fZ),
    ]

    lFaces = [[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1], [1, 2, 3, 4]]

    meshF.from_pydata(lVex, [], lFaces)
    meshF.update(calc_edges=True)
    if hasattr(meshF, "use_auto_smooth"):
        meshF.use_auto_smooth = True
    # endif

    bm = bmesh.new()
    bm.from_mesh(meshF)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(meshF)
    meshF.update()
    bm.free()

    for xPoly in meshF.polygons:
        xPoly.use_smooth = True
    # endfor

    matCol = bpy.data.materials.new(name=_sName)
    matCol.use_nodes = True
    objF.active_material = matCol

    return objF


# enddef

#####################################################################################
def CreateFrustumPanoEquidist(*, sName, fSenSizeX_mm, fSenSizeY_mm, fFov_deg, iResolution, fRayLen):

    iStepCntX = iStepCntY = 0
    fAspect = fSenSizeY_mm / fSenSizeX_mm

    if fSenSizeX_mm >= fSenSizeY_mm:
        iStepCntX = iResolution
        iStepCntY = int(math.ceil(iStepCntX * fAspect))
    else:
        iStepCntY = iResolution
        iStepCntX = int(math.ceil(iStepCntY / fAspect))
    # endif

    fSenSizeMax_mm = max(fSenSizeX_mm, fSenSizeY_mm)

    fRadMax_mm = fSenSizeMax_mm / 2.0
    fAngleMax_deg = fFov_deg / 2.0
    fAnglePerRadius_deg_mm = fAngleMax_deg / fRadMax_mm

    aX = np.linspace(-fRadMax_mm, fRadMax_mm, num=iStepCntX + 1)
    aY = np.linspace(-fRadMax_mm * fAspect, fRadMax_mm * fAspect, num=iStepCntY + 1)

    vZ = mathutils.Vector((0.0, 0.0, -1.0))
    lVex = [(0.0, 0.0, 0.0)]

    # Loop over all points in grid
    for dY in aY:
        for dX in aX:
            vImgPnt = mathutils.Vector((dX, dY, 0.0))

            # test whether radius of point (dX, dY) relates to greater than max angle
            dR = vImgPnt.length

            dAngle_deg = fAnglePerRadius_deg_mm * dR
            if dAngle_deg > fAngleMax_deg:
                vImgPntN = vImgPnt / dR
                vImgPnt = vImgPntN * fRadMax_mm
                dAngle_deg = fAngleMax_deg
            elif dAngle_deg < 1e-4:
                vImgPnt = mathutils.Vector((0.0, 0.0, 0.0))
                vImgPntN = None
                dAngle_deg = 0.0
            else:
                vImgPntN = vImgPnt / dR
            # endif

            dAngle_rad = math.radians(dAngle_deg)

            if vImgPntN is not None:
                vRayN = math.cos(dAngle_rad) * vZ + math.sin(dAngle_rad) * vImgPntN
            else:
                vRayN = vZ
            # endif

            vRay = fRayLen * vRayN
            lVex.append(vRay[:])
        # endfor
    # endfor

    lFaces = []
    iElCntX = iStepCntX + 1
    iElCntY = iStepCntY + 1

    # Create faces for projection surface
    for iY in range(iElCntY - 1):
        for iX in range(iElCntX - 1):
            iIdx = iY * iElCntX + iX + 1
            lFaces.append([iIdx, iIdx + 1, iIdx + iElCntX + 1, iIdx + iElCntX])
        # endfor
    # endfor

    # Create faces for connection to origin
    for iY in [0, iElCntY - 1]:
        for iX in range(iElCntX - 1):
            iIdx = iY * iElCntX + iX + 1
            lFaces.append([0, iIdx + 1, iIdx])
        # endfor
    # endfor

    for iX in [0, iElCntX - 1]:
        for iY in range(iElCntY - 1):
            iIdx = iY * iElCntX + iX + 1
            lFaces.append([0, iIdx, iIdx + iElCntX])
        # endfor
    # endfor

    ########################################################################
    meshF = bpy.data.meshes.new(sName + "_mesh")  # add a new mesh
    objF = bpy.data.objects.new(sName, meshF)  # add a new object using the mesh
    # Ensure lens object is initially at origin, so that mesh vertices
    # can be places relative to origin.
    objF.location = (0, 0, 0)

    meshF.from_pydata(lVex, [], lFaces)
    meshF.update(calc_edges=True)
    if hasattr(meshF, "use_auto_smooth"):
        meshF.use_auto_smooth = True
    # endif

    bm = bmesh.new()
    bm.from_mesh(meshF)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(meshF)
    meshF.update()
    bm.free()

    for xPoly in meshF.polygons:
        xPoly.use_smooth = True
    # endfor

    return objF


# enddef

#####################################################################################
def CreateFrustumPanoFovRange(*, sName, lFovRange_deg, fFovMax_deg, iResolution, fRayLen):

    lFov_deg = [
        lFovRange_deg[0][1] - lFovRange_deg[0][0],
        lFovRange_deg[1][1] - lFovRange_deg[1][0],
    ]

    iStepCntX = iStepCntY = 0
    fAspect = lFov_deg[1] / lFov_deg[0]

    if lFov_deg[0] >= lFov_deg[1]:
        iStepCntX = iResolution
        iStepCntY = int(math.ceil(iStepCntX * fAspect))
    else:
        iStepCntY = iResolution
        iStepCntX = int(math.ceil(iStepCntY / fAspect))
    # endif

    fAngleMax_deg = fFovMax_deg / 2.0

    aX = np.linspace(lFovRange_deg[0][0], lFovRange_deg[0][1], num=iStepCntX + 1)
    aY = np.linspace(lFovRange_deg[1][0], lFovRange_deg[1][1], num=iStepCntY + 1)

    vZ = mathutils.Vector((0.0, 0.0, -1.0))
    lVex = [(0.0, 0.0, 0.0)]

    # Loop over all points in grid
    for dY in aY:
        for dX in aX:
            vImgDir = mathutils.Vector((dX, dY, 0.0))

            # test whether radius of point (dX, dY) relates to greater than max angle
            dAngle_deg = vImgDir.length

            if dAngle_deg > fAngleMax_deg:
                vImgDirN = vImgDir / dAngle_deg
                dAngle_deg = fAngleMax_deg
            elif dAngle_deg < 1e-4:
                vImgDir = mathutils.Vector((0.0, 0.0, 0.0))
                vImgDirN = None
                dAngle_deg = 0.0
            else:
                vImgDirN = vImgDir / dAngle_deg
            # endif

            dAngle_rad = math.radians(dAngle_deg)

            if vImgDirN is not None:
                vRayN = math.cos(dAngle_rad) * vZ + math.sin(dAngle_rad) * vImgDirN
            else:
                vRayN = vZ
            # endif

            vRay = fRayLen * vRayN
            lVex.append(vRay[:])
        # endfor
    # endfor

    lFaces = []
    iElCntX = iStepCntX + 1
    iElCntY = iStepCntY + 1

    # Create faces for projection surface
    for iY in range(iElCntY - 1):
        for iX in range(iElCntX - 1):
            iIdx = iY * iElCntX + iX + 1
            lFaces.append([iIdx, iIdx + 1, iIdx + iElCntX + 1, iIdx + iElCntX])
        # endfor
    # endfor

    # Create faces for connection to origin
    for iY in [0, iElCntY - 1]:
        for iX in range(iElCntX - 1):
            iIdx = iY * iElCntX + iX + 1
            lFaces.append([0, iIdx + 1, iIdx])
        # endfor
    # endfor

    for iX in [0, iElCntX - 1]:
        for iY in range(iElCntY - 1):
            iIdx = iY * iElCntX + iX + 1
            lFaces.append([0, iIdx, iIdx + iElCntX])
        # endfor
    # endfor

    ########################################################################
    meshF = bpy.data.meshes.new(sName + "_mesh")  # add a new mesh
    objF = bpy.data.objects.new(sName, meshF)  # add a new object using the mesh
    # Ensure lens object is initially at origin, so that mesh vertices
    # can be places relative to origin.
    objF.location = (0, 0, 0)

    meshF.from_pydata(lVex, [], lFaces)
    meshF.update(calc_edges=True)
    if hasattr(meshF, "use_auto_smooth"):
        meshF.use_auto_smooth = True
    # endif

    bm = bmesh.new()
    bm.from_mesh(meshF)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(meshF)
    meshF.update()
    bm.free()

    for xPoly in meshF.polygons:
        xPoly.use_smooth = True
    # endfor

    matCol = bpy.data.materials.new(name=sName)
    matCol.use_nodes = True
    objF.active_material = matCol

    return objF


# enddef
