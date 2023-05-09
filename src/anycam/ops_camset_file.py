#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ops_camset.py
# Created Date: Friday, April 30th 2021, 1:38:08 pm
# Author: Christian Perwass (CR/AEC5)
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
import re
import os
from pathlib import Path
from typing import Optional

from anybase import config
from anybase import path as anypath
from anybase.cls_any_error import CAnyError_Message

from . import ac_global
from . import ops
from . import ops_camset

###################################################################################
def Export(_xContext):

    xAcCamSetList = _xContext.scene.AcPropsCamSets

    if not xAcCamSetList.bValidSelection:
        raise Exception("Not camera set selected")
    # endif

    xCamSet = xAcCamSetList.Selected
    if xCamSet.iCount == 0:
        raise Exception("Nothing to export")
    # endif

    lCathPaths = xCamSet.GetCathPaths()
    if any(len(x) == 0 for x in lCathPaths):
        raise Exception("There are undefined paths")
    # endif

    if len(lCathPaths) > len(set(lCathPaths)):
        raise Exception("The paths are not unique")
    # endif

    sPathData = bpy.path.abspath(xCamSet.sPathExport)
    if not os.path.exists(sPathData):
        raise Exception("Given export path does not exist")
    # endif

    if xCamSet.bExportFileExists and not xCamSet.bExportOverwrite:
        return False, "Existing file not overwritten: {0}".format(xCamSet.GetExportFilePath())
    # endif

    dicCamSet = {}
    for xCamLoc in xCamSet.clCameras:
        dicAcCam = ops.GetAnyCam(_xContext, xCamLoc.sAnyCamLabel)
        dicAnyCam = dicAcCam.get("dicAnyCam")

        dicDataSource = {}
        dicAcEx = dicAnyCam.get("mEx")
        if dicAcEx is not None:
            mSrcPkg = dicAcEx.get("mSrcPkg")
            if mSrcPkg is not None:
                dicDataSource["mSrcPkg"] = mSrcPkg
            # endif
            sSrcCamId = dicAcEx.get("sSrcCamId")
            if sSrcCamId is not None:
                dicDataSource["sSrcCamId"] = sSrcCamId
            # endif

            xBlendPath = Path(bpy.data.filepath)
            dicDataSource["mBlender"] = {
                "sFile": xBlendPath.name,
                "sScene": _xContext.scene.name,
                "sViewLayer": _xContext.view_layer.name,
            }
        # endif

        dicCam = {
            "sDTI": "camera-pose:1.1",
            # xCamLoc.objCamera may differ from dicAcCam.get("objCam"),
            # as it may be the origin of a camera package
            "sCamera": xCamLoc.sAnyCamLabel,
            "sParent": xCamLoc.objLocation.name,
            "mDataSource": dicDataSource,
        }

        config.SetElementAtPath(dicCamSet, xCamLoc.sCathPath, dicCam)
    # endfor

    dicFile = {"sId": xCamSet.sId, "mConfigs": dicCamSet}

    sFilename = xCamSet.sId.replace(".", "_")
    config.Save((sPathData, sFilename), dicFile, sDTI="/catharsys/camera-set:1.0")

    dicPaths = {"lCamPose": lCathPaths}

    sFileCamPose = "{0}_campose".format(sFilename)
    config.Save((sPathData, sFileCamPose), dicPaths, sDTI="/catharsys/camera-set/pose-paths:1.0")

    return True, os.path.join(sPathData, sFilename)


# enddef

