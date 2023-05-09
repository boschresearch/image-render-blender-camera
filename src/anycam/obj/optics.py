#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /optics.py
# Created Date: Thursday, October 22nd 2020, 2:51:37 pm
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

#################################################################
# Optics object module
import bpy
import bmesh
import math

from . import util
from .. import material
from .. import mesh
from anybase import config
import anyblend
from anybase.cls_anyexcept import CAnyExcept

#################################################################
# Create a lens object
# _sName: Name of the lens object
# _fZ: Position of center of bottom lens surface on z-axis
# _dicLens: A lens dictionary containing the lens data
# _fSize: The size along X and Y of the lens
# _iGridCuts: The number of grid cuts of the top and bottom surfaces


def CreateLens(_cnMain, _sName, _dicLens, _dicPars, iVersion=1):

    sLensName = _sName + ".Lens." + _dicLens["sName"].replace(" ", "_")
    meshLens = bpy.data.meshes.new(sLensName + "_mesh")  # add a new mesh
    objLens = bpy.data.objects.new(sLensName, meshLens)  # add a new object using the mesh

    vlMain = bpy.context.view_layer
    _cnMain.objects.link(objLens)  # put the object into the scene (link)
    vlMain.objects.active = objLens  # set as the active object in the scene
    objLens.select_set(True)  # select object

    # Ensure lens object is initially at origin, so that mesh vertices
    # can be places relative to origin.
    objLens.location = (0, 0, 0)

    # Remove all materials that may exist in object
    for matX in objLens.data.materials:
        objLens.data.materials.remove(matX)

    # Get lens aperture material and put it into material slot 0
    matAperture = material.optics.GetAperture()
    objLens.data.materials.append(matAperture)

    # Create list of all media
    iMediaCnt = len(_dicLens["lMedium"])
    lMedia = [_dicPars["sMediumEnv"]]
    lMedia.extend(_dicLens["lMedium"])

    for iMatIdx in range(iMediaCnt):
        # Get lens refraction material and place it in slot iMatIdx+1
        matRef = material.optics.GetRefractMedium(lMedia[iMatIdx], lMedia[iMatIdx + 1])
        objLens.data.materials.append(matRef)
    # endfor

    # if there is more than 1 material, the last surface has its own material with the normal reversed
    if iMediaCnt > 1:
        matRef = material.optics.GetRefractMedium(lMedia[0], lMedia[-1])
        objLens.data.materials.append(matRef)
    # endif

    # Get mm scale
    fBUperMM = _dicPars["fBUperMM"]

    # Create a new BMesh
    xBMesh = bmesh.new()

    # Create the lens mesh
    mesh.optics.CreateLens(xBMesh, _dicLens, _dicPars, iVersion=iVersion)

    # Switch on smooth shading
    for face in xBMesh.faces:
        face.smooth = True
    # endfor

    # make the bmesh the object's mesh
    xBMesh.to_mesh(meshLens)
    xBMesh.free()  # always do this when finisheds

    # Put lens at given location along z-axis
    objLens.location = (0, 0, _dicLens["fPosBotZ"] * fBUperMM)
    objLens.data.update()

    return objLens


# enddef

#################################################################
# Create an aperture object
# _dicLens: A lens dictionary containing the lens data
# _dicPars: General parameters


