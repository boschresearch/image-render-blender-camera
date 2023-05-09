#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /optics.py
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

################################################################
# Module to create optics meshes
import bpy
import bmesh
from bmesh.types import BMVert
from bmesh.types import BMFace

import math

##################################################################
## Get list of vertices based on condition on at least one face
## they are connected to.
##
def GetVertsOfFaces(xBMesh, fCond):
    for fc in xBMesh.faces:
        fc.select = fCond(fc)
    # endfor
    lVerts = [vx for vx in xBMesh.verts if vx.select == True]
    lFaces = [fc for fc in xBMesh.faces if fc.select == True]

    for vx in lVerts:
        vx.select_set(False)
    # endfor
    xBMesh.select_flush(False)
    return lFaces, lVerts


# undef
##################################################################

#################################################################
# Calc aspherical function
def DispAspherical(fR, fCurvAbs, fConic, lPoly, *, iVersion):

    fR2 = fR * fR

    fValue = 1.0 - (1.0 + fConic) * fCurvAbs * fCurvAbs * fR2
    if fValue < 0.0 and fValue > -1e-15:
        fValue = 0.0
    elif fValue <= -1e-15:
        raise RuntimeError(
            "Function DispAspherical(): Invalid aspherical surface parameters: "
            "curvature {}, conic {}, r2 {}".format(fCurvAbs, fConic, fR2)
        )
    # endif

    fZ = fCurvAbs * fR2 / (1 + math.sqrt(fValue))

    if iVersion == 1:
        # the first parameter in the aspherical polynomial is the r^4 component
        fRn = fR2
        for dPoly in lPoly:
            fRn *= fR2
            fZ += dPoly * fRn
        # endfor

    elif iVersion == 2:
        # the first parameter in the aspherical polynomial is the r^2 component
        fRn = fR2
        for dPoly in lPoly:
            fZ += dPoly * fRn
            fRn *= fR2
        # endfor
    else:
        raise Exception(
            "Function DispAspherical() not implemented for data version '{0}'".format(
                iVersion
            )
        )
    # endif

    return fZ


# enddef

#################################################################
# SetVertsToCircle
# Set vertices in a mesh to a circle, while distorting the mesh
# as little as possible.
def SetVertsToCircle(lfcGrid, fHalfDiaBU, fGridSizeBU, sType):

    lVex = []
    for face in lfcGrid:
        lIn = []
        lOut = []

        lRad = []
        bHasIn = False
        bHasOut = False

        for vx in face.verts:
            fR = math.sqrt(vx.co.x * vx.co.x + vx.co.y * vx.co.y)
            lRad.append(fR)
            if fR <= fHalfDiaBU:
                bHasIn = True
                lIn.append(vx)
            else:
                bHasOut = True
                lOut.append(vx)
            # endif
        # endfor

        # if face is completely inside or outside radius,
        # then don't change any vertex of it.
        if bHasIn == False or bHasOut == False:
            continue
        # endif

        if sType == "outside":
            lVex.extend(lOut)
        elif sType == "inside":
            lVex.extend(lIn)
        elif sType == "balanced":
            fMaxDistBU = fGridSizeBU / math.sqrt(2.0)
            iRadIdx = 0
            for vx in face.verts:
                fVal = abs(fHalfDiaBU - lRad[iRadIdx])
                if fVal <= fMaxDistBU:
                    lVex.append(vx)
                # endfor
                iRadIdx += 1
            # endfor
        # endif
    # endfor

    for vx in lVex:
        vx.select_set(True)
        # fR = math.sqrt(vx.co.x*vx.co.x + vx.co.y*vx.co.y)
        # fScale = fHalfDiaBU / fR
        # vx.co.x *= fScale
        # vx.co.y *= fScale
    # endfor

    for face in lfcGrid:
        iSelCnt = 0
        for vx in face.verts:
            if vx.select == True:
                iSelCnt += 1
            # endif
        # endfor

        if iSelCnt == len(face.verts):
            fMax = 0.0
            for vx in face.verts:
                fR = math.sqrt(vx.co.x * vx.co.x + vx.co.y * vx.co.y)
                fVal = abs(fHalfDiaBU - fR)
                if fVal > fMax:
                    vxMax = vx
                    fMax = fVal
                # endif
            # endfor
            vxMax.select_set(False)
        # endif
    # endfor

    for vx in lVex:
        if vx.select == True:
            fR = math.sqrt(vx.co.x * vx.co.x + vx.co.y * vx.co.y)
            fScale = fHalfDiaBU / fR
            vx.co.x *= fScale
            vx.co.y *= fScale
        # endif
    # endfor


