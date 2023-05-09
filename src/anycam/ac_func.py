#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /ac_func.py
# Created Date: Thursday, October 22nd 2020, 2:51:39 pm
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

####################################################################
# AnyCam Plugin Functions

import os
import sys
import pyjson5 as json
from typing import Optional

import bpy
from . import ac_global
from . import ops, ops_camset
from . import util
from .ac_props_camloc import UpdateFrustum
from anybase import config
from anybase.cls_anyexcept import CAnyExcept
import anyblend


#######################################################################################
def UpdateAllFrustums(*, _xContext: Optional[bpy.types.Context] = None):

    xCtx: bpy.types.Context = None
    if _xContext is not None:
        xCtx = _xContext
    else:
        xCtx = bpy.context
    # endif

    lFrustum, lMatch = ops_camset.FindAllCameraFrustums(bpy.data.objects)
    for xF in lFrustum:
        anyblend.object.Hide(xF, bHide=True, bHideInAllViewports=True, bHideRender=True)
    # endfor

    xAcCamSetList = xCtx.scene.AcPropsCamSets
    global g_reCameraEx

    if xAcCamSetList.bValidSelection:
        xCamSet = xAcCamSetList.Selected
        for xCamLoc in xCamSet.clCameras:
            UpdateFrustum(xCamLoc)
        # endfor
    # endif

    xAcProps = xCtx.window_manager.AcProps

    for xCamObj in xAcProps.clCamObj:
        objCam: bpy.types.Object = bpy.data.objects.get(xCamObj.sLabel)
        if objCam is None:
            continue
        # endif

        objChild: bpy.types.Object
        for objChild in objCam.children:
            if objChild.name.startswith("Frustum"):
                anyblend.object.Hide(objChild, bHide=True, bHideInAllViewports=True, bHideRender=True)
            # endif
        # endfor
    # endfor


# enddef


#######################################################################################
# Update AnyCam camera object list
def CamObjUpdate(self, context):
    try:
        xAcProps = context.window_manager.AcProps
        ops.CamObjUpdate(xAcProps.clCamObj)
        UpdateAllFrustums()

    except Exception as xEx:
        if hasattr(self, "report"):
            self.report({"ERROR"}, str(xEx))
        else:
            print(f"ERROR: {(str(xEx))}")
        # endif
    # endtry


# enddef


#######################################################################################
# Callback functions used by properties and operators
def PathCamDbUpdate(self, context):
    # print("Running Path Cam Data Update")

    try:
        xAcProps = context.window_manager.AcProps
        # print(xAcProps.sPathCamData)

        # user_prefs = context.user_preferences
        # addon_prefs = user_prefs.addons[__package__].preferences
        # print("Addon prefs: " + addon_prefs.sAcDataPath)
        # # Store current path in preferences
        # addon_prefs.sAcDataPath = xAcProps.sPathCamData
        # bpy.ops.wm.save_userpref()

        # User provided path to camera data packages.
        sAcDataPath = bpy.path.abspath(xAcProps.sPathCamData)
        # print(sAcDataPath)

        # Load Camera modules
        dicAcDb = ops.LoadDataPkg(sAcDataPath)
        ops.AddAnyCamDb(dicAcDb)

    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endtry


# enddef

#######################################################################################
# Create the full Blender camera object name from the camear db name and a user name
def CreateFullCameraName(context, _iCamDbIdx):
    xAcProps = context.window_manager.AcProps

    if _iCamDbIdx < 0 or _iCamDbIdx >= len(xAcProps.clCamDb):
        return ""
    # endif

    sUserName = xAcProps.sCamName
    xCamInfo = xAcProps.clCamDb[_iCamDbIdx]
    sCamId = xCamInfo.sId

    sFullCamName = ops.CreateFullCameraName(sUserName, sCamId, _dicAnyCamDb=ac_global.dicAnyCamDb)
    return sFullCamName


# enddef