###################################################################################
def Import(_xContext):

    xAcCamSetList = _xContext.scene.AcPropsCamSets

    if not xAcCamSetList.bImportFileExists:
        return False, "Import file does not exist: {0}".format(xAcCamSetList.GetImportFilePath())
    # endif

    xPath = Path(xAcCamSetList.GetImportFilePath())

    try:
        dicData = config.Load((xPath.parent, xPath.name), sDTI="/catharsys/camera-set:1.0")
    except Exception as xEx:
        return False, "Error importing camera set: {0}".format(str(xEx))
    # endtry

    sId = dicData.get("sId")
    if sId is None:
        return False, "Config file has no 'sId' element"
    # endif

    lCamSetIds = xAcCamSetList.GetIdList()
    if sId in lCamSetIds:
        return False, "Id '{0}' of import file already exists".format(sId)
    # endif

    dicCamSet = dicData.get("mConfigs")
    if dicCamSet is None:
        return False, "Configuration data does not contain tag 'mConfigs'"
    # endif

    lPaths = config.GetDictPaths(dicCamSet, sDTI="camera-pose:1")
    lCamIds = []
    lCamObjs = []
    lLocObjs = []
    for sPath in lPaths:
        dicCamPose = config.GetDictValue(dicCamSet, sPath, dict, bAllowKeyPath=True, sWhere="camera set")
        # dicCamPose = config.GetElementAtPath(dicCamSet, sPath)
        sCamId = dicCamPose.get("sCamera")
        dicCam = ops.GetAnyCam(_xContext, sCamId, bRaiseException=False)
        if dicCam is None:

            # Check whether camera name has the correct structure
            # to be loaded from an AnyCam DB
            xMatchCam = ops_camset.g_reCameraEx.match(sCamId)
            if xMatchCam is None:
                return (
                    False,
                    "Camera '{0}' does not exist and can not be created automatically".format(sCamId),
                )
            # endif

            dicDataSource = dicCamPose.get("mDataSource")
            if dicDataSource is None:
                return (
                    False,
                    "Camera '{0}' does not exist and can not be created automatically".format(sCamId),
                )
            # endif

            dicSrcPkg = dicDataSource.get("mSrcPkg")
            sSrcCamId = dicDataSource.get("sSrcCamId")
            if dicSrcPkg is None or sSrcCamId is None:
                return (
                    False,
                    "Camera '{0}' does not exist and data source does not contain necessary information to create camera".format(
                        sCamId
                    ),
                )
            # endif

            sSrcPkgId = dicSrcPkg.get("sId")
            if sSrcCamId is None:
                return (
                    False,
                    "Camera '{0}' does not exist and source package data does not contain 'sId' tag".format(sCamId),
                )
            # endif

            dicSrcPkgDb = ac_global.dicAnyCamDb.get("_mSrcPkgDb")
            if dicSrcPkgDb is None or dicSrcPkgDb.get(sSrcPkgId) is None:
                return (
                    False,
                    "Camera '{0}' does not exist. Please load camera database '{1}' ({2}) to create it".format(
                        sCamId, dicSrcPkg.get("sName", sSrcPkgId), sSrcPkgId
                    ),
                )
            # endif

            dicResult = ops.CreateCameraFromDb(xMatchCam.group("username"), sSrcCamId, False)
            if not dicResult.get("bResult"):
                return (
                    False,
                    "Camera '{0}' does not exist and creation from database resulted in error: {1}".format(
                        sCamId, dicResult.get("sMsg")
                    ),
                )
            # endif

            dicCam = ops.GetAnyCam(_xContext, sCamId, bRaiseException=False)
            if dicCam is None:
                return False, "Camera '{0}' does not exist and could not be created"
            # endif
        # endif
        objCam = dicCam.get("objCam")
        dicAnyCam = dicCam.get("dicAnyCam")
        sOrigin = dicAnyCam.get("sOrigin")
        if sOrigin is not None:
            objOrig = _xContext.scene.objects.get(sOrigin)
            if objOrig is None:
                return False, "Origin '{0}' of camera '{1}' does no exist".format(sOrigin, sCamId)
            # endif
            objCam = objOrig
        # endif
        lCamIds.append(sCamId)
        lCamObjs.append(objCam)

        sLocId = dicCamPose.get("sParent")
        objLoc = _xContext.scene.objects.get(sLocId)
        if objLoc is None:
            return False, "Location '{0}' does not exist".format(sLocId)
        # endif

        if objLoc.type != "EMPTY":
            return False, "Location '{0}' is not an Empty".format(sLocId)
        # endif
        lLocObjs.append(objLoc)
    # endfor

    xCamSet = xAcCamSetList.Add(sId=sId)
    for iIdx, sPath in enumerate(lPaths):
        xCamLoc = ops_camset.AddCamLoc(
            _xContext,
            xCamSet=xCamSet,
            objCam=lCamObjs[iIdx],
            objLoc=lLocObjs[iIdx],
            sAnyCamLabel=lCamIds[iIdx],
        )

        xCamLoc.sCathPath = sPath
    # endfor

    xAcProps = _xContext.window_manager.AcProps
    ops.CamObjUpdate(xAcProps.clCamObj)

    return True, xPath.as_posix()