# enddef

#################################################################
# Prepare Lens Grid
# Ensure that edge of refractive part of lens has smooth normals.
def PrepareLensGrid(lfcGrid, fHalfDiaBU, fEdgeBU, fGridSizeBU, iSurfMatId):

    fFullHalfDiaBU = fHalfDiaBU + fEdgeBU

    for face in lfcGrid:
        face.select_set(False)
    # endfor

    SetVertsToCircle(lfcGrid, fFullHalfDiaBU, fGridSizeBU, "balanced")
    SetVertsToCircle(lfcGrid, fHalfDiaBU, fGridSizeBU, "balanced")

    for face in lfcGrid:
        vxCtr = face.calc_center_median()
        fR = math.sqrt(vxCtr.x * vxCtr.x + vxCtr.y * vxCtr.y)
        if fR < fHalfDiaBU:
            face.material_index = iSurfMatId
            # face.select_set(True)
        else:
            face.material_index = 0
            # face.select_set(False)
        # endif
    # endfor


# enddef

#################################################################
# Apply aspherical function
def ApplyLensShapeAspherical(
    lfcGrid,
    lvxGrid,
    fGridSizeBU,
    fDia,
    fCurv,
    fConic,
    lPoly,
    fEdgeMM,
    fBUperMM,
    iSurfMatId,
    *,
    iVersion
):

    fEdgeBU = fEdgeMM * fBUperMM
    fHalfDia = fDia / 2.0
    fFullHalfDia = fHalfDia + fEdgeMM

    fHalfDiaBU = fHalfDia * fBUperMM
    fFullHalfDiaBU = fFullHalfDia * fBUperMM

    fCurvBU = fCurv / fBUperMM

    # If curvature is zero, create flat surface
    if abs(fCurvBU) < 1e-7:

        PrepareLensGrid(lfcGrid, fHalfDiaBU, fEdgeBU, fGridSizeBU, iSurfMatId)

        # for vx in lvxGrid:
        # fR = math.sqrt(vx.co.x*vx.co.x + vx.co.y*vx.co.y)
        # if fR < fHalfDiaBU:
        # vx.select_set(True)
        # # endif
        # # endfor

    else:

        fCurvAbs = abs(fCurv)
        fCurvAbsBU = fCurvAbs * fBUperMM

        fSign = 1.0
        if fCurv < 0.0:
            fSign = -1.0

        # Check for maximally allowed diameter
        # If the conic constant is <= -1, the maximally allowed
        # diameter is infinity.
        if fConic > -1:
            fFullHalfDiaMax = math.sqrt(1.0 / (1.0 + fConic)) / fCurvAbs
            fFullHalfDia = min(fFullHalfDia, fFullHalfDiaMax)
            fHalfDia = fFullHalfDia - fEdgeMM
        # endif

        PrepareLensGrid(
            lfcGrid, fHalfDia * fBUperMM, fEdgeMM * fBUperMM, fGridSizeBU, iSurfMatId
        )

        # Calc max z displacement
        fZmaxBU = (
            DispAspherical(fFullHalfDia, fCurvAbs, fConic, lPoly, iVersion=iVersion)
            * fBUperMM
        )

        for vx in lvxGrid:
            fR = math.sqrt(vx.co.x * vx.co.x + vx.co.y * vx.co.y) / fBUperMM
            if fR < fFullHalfDia:
                fZdeltaBU = (
                    DispAspherical(fR, fCurvAbs, fConic, lPoly, iVersion=iVersion)
                    * fBUperMM
                )
                # if fR < fHalfDia:
                # vx.select_set(True)
                # # endif
            else:
                fZdeltaBU = fZmaxBU
            # endif
            vx.co.z += fSign * fZdeltaBU
        # endfor
    # endif

    return fHalfDiaBU, fFullHalfDiaBU


