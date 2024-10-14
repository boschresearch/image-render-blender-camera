#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /camera_pinhole.py
# Created Date: Thursday, October 22nd 2020, 2:51:36 pm
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

import anyblend.ops_image
import bpy
import bmesh
import math
import mathutils
import json
import numpy as np

from . import util

from .. import ops
from .. import node
from .. import material
from .. import model
from ..mesh import solids
import anyblend
from anybase.cls_anyexcept import CAnyExcept


#####################################################################
# Create the camera name
def CreateName(_sName):
    return "Cam.PinGen.{0}".format(_sName)


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

    # Calculate Blender Units per Millimeter
    fBUperMM = fScale * 1e-3 / bpy.context.scene.unit_settings.scale_length

    #####################################################
    # Get camera data
    dicSensor = _dicCamera.get("dicSensor")
    dicProject = _dicCamera.get("dicProject")

    lVigCoef = dicProject.get("lVignetting")
    fVigNorm = dicProject.get("fVignettingNorm")

    fPixSize_um = dicSensor.get("fPixSize")
    iPixCntX = dicSensor.get("iPixCntX")
    iPixCntY = dicSensor.get("iPixCntY")

    sUnit = dicProject.get("sUnit")
    if sUnit is None:
        raise RuntimeError("Element 'sUnit' not defined")
    # endif

    if sUnit == "pixel":
        fPixPerVal = 1.0
    elif sUnit == "mm":
        fPixPerVal = 1.0 / (1e-3 * fPixSize_um)
    else:
        raise RuntimeError("Unsupported unit '{}'".format(sUnit))
    # endif

    lSenSizeXY = dicProject.get("lSenSizeXY")
    lSenSizeXY_pix = [int(round(x * fPixPerVal)) for x in lSenSizeXY]
    if iPixCntX != lSenSizeXY_pix[0] or iPixCntY != lSenSizeXY_pix[1]:
        return {
            "bResult": False,
            "objCam": None,
            "sMsg": (
                "Given sensor '{}' has different pixel count than calibration data in projection '{}'".format(
                    dicSensor.get("sId"), dicProject.get("sId")
                )
            ),
        }
    # endif

    #####################################################
    # Get tangential/prism/tilt distortion coefficients - currently unsupported
    lDistTan = dicProject.get("lDistTan")
    if any(lDistTan):
        raise RuntimeError(f"Tangential distortion parameters (unsupported) given: {[x for x in lDistTan]}.")
    lDistPrism = dicProject.get("lDistPrism")
    if any(lDistPrism):
        raise RuntimeError(f"Prism distortion parameters (unsupported) given: {[x for x in lDistPrism]}.")
    lDistTilt = dicProject.get("lDistTilt")
    if any(lDistTilt):
        raise RuntimeError(f"Tilt distortion parameters (unsupported) given: {[x for x in lDistTilt]}.")

    #####################################################
    # Create ray direction lookup image
    lFocLenXY = dicProject.get("lFocLenXY")
    if lFocLenXY is None:
        raise RuntimeError("Missing normalized focal length element 'lFocLenXY' in camera definition")
    # endif
    lFocLenXY_pix = [int(round(x * fPixPerVal)) for x in lFocLenXY]

    lImgCtrXY = dicProject.get("lImgCtrXY")
    if lImgCtrXY is None:
        raise RuntimeError("Missing normalized image center element 'lImgCtrXY' in camera definition")
    # endif
    lImgCtrXY_pix = [int(round(x * fPixPerVal)) for x in lImgCtrXY]

    lDistRad = dicProject.get("lDistRad", [0.0, 0.0])
    if not isinstance(lDistRad, list):
        raise RuntimeError("Expect element 'lDistRad' to be a list of 2, 3, or 6 floats")
    # endif

    iDistCnt = len(lDistRad)
    if iDistCnt == 0:
        lDistRad = [0.0, 0.0]
    elif iDistCnt not in [2, 3, 6]:
        raise RuntimeError("Expect element 'lDistRad' to be a list of 2, 3, or 6 floats")
    # endif

    fFac = fFac2 = 1.0 / (fPixPerVal * fPixPerVal)
    lDistRad_pix = lDistRad.copy()
    iDistCnt = len(lDistRad)
    iCnt = min(3, iDistCnt)
    for iIdx in range(iCnt):
        lDistRad_pix[iIdx] = fFac * lDistRad[iIdx]
        if iDistCnt == 6:
            lDistRad_pix[iIdx + 3] = fFac * lDistRad[iIdx + 3]
        # endif
        fFac *= fFac2
    # endfor

    dicLut = model.camera_opencv.create_lookup((iPixCntX, iPixCntY), lFocLenXY_pix, lImgCtrXY_pix, lDistRad_pix)
    if dicLut is None:
        return {
            "bResult": False,
            "objCam": None,
            "sMsg": "Error creating inverse projection lookup table",
        }
    # endif
    aRayNorm = dicLut["aRays"]
    lFov_deg = dicLut["lFov_deg"]
    lFovRange_deg = dicLut["lFovRange_deg"]

    #####################################################
    # Create camera empty, that acts as origin for whole camera system

    # Create the name for the camera
    sCamName = CreateName(_sName)

    # get or create anycam collection where all cameras are placed
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

    fPixSize_mm = 1e-3 * fPixSize_um
    fSenSizeX_mm = fPixSize_mm * iPixCntX
    fSenSizeY_mm = fPixSize_mm * iPixCntY
    # fSenSizeMax_mm = max(fSenSizeX_mm, fSenSizeY_mm)
    # fFocLen_mm = fSenSizeMax_mm
    fFocLen_mm = lFocLenXY_pix[0] * fPixSize_mm

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

    camX.shift_x = 0.0
    camX.shift_y = 0.0

    camX.clip_start = fBUperMM * 0.5 * fFocLen_mm
    camX.clip_end = fBUperMM * 1e7
    camX.display_size = max(0.5, fBUperMM * fFocLen_mm)

    # Sensor position relative to camera origin, which is
    # on last glass surface towards environment.
    objCam.location = (0, 0, fFocLen_mm * fBUperMM)
    objCam.rotation_euler = (0, 0, 0)

    ##############################################################
    # Creating LUT image object
    sImgName = sCamName + ".RayDir"
    imgA = bpy.data.images.get(sImgName)
    if imgA is not None:
        bpy.data.images.remove(imgA)
    # endif
    imgA = bpy.data.images.new(sImgName, iPixCntX, iPixCntY, alpha=True, float_buffer=True, is_data=True)
    sImgName = imgA.name
    # bpy.ops.image.new(name=sImgName, width=iImgW, height=iImgH)
    # imgA = bpy.data.images[sImgName]
    imgA.use_fake_user = True

    # add a fourth color channel to store data as Blender image
    aRayImg = np.c_[aRayNorm, np.ones((iPixCntY, iPixCntX, 1))]

    # print("LUT pixel count: {}".format(aRayImg.size))
    # print("image pixel count: {}".format(len(imgA.pixels)))

    # Copy the actual pixels into the Blender image
    imgA.pixels = list(aRayImg.flatten())

    # Pack image in Blender file
    anyblend.ops_image.Pack(imgA)

    # Create a texture that uses the image to ensure that the image is not deleted by Blender
    sTexName = sCamName + ".RayDir.Tex"
    texA = bpy.data.textures.get(sTexName)
    if texA is not None:
        bpy.data.textures.remove(texA)
    # endif
    texA = bpy.data.textures.new(sTexName, type="IMAGE")
    texA.image = imgA
    texA.use_fake_user = True

    #####################################################
    # Create plane with refractor that acts as sensor plane
    sRefractorName = sSenName + ".RF"

    objRF = bpy.data.objects.get(sRefractorName)
    if objRF is not None:
        bpy.data.objects.remove(objRF)
    # endif

    meshRF = bpy.data.meshes.get(sRefractorName)
    if meshRF is not None:
        bpy.data.meshes.remove(meshRF)
    # endif

    meshRF = bpy.data.meshes.new(sRefractorName)
    objRF = bpy.data.objects.new(name=sRefractorName, object_data=meshRF)
    cnMain.objects.link(objRF)

    # objRF.location = (-lCenter_mm[0], -lCenter_mm[1], 0)
    objRF.location = (0, 0, 0)

    try:
        # Get Refractor Material
        matRF, ngLut = material.ray_lut.Create(
            sId=sCamName,
            sImgLut=imgA.name,
            lSenSizeXY_pix=[iPixCntX, iPixCntY],
            fPixSize_mm=fPixSize_mm,
            lCenter_mm=[0.0, 0.0],
            fVignettingNormRadius_mm=fVigNorm,
            lVignettingCoef=lVigCoef,
            bForce=True,
        )
    except Exception as xEx:
        return {
            "bResult": False,
            "objCam": objCamOrig,
            "sMsg": "Exception creating LUT material:\n{}".format(str(xEx)),
        }
    # endtry

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

    dicAnyCamEx.update(
        {
            "mDepData": {
                "images": [imgA.name],
                "textures": [texA.name],
                "materials": [matRF.name],
                "node_groups": [ngLut.name],
            }
        }
    )

    objCam["AnyCam"] = json.dumps(
        {
            "sDTI": "/anycam/camera/pingen/opencv:1.2",
            "iSenResX": iPixCntX,
            "iSenResY": iPixCntY,
            "fAspectX": 1.0,
            "fAspectY": 1.0,
            "fPixSize_um": dicSensor.get("fPixSize"),
            "sOrigin": objCamOrig.name,
            "lFov_deg": lFov_deg,
            "lFovRange_deg": lFovRange_deg,
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