# endif


###################################################################################
def ImportCamera(
    *,
    _sCamSetId: str,
    _sCamDbPath: str,
    _sCamPosePath: str,
    _sCamId: str,
    _sCamName: str,
    _sParent: str,
    _bReplace: bool = True,
    _xContext: Optional[bpy.types.Context] = None,
) -> str:

    xCtx: bpy.types.Context = None
    if _xContext is None:
        xCtx = bpy.context
    else:
        xCtx = _xContext
    # endif

    try:
        if not hasattr(xCtx.scene, "AcPropsCamSets"):
            raise RuntimeError(f"Scene '{xCtx.scene.name}' does not contain AnyCam data structures")
        # endif

        xAcCamSetList = xCtx.scene.AcPropsCamSets

        objLoc: bpy.types.Object = xCtx.scene.objects.get(_sParent)
        if objLoc is None:
            raise RuntimeError(f"Camera parent location '{_sParent}' does not exist")
        # endif

        pathCamDb: Path = anypath.MakeNormPath(_sCamDbPath)
        if not pathCamDb.exists():
            raise RuntimeError(f"Camera database path does not exist: {(pathCamDb.as_posix())}")
        # endif

        # Load camera database
        dicAcDb = ops.LoadDataPkg(pathCamDb.as_posix())
        ops.AddAnyCamDb(dicAcDb)

        # Create Camera
        dicResult = ops.CreateCameraFromDb(_sCamName, _sCamId, _bReplace, fScale=1.0)
        if not dicResult["bResult"]:
            sMsg: str = dicResult["sMsg"]
            raise RuntimeError(f"Error creating camera '{_sCamId}' from database '{_sCamDbPath}': {sMsg}")
        # endif

        objCam: bpy.types.Object = dicResult.get("objCam")
        objAnyCam: bpy.types.Object = dicResult.get("objAnyCam")
        if objCam is None or objAnyCam is None:
            raise RuntimeError(f"Error creating camera '{_sCamId}' from database '{_sCamDbPath}': {sMsg}")
        # endif

        lCamSetIds = xAcCamSetList.GetIdList()
        xCamSet = None
        if _sCamSetId not in lCamSetIds:
            xCamSet = xAcCamSetList.Add(sId=_sCamSetId)
        else:
            xCamSet = xAcCamSetList.Get(_sCamSetId)
        # endif

        # xCamSet.bShowFrustum = False
        # xCamSet.bShowIntersection = False

        xCamLoc = ops_camset.AddCamLoc(xCtx, xCamSet=xCamSet, objCam=objCam, objLoc=objLoc, sAnyCamLabel=objAnyCam.name)
        xCamLoc.sCathPath = _sCamPosePath
        xCamLoc.bShowCameraFrustum = False
        xCamLoc.bShowIntersection = False

        xAcProps = xCtx.window_manager.AcProps
        ops.CamObjUpdate(xAcProps.clCamObj)

        return objAnyCam.name
    except Exception as xEx:
        raise CAnyError_Message(sMsg=f"Error importing camera '{_sCamId}' from database '{_sCamDbPath}'", xChildEx=xEx)
    # endtry


# enddef