# enddef

#################################################################
# Spherical displacement function
def DispSpherical(fR, fRadius):
    fZ = fRadius - math.sqrt(fRadius * fRadius - fR * fR)
    return fZ


#################################################################
# Apply spherical function
def ApplyLensShapeSpherical(
    lfcGrid,
    lvxGrid,
    fGridSizeBU,
    fDia,
    fCurv,
    fEdgeMM,
    fBUperMM,
    iSurfMatId,
    *,
    iVersion
):

    # Helper variables
    fEdgeBU = fEdgeMM * fBUperMM
    fHalfDiaBU = (fDia / 2.0) * fBUperMM
    fFullHalfDiaBU = fHalfDiaBU + fEdgeBU

    # If curvature is zero, create flat surface
    if abs(fCurv) < 1e-7:

        PrepareLensGrid(lfcGrid, fHalfDiaBU, fEdgeBU, fGridSizeBU, iSurfMatId)

        for vx in lvxGrid:
            fR = math.sqrt(vx.co.x * vx.co.x + vx.co.y * vx.co.y)
            if fR < fHalfDiaBU:
                vx.select_set(True)
            # endif
        # endfor

    else:

        fRadBU = fBUperMM / abs(fCurv)
        fRadBU2 = fRadBU * fRadBU

        fSign = 1.0
        if fCurv < 0.0:
            fSign = -1.0

        # Ensure that half diameter is not larger than curvature radius
        fFullHalfDiaBU = min(fFullHalfDiaBU, fRadBU)
        fFullHalfDiaBU2 = fFullHalfDiaBU * fFullHalfDiaBU

        fHalfDiaBU = fFullHalfDiaBU - fEdgeBU

        PrepareLensGrid(lfcGrid, fHalfDiaBU, fEdgeBU, fGridSizeBU, iSurfMatId)

        # Calc max z displacement
        fZmax = fRadBU - math.sqrt(fRadBU2 - fFullHalfDiaBU2)

        for vx in lvxGrid:
            fR = math.sqrt(vx.co.x * vx.co.x + vx.co.y * vx.co.y)
            if fR < fFullHalfDiaBU:
                fZdelta = fRadBU - math.sqrt(fRadBU2 - fR * fR)
                if fR < fHalfDiaBU:
                    vx.select_set(True)
                # endif
            else:
                fZdelta = fZmax
            # endif
            vx.co.z += fSign * fZdelta
        # endfor
    # endif

    return fHalfDiaBU, fFullHalfDiaBU


# enddef
#################################################################

##################################################################
# Create a lens with two surfaces