#######################################################################################
# Callback functions used by properties and operators
def CreateSelectedCamera(self, context):
    xAcProps = context.window_manager.AcProps
    # print(xAcProps.iCamDbSelIdx)

    sCamName = xAcProps.sCamName
    fScale = xAcProps.fCameraScale

    xCamInfo = xAcProps.clCamDb[xAcProps.iCamDbSelIdx]
    sCamId = xCamInfo.sId

    # print(sCamId)
    lRet = ops.CreateCameraFromDb(sCamName, sCamId, xAcProps.bOverwriteCamera, fScale=fScale)

    if lRet.get("bResult") is False:
        self.report({"ERROR"}, lRet.get("sMsg", "Error in creating camera"))
    # endif


# enddef


#######################################################################################
# Select Camera
def SelectCamera(self, context):

    xAcProps = context.window_manager.AcProps
    if xAcProps.iCamObjSelIdx >= 0 and xAcProps.iCamObjSelIdx < len(xAcProps.clCamObj):
        xCamInfo = xAcProps.clCamObj[xAcProps.iCamObjSelIdx]
        sCamId = xCamInfo.sLabel
        objCam = bpy.data.objects.get(sCamId)

        if objCam is not None:
            bpy.ops.object.select_all(action="DESELECT")
            objCam.select_set(True)
            context.view_layer.objects.active = objCam

            # xAcProps.iCamResX = xCamInfo.iResX
        # endif
    # endif


# enddef


#######################################################################################
# Activate selected camera
def ActivateSelectedCamera(self, context):

    xAcProps = context.window_manager.AcProps

    xCamInfo = xAcProps.clCamObj[xAcProps.iCamObjSelIdx]
    sCamId = xCamInfo.sLabel
    iResX = xCamInfo.iResX
    iResY = xCamInfo.iResY
    # print(sCamId)

    try:
        if xAcProps.bTransformSceneToCameraFrame is True:
            TransformSceneToCameraFrame(self, context, bRevert=True)
        # endif

        ops.ActivateCamera(
            context,
            sCamId,
            iResX=iResX,
            iResY=iResY,
            bApplyRenderPars=xAcProps.bApplyRenderParsOnActivation,
        )

        if xAcProps.bTransformSceneToCameraFrame is True:
            TransformSceneToCameraFrame(self, context, bRevert=False)
        # endif

    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endtry


# enddef


#######################################################################################
# Activate selected camera
def RemoveSelectedCamera(self, context):

    xAcProps = context.window_manager.AcProps

    xCamInfo = xAcProps.clCamObj[xAcProps.iCamObjSelIdx]
    sCamId = xCamInfo.sLabel
    dicCam = ops.GetAnyCam(context, sCamId)

    xAcCamSetList = context.scene.AcPropsCamSets
    if xAcCamSetList is not None:
        for xCamSet in xAcCamSetList.clCamSets:
            for xCamLoc in xCamSet.clCameras:
                if xCamLoc.sAnyCamLabel == sCamId:
                    self.report(
                        {"WARNING"},
                        "Camera '{0}' is part of camera set '{1}'. Remove camera set before removing camera".format(
                            sCamId, xCamSet.sId
                        ),
                    )
                    return
                # endif
            # endfor
        # endfor
    # endif

    dicAnyCam = dicCam.get("dicAnyCam")
    sOrigin = dicAnyCam.get("sOrigin")
    if sOrigin is None:
        objX = dicCam.get("objCam")
        if objX is None:
            raise CAnyExcept("Camera object not found")
        # endif
    else:
        objX = bpy.data.objects.get(sOrigin)
        if objX is None:
            raise CAnyExcept("Camera origin object '{0}' not found".format(sOrigin))
        # endif
    # endif

    dicAnyCamEx = dicAnyCam.get("mEx")
    if dicAnyCamEx is not None:
        dicDepData = dicAnyCamEx.get("mDepData")
        if dicDepData is not None:
            for sDataContainer in dicDepData:
                if not hasattr(bpy.data, sDataContainer):
                    continue
                # endif
                xData = getattr(bpy.data, sDataContainer)
                lNames = dicDepData.get(sDataContainer)
                for sName in lNames:
                    xItem = xData.get(sName)
                    if xItem is not None:
                        xData.remove(xItem)
                    # endif
                # endfor names
            # endfor data container
        # endif has dep data
    # endif has anycam ex

    try:
        ops.DeleteObjectHierarchy(objX)
    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endtry


