#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /camera_lft.py
# Created Date: Thursday, October 22nd 2020, 2:51:35 pm
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
import pyjson5 as json

from .. import ops
from .. import node
from .. import material

from anybase import config
import anyblend
from anybase.cls_anyexcept import CAnyExcept


#####################################################################
# Create the camera name
def CreateName(_sName):
    return "Cam.Poly.{0}".format(_sName)


# enddef

#####################################################################
# Create Light Field Trace Cameras


def Create(
    _sName,
    _dicCamera,
    bOverwrite=False,
    bForce=False,
    fScale=1.0,
    bCreateFrustum=False,
    dicAnyCamEx=None,
):

    # #### DEBUG ########
    # bOverwrite = True
    # bForce = True
    # ###################

    # Calculate Blender Units per Millimeter
    fBUperMM = fScale * 1e-3 / bpy.context.scene.unit_settings.scale_length

    #####################################################
    # Get camera data
    dicSensor = _dicCamera.get("dicSensor")
    # sSensorName = dicSensor.get("sName").replace(" ", "_")

    dicPoly = _dicCamera.get("dicPoly")

    dicType = config.CheckConfigType(dicPoly, "/anycam/db/project/poly/*:1.*")
    if not dicType.get("bOK"):
        raise CAnyExcept("Invalid polynomial type '{0}': {1}".format(dicType.get("sCfgDti"), dicType.get("sMsg")))
    # endif

    lPolyType = dicType.get("lCfgType")
    sPolyType = lPolyType[4]
    if sPolyType != "radial":
        raise CAnyExcept("Polynomial camera type '{0}' not supported".format(sPolyType))
    # endif

    lCenter_mm = dicPoly.get("lCenter_mm", [0.0, 0.0])
    fMaxAngle_deg = dicPoly.get("fMaxAngle_deg", 180.0)
    fMaxAngle_deg = min(max(1.0, fMaxAngle_deg), 180.0)

    lVignetting = dicPoly.get("lVignetting")

    #####################################################
    # Create camera empty, that acts as origin for whole camera system
    sCamName = CreateName(_sName)

    cnMain = bpy.data.collections.get("AnyCam")
    if cnMain is None:
        cnMain = bpy.data.collections.new("AnyCam")
        bpy.context.scene.collection.children.link(cnMain)
    # endif

    objCamOrig = bpy.data.objects.get(sCamName)
    if objCamOrig is not None:
        if bOverwrite is True:
            ops.DeleteObjectHierarchy(objCamOrig)
            objCamOrig = None
        else:
            return {
                "bResult": False,
                "objCam": objCamOrig,
                "sMsg": "Camera with selected name already exists.",
            }
        # endif
    # endif

    #####################################################
    # Create Parameter node groups
    node.grp.render_pars.Create(bForce=bForce, fScale=fScale)
    node.grp.sensor_pars.Create(dicSensor, bForce=bForce)

    #####################################################

    objCamOrig = bpy.data.objects.new(sCamName, None)
    objCamOrig.location = (0, 0, 0)
    objCamOrig.empty_display_size = 1
    objCamOrig.empty_display_type = "PLAIN_AXES"
    cnMain.objects.link(objCamOrig)

    # bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1, location=(0, 0, 0))
    # objCamOrig = bpy.context.view_layer.objects.active
    # objCamOrig.name = sCamName

    #####################################################
    # Create render pinhole camera
    sSenName = sCamName + ".Sen"

    camX = bpy.data.cameras.get(sSenName)
    if camX is not None:
        bpy.data.cameras.remove(camX)
        camX = None
    # endif

    camX = bpy.data.cameras.new(sSenName)
    objCam = bpy.data.objects.new(name=sSenName, object_data=camX)

    # cnMain = bpy.context.scene.collection
    vlMain = bpy.context.view_layer
    cnMain.objects.link(objCam)
    vlMain.objects.active = objCam
    objCam.select_set(True)

    # Specify camera parameters
    fPixSize_um = dicSensor.get("fPixSize")
    iPixCntX = dicSensor.get("iPixCntX")
    iPixCntY = dicSensor.get("iPixCntY")

    fPixSize_mm = 1e-3 * fPixSize_um
    fSenSizeX_mm = fPixSize_mm * iPixCntX
    fSenSizeY_mm = fPixSize_mm * iPixCntY
    fSenSizeMax_mm = max(fSenSizeX_mm, fSenSizeY_mm)
    fFocLen_mm = fSenSizeMax_mm

    camX.type = "PERSP"
    camX.lens = fFocLen_mm
    camX.lens_unit = "MILLIMETERS"
    # camX.ortho_scale = fBUperMM * fSenSizeMax_mm
    camX.sensor_width = fSenSizeX_mm
    camX.sensor_height = fSenSizeY_mm

    if fSenSizeX_mm >= fSenSizeY_mm:
        camX.sensor_fit = "HORIZONTAL"
    else:
        camX.sensor_fit = "VERTICAL"
    # endif

    camX.shift_x = -lCenter_mm[0] / fSenSizeMax_mm
    camX.shift_y = -lCenter_mm[1] / fSenSizeMax_mm

    camX.clip_start = fBUperMM * 0.5 * fFocLen_mm
    camX.clip_end = fBUperMM * 1e7
    camX.display_size = max(0.5, fBUperMM * fFocLen_mm)

    # Sensor position relative to camera origin, which is
    # on last glass surface towards environment.
    objCam.location = (
        lCenter_mm[0] * fBUperMM,
        lCenter_mm[1] * fBUperMM,
        fFocLen_mm * fBUperMM,
    )
    objCam.rotation_euler = (0, 0, 0)

    #####################################################
    # Create plane with refractor that acts as sensor plane
    sRefractorName = sSenName + ".RF"
    meshRF = bpy.data.meshes.get(sRefractorName)
    if meshRF is not None:
        bpy.data.meshes.remove(meshRF)
    # endif

    meshRF = bpy.data.meshes.new(sRefractorName)
    objRF = bpy.data.objects.new(name=sRefractorName, object_data=meshRF)
    cnMain.objects.link(objRF)

    # objRF.location = (-lCenter_mm[0], -lCenter_mm[1], 0)
    objRF.location = (0, 0, 0)

    lCoef = dicPoly.get("lCoef")
    if not lCoef:
        raise CAnyExcept("No polynomial coefficients given")
    # endif

    sPolyTypeIn = dicPoly.get("sInputType")
    lPolyTypeIn = sPolyTypeIn.split("/")
    if not sPolyTypeIn.startswith("radius/normalized/") or len(lPolyTypeIn) < 4:
        raise CAnyExcept("Unsupported polynomial input type: {0}".format(sPolyTypeIn))
    # endif

    if lPolyTypeIn[2] == "sensor-half-width":
        if lPolyTypeIn[3] != "mm":
            raise CAnyExcept("Unsupported unit in polynomial input type: {0}".format(sPolyTypeIn))
        # endif
        fNormRadius_mm = 0.5 * fSenSizeMax_mm
    elif lPolyTypeIn[2] == "fixed":
        fNormRadius_mm = dicPoly.get("fNormLength_mm")
        if fNormRadius_mm is None:
            raise CAnyExcept(
                "Polynomial normalization length not given in parameter 'fNormLength_mm': {0}".format(sPolyTypeIn)
            )
        # endif
    else:
        raise CAnyExcept("Unsupported polynomial input type: {0}".format(sPolyTypeIn))
    # endif

    if dicPoly.get("sOutputType") != "angle/rad":
        raise CAnyExcept("Unsupported polynomial output type: {0}".format(dicPoly.get("sOutputType")))
    # endif

    # Get Refractor Material
    matRF = material.ray_poly_radial.Create(
        sId=sCamName,
        fNormRadius_mm=fNormRadius_mm,
        lCoef=lCoef,
        lCenter_mm=lCenter_mm,
        fMaxAngle_deg=fMaxAngle_deg,
        lVignetting=lVignetting,
        bForce=bForce,
    )

    objRF.data.materials.append(matRF)

    xBMesh = bmesh.new()

    # Create Plane with Ray Splitter material
    fW2 = (math.ceil(fSenSizeX_mm * 10.0) / 20.0 + 0.1) * fBUperMM
    fH2 = (math.ceil(fSenSizeY_mm * 10.0) / 20.0 + 0.1) * fBUperMM
    fZ = 0.0

    # tNorm = (0, 0, 1)
    v1 = xBMesh.verts.new((-fW2, -fH2, fZ))
    v2 = xBMesh.verts.new((fW2, -fH2, fZ))
    v3 = xBMesh.verts.new((fW2, fH2, fZ))
    v4 = xBMesh.verts.new((-fW2, fH2, fZ))
    xBMesh.faces.new((v1, v2, v3, v4))

    xBMesh.to_mesh(meshRF)
    xBMesh.free()

    #############################################################
    # Store AnyCam Data
    if dicAnyCamEx is None:
        dicAnyCamEx = {}
    # endif

    objCam["AnyCam"] = json.dumps(
        {
            "sDTI": "/anycam/camera/poly/radial:1.1",
            "iSenResX": iPixCntX,
            "iSenResY": iPixCntY,
            "sOrigin": objCamOrig.name,
            "mEx": dicAnyCamEx,
        }
    )

    #############################################################
    # Place objects in hierarchical order
    anyblend.viewlayer.Update()
    anyblend.object.ParentObject(objCam, objRF)
    anyblend.object.ParentObject(objCamOrig, objCam)

    return {"bResult": True, "objCam": objCamOrig, "objAnyCam": objCam}


# enddef