def CreateLensSurf2(_xBMesh, _dicLens, _dicPars):  # _fSize, _iGridCuts):

    bmesh.ops.create_cube(_xBMesh, size=1)

    fBUperMM = _dicPars["fBUperMM"]

    fSizeBU = _dicPars["fMaxSize"] * fBUperMM
    iGridCuts = _dicPars["iGridCuts"]
    fThickCtrBU = _dicLens["lThickCtr"][0] * fBUperMM

    face_top = [fc for fc in _xBMesh.faces if fc.normal.z > 0.9][0]
    face_bot = [fc for fc in _xBMesh.faces if fc.normal.z < -0.9][0]

    for vx in face_top.verts:
        vx.co.x *= fSizeBU
        vx.co.y *= fSizeBU
        vx.co.z = fThickCtrBU

    for vx in face_bot.verts:
        vx.co.x *= fSizeBU
        vx.co.y *= fSizeBU
        vx.co.z = 0.0

    bmesh.ops.subdivide_edges(
        _xBMesh, edges=face_top.edges, cuts=iGridCuts, use_grid_fill=True
    )
    bmesh.ops.subdivide_edges(
        _xBMesh, edges=face_bot.edges, cuts=iGridCuts, use_grid_fill=True
    )

    lvxSurf = [0, 0]
    lfcSurf = [0, 0]

    lfcSurf[0], lvxSurf[0] = GetVertsOfFaces(_xBMesh, lambda x: x.normal.z < -0.9)
    lfcSurf[1], lvxSurf[1] = GetVertsOfFaces(_xBMesh, lambda x: x.normal.z > 0.9)

    fGridSizeBU = fSizeBU / iGridCuts
    fEdgeBU = 2.0 * fGridSizeBU
    fEdgeMM = fEdgeBU / fBUperMM

    for iSurfIdx in range(2):

        for vx in lvxSurf[iSurfIdx]:
            vx.select_set(False)
        # endfor
        _xBMesh.select_flush(False)

        dRad = _dicLens["lfRad"][iSurfIdx]
        if abs(dRad) < 1e-10:
            dCurv = 0.0
        else:
            dCurv = 1.0 / dRad
        # endif

        sType = _dicLens["lsSubType"][iSurfIdx]
        if sType == "spherical":
            fHalfDiaBU, fFullHalfDiaBU = ApplyLensShapeSpherical(
                lfcSurf[iSurfIdx],
                lvxSurf[iSurfIdx],
                fGridSizeBU,
                _dicLens["lfDia"][iSurfIdx],
                dCurv,
                fEdgeMM,
                fBUperMM,
                1,
            )
        elif sType == "aspherical":
            fHalfDiaBU, fFullHalfDiaBU = ApplyLensShapeAspherical(
                lfcSurf[iSurfIdx],
                lvxSurf[iSurfIdx],
                fGridSizeBU,
                _dicLens["lfDia"][iSurfIdx],
                dCurv,
                _dicLens["lfConic"][iSurfIdx],
                _dicLens["lAsphPoly"][iSurfIdx],
                fEdgeMM,
                fBUperMM,
                1,
            )
        # endif

        for vx in _xBMesh.verts:
            vx.select_set(False)
        # endfor
        _xBMesh.select_flush(False)


# enddef

##################################################################
# Extrude faces, translate them and return extruded faces


def _ExtrudeFaces(_xBMesh, _lFaces, _vTrans):

    dicExtruded = bmesh.ops.extrude_face_region(_xBMesh, geom=_lFaces)

    lExtVerts = [v for v in dicExtruded["geom"] if isinstance(v, BMVert)]
    bmesh.ops.translate(_xBMesh, vec=_vTrans, verts=lExtVerts)

    lFaces = [fc for fc in dicExtruded["geom"] if isinstance(fc, BMFace)]
    return lFaces


# enddef

##################################################################
# Create a lens with two surfaces