def CreateAperture(_cnMain, _sName, _dicApert, _dicPars):

    sApertName = _sName + ".Aper." + _dicApert["sName"].replace(" ", "_")
    meshApert = bpy.data.meshes.new(sApertName + "_mesh")  # add a new mesh
    objApert = bpy.data.objects.new(sApertName, meshApert)  # add a new object using the mesh

    vlMain = bpy.context.view_layer
    _cnMain.objects.link(objApert)  # put the object into the scene (link)
    vlMain.objects.active = objApert  # set as the active object in the scene
    objApert.select_set(True)  # select object

    # Ensure lens object is initially at origin, so that mesh vertices
    # can be places relative to origin.
    objApert.location = (0, 0, 0)

    # Remove all materials that may exist in object
    for matX in objApert.data.materials:
        objApert.data.materials.remove(matX)

    # Get lens aperture material and put it into material slot 0
    matAperture = material.optics.GetAperture()
    objApert.data.materials.append(matAperture)

    # Create a new BMesh
    xBMesh = bmesh.new()

    # Get mm scale
    fBUperMM = _dicPars["fBUperMM"]

    # Create a circle
    fDiaBU = _dicApert["lfDia"][0] * fBUperMM
    try:
        bmesh.ops.create_circle(
            xBMesh,
            cap_ends=False,
            segments=_dicPars["iGridCuts"],
            diameter=fDiaBU / 2.0,
        )
    except Exception:
        bmesh.ops.create_circle(xBMesh, cap_ends=False, segments=_dicPars["iGridCuts"], radius=fDiaBU / 2.0)
    # endtry

    # Get inner edges
    lInnerEdges = xBMesh.edges

    # Extrude circle
    dicRes = bmesh.ops.extrude_edge_only(xBMesh, edges=xBMesh.edges[:])
    lOuterCircle = dicRes["geom"]
    del dicRes

    # Get only the vertices of extruded circle
    lOuterVerts = [vx for vx in lOuterCircle if isinstance(vx, bmesh.types.BMVert)]
    lOuterEdges = [vx for vx in lOuterCircle if isinstance(vx, bmesh.types.BMEdge)]

    fMaxSizeBU = _dicPars["fMaxSize"] * fBUperMM / 2.0

    # Scale extruded vertices to surrounding square
    for vx in lOuterVerts:
        if abs(vx.co.x) >= abs(vx.co.y):
            fScale = fMaxSizeBU / abs(vx.co.x)
        else:
            fScale = fMaxSizeBU / abs(vx.co.y)
        # endif

        vx.co.x *= fScale
        vx.co.y *= fScale

    # endfor

    # Extrude all faces to create volume
    dicRes = bmesh.ops.extrude_face_region(xBMesh, geom=xBMesh.faces[:])
    lTopVerts = [vx for vx in dicRes["geom"] if isinstance(vx, bmesh.types.BMVert)]
    del dicRes

    # Translate extruded vertices to top plane position
    fThickCtrBU = _dicApert["fThickCtr"] * fBUperMM
    bmesh.ops.translate(xBMesh, vec=(0, 0, fThickCtrBU), verts=lTopVerts)

    # Switch on smooth shading
    # for face in xBMesh.faces:
    #     face.smooth = True
    # endfor

    # make the bmesh the object's mesh
    xBMesh.to_mesh(meshApert)
    xBMesh.free()  # always do this when finisheds

    # Put lens at given location along z-axis
    objApert.location = (0, 0, _dicApert["fPosBotZ"] * fBUperMM)
    objApert.data.update()

    return objApert


# enddef

#################################################################
# Create an optical element
# _dicOptic: Specification of optical element
# _dicPars: General Parameter
def CreateElement(_cnMain, _sName, _dicOptic, _dicPars):

    objRet = None
    dicType = config.CheckConfigType(_dicOptic, "/anycam/db/opticalsystem/*:*")
    if not dicType.get("bOK"):
        raise CAnyExcept(
            "Unsupported lens system object of type '{0}': {1}".format(dicType.get("sCfgDti"), dicType.get("sMsg"))
        )
    # endif
    sOpticType = dicType.get("lCfgType")[3]
    lVer = dicType.get("lCfgVer")

    if lVer[0] == 1:
        if sOpticType == "lens":
            objRet = CreateLens(_cnMain, _sName, _dicOptic, _dicPars, iVersion=1)
        elif sOpticType == "aperture":
            objRet = CreateAperture(_cnMain, _sName, _dicOptic, _dicPars)
        else:
            raise Exception(
                "Optic system element type '{0}' not supported for version '{1}.x'".format(sOpticType, lVer[0])
            )
        # endif
    elif lVer[0] == 2:
        if sOpticType == "lens":
            objRet = CreateLens(_cnMain, _sName, _dicOptic, _dicPars, iVersion=2)
        else:
            raise Exception(
                "Optic system element type '{0}' not supported for version '{1}.x'".format(sOpticType, lVer[0])
            )
        # endif
    else:
        raise Exception("Optic system element type '{0}' not supported for version '{1}.x'".format(sOpticType, lVer[0]))
    # endif

    return objRet


# enddef

##################################################################
# Generate optical system
#