# enddef


#######################################################################################
# Callback when selecting a list element
def CameraInfoSelected(self, context):

    pass
    # xAcProps = context.window_manager.AcProps

    # print(xAcProps.iCamDbSelIdx)


# enddef

#######################################################################################
def AssignRenderParsToSelectedCamera(self, context):

    xAcProps = context.window_manager.AcProps

    iSelIdx = xAcProps.iCamObjSelIdx
    if iSelIdx < 0 or iSelIdx >= len(xAcProps.clCamObj):
        self.report({"ERROR"}, "No camera selected")
        return
    # endif

    xCamInfo = xAcProps.clCamObj[iSelIdx]
    sCamId = xCamInfo.sLabel
    sCamType = xCamInfo.sType

    objCam = bpy.data.objects.get(sCamId, None)
    if objCam is None:
        self.report({"ERROR"}, "Camera '{0}' not found.".format(sCamId))
        return
    # endif

    scMain = bpy.context.scene
    dicPars = ops.GetBlenderPars(scMain, ac_global.dicRenderParsDef)
    dicAnyCam = ops.LoadAnyCamData(objCam)

    if sCamType == "lft":
        if dicPars["render"]["engine"] != "CYCLES":
            self.report({"ERROR"}, "Switch to 'cycles' render engine to use LFT cameras.")
            return
        # endif

        iRefractSurfCnt = dicAnyCam["iRefractSurfCnt"]

        if dicPars["cycles"]["transmission_bounces"] < iRefractSurfCnt:
            dicPars["cycles"]["transmission_bounces"] = iRefractSurfCnt
            scMain.cycles.transmission_bounces = iRefractSurfCnt
            self.report(
                {"WARNING"},
                "The Cycles maximal transmission bounces are set to {0}.".format(iRefractSurfCnt),
            )
        # endif

        if dicPars["cycles"]["max_bounces"] < iRefractSurfCnt:
            dicPars["cycles"]["max_bounces"] = iRefractSurfCnt
            scMain.cycles.max_bounces = iRefractSurfCnt
            self.report(
                {"WARNING"},
                "The Cycles maximal bounces are set to {0}.".format(iRefractSurfCnt),
            )
        # endif
    # endif

    dicAnyCam["mRenderPars"] = dicPars
    objCam["AnyCam"] = json.dumps(dicAnyCam)


# enddef

#######################################################################################
def ApplyRenderParsFromSelectedCamera(self, context):

    xAcProps = context.window_manager.AcProps

    iSelIdx = xAcProps.iCamObjSelIdx
    if iSelIdx < 0 or iSelIdx >= len(xAcProps.clCamObj):
        self.report({"ERROR"}, "No camera selected")
        return
    # endif

    xCamInfo = xAcProps.clCamObj[iSelIdx]
    sCamId = xCamInfo.sLabel
    # sCamType = xCamInfo.sType

    try:
        ops.ApplyCameraRenderPars(context, sCamId)
    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endtry


# enddef


#######################################################################################
# Set the LFT rendering wavelength
def SetLftRenderWavelength(self, context):

    from . import node

    node.grp.render_pars.SetValues(Wavelength=self.iLftRenderWavelength)


# enddef


#######################################################################################
# Transform Scene To Camera Frame
def TransformSceneToCameraFrame(self, context, bRevert):

    try:
        if bRevert is True:
            ops.RevertTransformSceneToCameraFrame(xContext=context)
        else:
            ops.TransformSceneToCameraFrame(xContext=context)
        # endif
    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endtry


# enddef