def CreateLensSurfN(_xBMesh, _dicLens, _dicPars, *, iVersion):
    from mathutils import Vector

    fBUperMM = _dicPars["fBUperMM"]

    fSizeMM = _dicPars["fMaxSize"]
    fSizeBU = fSizeMM * fBUperMM
    iGridCuts = _dicPars["iGridCuts"]
    lThickCtrBU = [dVal * fBUperMM for dVal in _dicLens["lThickCtr"]]
    iSurfCnt = len(lThickCtrBU) + 1

    fGridSizeBU = fSizeBU / iGridCuts
    fEdgeBU = 2.0 * fGridSizeBU
    fEdgeMM = fEdgeBU / fBUperMM

    fHalfSizeBU = fSizeBU / 2.0

    # Create a mesh of a single plane
    lVerts = [
        (fHalfSizeBU, fHalfSizeBU, 0.0),
        (fHalfSizeBU, -fHalfSizeBU, 0.0),
        (-fHalfSizeBU, -fHalfSizeBU, 0.0),
        (-fHalfSizeBU, fHalfSizeBU, 0.0),
    ]  # 4 verts made with XYZ coords
    lEdgeIdx = []
    lFaceIdx = [[3, 2, 1, 0]]

    meshTemp = bpy.data.meshes.new("_temp")
    meshTemp.from_pydata(lVerts, lEdgeIdx, lFaceIdx)
    _xBMesh.from_mesh(meshTemp)
    bpy.data.meshes.remove(meshTemp)

    _xBMesh.faces.ensure_lookup_table()
    lFaces = [_xBMesh.faces[0]]
    lfcSrcPlane = [_xBMesh.faces[0]]

    # Extrude the plane once for each additional surface
    for iFaceIdx in range(iSurfCnt - 1):
        vTrans = Vector((0, 0, lThickCtrBU[iFaceIdx]))
        lFaces = _ExtrudeFaces(_xBMesh, lFaces, vTrans)
        lfcSrcPlane.append(lFaces[0])
    # endfor

    for iSurfIdx in range(iSurfCnt):

        fcSrcPlane = lfcSrcPlane[iSurfIdx]

        # Deselect all elements in bmesh
        for fc in _xBMesh.faces:
            fc.select_set(False)
        # endfor
        _xBMesh.select_flush(False)

        lfcSurf = [fcSrcPlane]
        dicRet = bmesh.ops.subdivide_edges(
            _xBMesh, edges=fcSrcPlane.edges, cuts=iGridCuts, use_grid_fill=True
        )

        # get all new faces due to subdivision
        lfcRet = [fc for fc in dicRet["geom_inner"] if isinstance(fc, BMFace)]

        # extend the list of all faces in surfaces
        lfcSurf.extend(lfcRet)
        # select all faces, so that all their vertices are also selected
        for fc in lfcSurf:
            fc.select_set(True)
        # endfor

        # Get the list of all vertices on surface by taking all selected vertices
        lvxSurf = [vx for vx in _xBMesh.verts if isinstance(vx, BMVert) and vx.select]

        # Deselect all elements in bmesh
        for fc in _xBMesh.faces:
            fc.select_set(False)
        # endfor
        _xBMesh.select_flush(False)

        # The material index to use for the optically active surface area
        if iSurfCnt == 2:
            iSurfMatId = 1
        else:
            iSurfMatId = iSurfIdx + 1
        # endif

        dRad = _dicLens["lfRad"][iSurfIdx]
        if abs(dRad) < 1e-10:
            dCurv = 0.0
        else:
            dCurv = 1.0 / dRad
        # endif

        sType = _dicLens["lsSubType"][iSurfIdx]
        if sType == "spherical":
            fHalfDiaBU, fFullHalfDiaBU = ApplyLensShapeSpherical(
                lfcSurf,
                lvxSurf,
                fGridSizeBU,
                _dicLens["lfDia"][iSurfIdx],
                dCurv,
                fEdgeMM,
                fBUperMM,
                iSurfMatId,
                iVersion=iVersion,
            )
        elif sType == "aspherical":
            fHalfDiaBU, fFullHalfDiaBU = ApplyLensShapeAspherical(
                lfcSurf,
                lvxSurf,
                fGridSizeBU,
                _dicLens["lfDia"][iSurfIdx],
                dCurv,
                _dicLens["lfConic"][iSurfIdx],
                _dicLens["lAsphPoly"][iSurfIdx],
                fEdgeMM,
                fBUperMM,
                iSurfMatId,
                iVersion=iVersion,
            )
        # endif
    # endfor

    # Deselect all elements in bmesh
    for fc in _xBMesh.faces:
        fc.select_set(False)
    # endfor
    _xBMesh.select_flush(False)


# enddef

##################################################################
# Create different lens types
def CreateLens(_xBMesh, _dicLens, _dicPars, *, iVersion):

    CreateLensSurfN(_xBMesh, _dicLens, _dicPars, iVersion=iVersion)

    # iSurfCnt = len(_dicLens['lfDia'])

    # if iSurfCnt == 2:
    #     CreateLensSurf2(_xBMesh, _dicLens, _dicPars)
    # elif iSurfCnt >= 3:
    #     CreateLensSurfN(_xBMesh, _dicLens, _dicPars)
    # # endif


# enddef
