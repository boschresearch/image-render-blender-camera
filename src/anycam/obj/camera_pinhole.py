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

import bpy
import bmesh
import math
import mathutils
import pyjson5 as json

from . import util
from .cls_cameraview_pinhole import CCameraViewPinhole

from .. import ops
from ..mesh import solids
import anyblend
from anybase.cls_anyexcept import CAnyExcept


#####################################################################
# Create the camera name
def CreateName(_sName):
    return "Cam.Pin.{0}".format(_sName)


# enddef


#####################################################################
# Create Light Field Trace Cameras
def Create(
    _sName,
    _dicCamera,
    bOverwrite=False,
    fScale=1.0,
    bCreateFrustum=False,
    dicAnyCamEx=None,
):

    # Calculate Blender Units per Millimeter
    fBUperMM = fScale * 1e-3 / bpy.context.scene.unit_settings.scale_length

    #####################################################
    # Get camera data
    dicSensor = _dicCamera.get("dicSensor")
    dicPinhole = _dicCamera.get("dicPinhole")
    iEnsureSquarePixel = _dicCamera.get("iEnsureSquarePixel", 0)

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
        if bOverwrite == True:
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

    # objCamOrig = bpy.data.objects.new(sCamName, None)
    # objCamOrig.location = (0, 0, 0)
    # objCamOrig.empty_display_size = 1
    # objCamOrig.empty_display_type = "PLAIN_AXES"
    # cnMain.objects.link(objCamOrig)

    #####################################################
    # Create render pinhole camera

    camX = bpy.data.cameras.get(sCamName)
    if camX is not None:
        bpy.data.cameras.remove(camX)
        camX = None
    # endif

    camX = bpy.data.cameras.new(sCamName)
    objCam = bpy.data.objects.new(name=sCamName, object_data=camX)

    vlMain = bpy.context.view_layer
    cnMain.objects.link(objCam)
    vlMain.objects.active = objCam
    objCam.select_set(True)

    dicFovRange = dicPinhole.get("mFovRange")
    if dicFovRange is not None:
        lFovH = dicFovRange.get("lHorizontal")
        if lFovH is None:
            raise CAnyExcept("No horizontal field-of-view given")
        # endif
        lFovV = dicFovRange.get("lVertical")
        if lFovV is None:
            raise CAnyExcept("No vertical field-of-view given")
        # endif
        lFovRange = [lFovH, lFovV]
    else:
        lFovRange = None
    # endif

    xView = CCameraViewPinhole()
    xView.Init(
        lPixCnt=[dicSensor.get("iPixCntX"), dicSensor.get("iPixCntY")],
        fPixSize_um=dicSensor.get("fPixSize"),
        fFovMax_deg=dicPinhole.get("fFovMax_deg"),
        lFov_deg=dicPinhole.get("lFov_deg"),
        lFovRange_deg=lFovRange,
        bEnsureSquarePixel=iEnsureSquarePixel != 0,
    )

    camX.type = "PERSP"
    camX.lens = xView.fFocLen_mm
    camX.lens_unit = "MILLIMETERS"
    camX.sensor_width = xView.fSenSizeX_mm
    camX.sensor_height = xView.fSenSizeY_mm

    if xView.fSenSizeX_mm >= xView.fSenSizeY_mm:
        camX.sensor_fit = "HORIZONTAL"
    else:
        camX.sensor_fit = "VERTICAL"
    # endif

    lShift = xView.EvalShift()
    camX.shift_x = lShift[0]
    camX.shift_y = lShift[1]

    # lFovCtrRatio = [lFovCenter_deg[i] / lFov_deg[i] for i in range(2)]

    # if fSenSizeX_mm >= fSenSizeY_mm:
    # 	camX.shift_x = lFovCtrRatio[0]
    # 	camX.shift_y = lFovCtrRatio[1] * (fSenSizeY_mm / fSenSizeX_mm)
    # else:
    # 	camX.shift_x = lFovCtrRatio[0] * (fSenSizeX_mm / fSenSizeY_mm)
    # 	camX.shift_y = lFovCtrRatio[1]
    # # endif

    camX.clip_start = fBUperMM * xView.fFocLen_mm / 2.0
    camX.clip_end = fBUperMM * 1e7
    camX.display_size = max(0.5, fBUperMM * xView.fSenSizeMax_mm / 2.0)

    #############################################################
    # Create Frustum Object and Mesh
    if bCreateFrustum:
        fSX = xView.fSenSizeX_mm / xView.fFocLen_mm
        fSY = xView.fSenSizeY_mm / xView.fFocLen_mm
        fOffX = xView.fSenCtrX_mm / xView.fFocLen_mm
        fOffY = xView.fSenCtrY_mm / xView.fFocLen_mm

        # print("Pyramid FoV X: {0}".format(2.0*math.degrees(math.atan(fSX/2.0))))
        # print("Pyramid FoV Y: {0}".format(2.0*math.degrees(math.atan(fSY/2.0))))

        objFS = solids.CreatePyramid(
            "Frustum.Pin.S." + _sName, fSX, fSY, -1.0, fOffX=fOffX, fOffY=fOffY
        )
        cnMain.objects.link(objFS)  # put the object into the scene (link)

        fScale = 1000.0
        objFL = solids.CreatePyramid(
            "Frustum.Pin.L." + _sName,
            fScale * fSX,
            fScale * fSY,
            -fScale,
            fOffX=fOffX * fScale,
            fOffY=fOffY * fScale,
        )
        cnMain.objects.link(objFL)  # put the object into the scene (link)

        anyblend.viewlayer.Update()
        # Make Frustum child of camera object
        anyblend.object.ParentObjectList(objCam, [objFL, objFS], bKeepTransform=False)
        anyblend.object.Hide(objFS, bHide=True, bHideInAllViewports=True, bHideRender=True)
        anyblend.object.Hide(objFL, bHide=True, bHideInAllViewports=True, bHideRender=True)


    # endif (CreateFrustum)

    #############################################################
    # Store AnyCam Data
    if dicAnyCamEx is None:
        dicAnyCamEx = {}
    # endif

    objCam["AnyCam"] = json.dumps(
        {
            "sDTI": "/anycam/camera/pin:1.2",
            "iSenResX": xView.iPixCntX,
            "iSenResY": xView.iPixCntY,
            "fAspectX": xView.fAspectX,
            "fAspectY": xView.fAspectY,
            "fPixSize_um": dicSensor.get("fPixSize"),
            "fFovMax_deg": dicPinhole.get("fFovMax_deg"),
            "lFov_deg": dicPinhole.get("lFov_deg"),
            "lFovRange_deg": lFovRange,
            "bEnsureSquarePixel": iEnsureSquarePixel != 0,
            "mEx": dicAnyCamEx,
        }
    )

    return {"bResult": True, "objCam": objCam, "objAnyCam": objCam}


# enddef