def CreateLensSystem(
    _cnMain,
    _sName,
    _dicLensSys,
    iGridCuts=100,
    fScale=1.0,
    sMediumEnv="Air",
    bUseLsTypeInName=True,
):
    """
    Create a lens system given the _dicLensSys dictionary.

    Parameters:
        _cnMain: The collection the lens system elements should be added to.
        _dicLensSys: A lens system dictionary

    Keyword arguments:
        GridCuts (int), default = 100:
            Number of grid cuts for the lens meshes.

        Scale (float), default = 1.0:
            It is assumed that all values in the lens system dictionary are given in millimeters.
            The unit settings in the current scene are used to calculate the correct scale factor
            from millimeters to blender units. The scale given here is multiplied with this internal scale.

        MediumEnv (string), default = 'Air':
            The name of the environment medium as given in the medium dictionary. For example, for
            lenses in air this would be 'Air'.

        UseLsTypeInName (string), default = True:
            Flag whether to use the type name of lens system in the object name.
    """
    ##########################################
    # Initialize parameter dictionary

    # Calculate Blender Units per Millimeter
    fBUperMM = fScale * 1e-3 / bpy.context.scene.unit_settings.scale_length

    # Create the parameter dictionary
    _dicPars = {}
    _dicPars["iGridCuts"] = iGridCuts
    _dicPars["fBUperMM"] = fBUperMM
    _dicPars["sMediumEnv"] = sMediumEnv

    # print(_dicPars)
    ##########################################

    bpy.ops.object.select_all(action="DESELECT")

    lOpticList = _dicLensSys["lOpticList"]
    fMaxSize = _dicLensSys["fMaxSize"]

    # If fMaxSize == 0, then calculate size from lens system
    if fMaxSize < 1e-7:
        lOpticDia = []
        for dicOptic in lOpticList:
            lOpticDia.append(max(dicOptic["lfDia"]))

        fBorder = 0.5
        fMaxSize = max(lOpticDia)
        fMaxSize += 2.0 * fBorder
    # endif

    # Store max size in parameter dictionary
    _dicPars["fMaxSize"] = fMaxSize

    if bUseLsTypeInName:
        sName = "{0}.LS.{1}".format(_sName, _dicLensSys["sName"].replace(" ", "_"))
    else:
        sName = "{0}.LS".format(_sName)
    # endif

    lobjLensSys = []
    iSurfCnt = 0

    for dicOptic in lOpticList:
        dicR = config.CheckConfigType(dicOptic, "/anycam/db/opticalsystem/lens:*")
        if dicR.get("bOK") == True:
            iSurfCnt += dicOptic.get("iSurfCnt")
        # endif
        lobjLensSys.append(CreateElement(_cnMain, sName, dicOptic, _dicPars))
    #        break ## !! DEBUG
    # endfor

    # Get mm scale in BU
    fBUperMM = _dicPars["fBUperMM"]

    # Move all objects so that they are relative to the sensor CS
    fSenPosZ_bu = _dicLensSys["fSenPosZ"] * fBUperMM

    for objLS in lobjLensSys:
        objLS.location.z -= fSenPosZ_bu
    # endfor

    # if lens system is defined from sensor to environment, need to rotate by 180Ã‚Â°
    if fSenPosZ_bu < _dicLensSys["fEnvPosZ"] * fBUperMM:
        for objLS in lobjLensSys:
            objLS.rotation_euler = (math.radians(180), 0, 0)
            objLS.location.z *= -1.0
        # endfor
    # endif

    # print(bpy.context.scene.scale_length)
    objLensOrig = bpy.data.objects.new(sName, None)
    objLensOrig.location = (0, 0, 0)
    objLensOrig.empty_display_size = 1
    objLensOrig.empty_display_type = "PLAIN_AXES"
    _cnMain.objects.link(objLensOrig)

    # Store total number of refractive surfaces.
    # Adds 1 to total number of lens surfaces, since the virtual image plane
    # also uses a refraction shader.
    objLensOrig["iRefractSurfCnt"] = iSurfCnt + 1

    # bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1, location=(0, 0, 0))
    # objLensOrig = bpy.context.view_layer.objects.active
    # objLensOrig.name = sName

    anyblend.viewlayer.Update()
    anyblend.object.ParentObjectList(objLensOrig, lobjLensSys)

    # bpy.context.view_layer.objects.active = objLensOrig
    # for objLS in lobjLensSys:
    #     objLS.select_set(True)
    # # endfor
    # bpy.ops.object.parent_set()

    return objLensOrig


# enddef
