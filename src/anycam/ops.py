#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /ops.py
# Created Date: Thursday, October 22nd 2020, 2:51:43 pm
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
# LF-Trace package main operations
import bpy
import mathutils
import os
import re
from pathlib import Path
import pyjson5 as json

from ison.util import data as isondata

from . import node
from . import obj
from . import ac_global

from anybase import config
from anybase import file
from anybase.cls_anyexcept import CAnyExcept

# Constants
c_sOriginName = ".temp.AnyCam.Origin.World"
c_sWorldMatrixName = ".temp.AnyCam.matrix_world"


#################################################################
# Create a lens system from the given data modules
def CreateLensSystem(modLensData, modMediaData):
    # TODO: Could update or delete function

    # Init render parameters
    node.grp.render_pars.Create()

    # Get media dictionary
    dicMedia = modMediaData.GetData()
    # print(dicMedia)

    # Create node groups for media refraction for all given media
    node.grp.media.Update(dicMedia)

    # Get lens system data
    lLensSys = modLensData.GetData()
    # print(lLensSys)

    # Create the lens system
    # obj.optics.CreateLensSystem(lLensSys)


# enddef


#######################################################################################
def LoadAnyCamData(_objCam, bUpdateObject=True):
    if _objCam is None:
        raise Exception("Empty camera object given")
    # endif

    if _objCam.type != "CAMERA":
        raise Exception("Given object is not a camera")
    # endif

    sAnyCam = _objCam.get("AnyCam")
    if sAnyCam is None:
        sAnyCam = json.dumps({"sDTI": "/anycam/camera/std:1.0", "iSenResX": bpy.context.scene.render.resolution_x, "iSenResY": bpy.context.scene.render.resolution_y})
        if bUpdateObject:
            _objCam["AnyCam"] = sAnyCam
        # endif
    # endif

    dicAnyCam = json.loads(sAnyCam)

    # Test for old AnyCam structure type and try to convert it
    lType = dicAnyCam.get("lType")
    if lType is not None:
        if lType[1] == "pano":
            dicAnyCam["sDTI"] = "/anycam/camera/pano/equidist:1.0"
        else:
            dicAnyCam["sDTI"] = "/anycam/camera/{0}:1.0".format(lType[1])
        # endif
        _objCam["AnyCam"] = json.dumps(dicAnyCam)
    # endif

    return dicAnyCam


# enddef


#######################################################################################
# Get list of AnyCam objects of given type
def GetCameraObjects():
    lObjList = []

    for xObj in bpy.data.objects:
        if xObj.type == "CAMERA":
            dicAnyCam = LoadAnyCamData(xObj)
            lObjList.append({"objCam": xObj, "dicAnyCam": dicAnyCam})
        # endif
    # endfor

    return lObjList


# enddef


#######################################################################################
# Get the anycam data of the camera with the given id
def GetAnyCam(_xContext, _sCamId, bRaiseException=True):
    objCam = bpy.data.objects.get(_sCamId)
    if objCam is None:
        if bRaiseException:
            raise Exception("Camera '{0}' not found.".format(_sCamId))
        else:
            return None
        # endif
    # endif

    dicAnyCam = LoadAnyCamData(objCam)

    return {"objCam": objCam, "dicAnyCam": dicAnyCam}


# enddef


#######################################################################################
# Get camera type from DTI of AnyCam object data block
def GetAnyCamType(_dicCam):
    dicCamType = config.SplitDti(_dicCam.get("sDTI"))
    lCamType = dicCamType.get("lType")
    sType = lCamType[2]

    if len(lCamType) > 3:
        sSubType = lCamType[3]
        sTypeName = "{0}/{1}".format(sType, sSubType)
    else:
        sSubType = ""
        sTypeName = sType
    # endif

    return {"sType": sType, "sSubType": sSubType, "sTypeName": sTypeName}


# enddef


#######################################################################################
# Get type of anycam
def GetAnyCamTypeFromId(_xContext, _sCamId, bRaiseException=True):
    dicRes = GetAnyCam(_xContext, _sCamId, bRaiseException=bRaiseException)
    if dicRes is None:
        return None
    # enddef

    dicAnyCam = dicRes.get("dicAnyCam")
    return GetAnyCamType(dicAnyCam)


# enddef


############################################################################################
def ParentAnyCam(*, sCamId, sParentId=None):
    dicObj = bpy.data.objects

    objCam = dicObj.get(sCamId)
    if objCam is None:
        raise Exception("Child object with id '{0}' not found".format(sCamId))
    # endif

    dicAnyCam = LoadAnyCamData(objCam)
    sOrigin = dicAnyCam.get("sOrigin")
    objC = objCam
    if sOrigin is not None:
        objOrig = bpy.data.objects.get(sOrigin)
        if objOrig is not None:
            objC = objOrig
        # endif0
    # endif

    if sParentId is not None:
        objP = dicObj.get(sParentId)
        if objP is None:
            raise Exception("Parent object with id '{0}' not found".format(sParentId))
        # endif

        objC.parent = objP
    else:
        objC.parent = None
    # endif


# enddef


#######################################################################################
# Set an AnyCam Object Property
def SetAnyCamProp(_xContext, _sCamId, _sPropId, _xValue):
    dicObj = GetAnyCam(_xContext, _sCamId)
    dicAnyCam = dicObj.get("dicAnyCam")
    dicAnyCam[_sPropId] = _xValue
    dicObj.get("objCam")["AnyCam"] = json.dumps(dicAnyCam)


# enddef


#######################################################################################
# Set AnyCam Sensor Resolution X
def SetAnyCamSenResX(_xContext, _sCamId, _iValue):
    SetAnyCamProp(_xContext, _sCamId, "iSenResX", _iValue)


# enddef


#######################################################################################
# Set AnyCam Sensor Resolution Y
def SetAnyCamSenResY(_xContext, _sCamId, _iValue):
    SetAnyCamProp(_xContext, _sCamId, "iSenResY", _iValue)


# enddef


######################################################
# Get list of names of children of Object
def GetObjectChildrenNames(objMain, Recursive=False):
    lNames = []
    for objChild in objMain.children:
        lNames.append(objChild.name)
        if Recursive and objChild.children is not None:
            lNames += GetObjectChildrenNames(objChild, Recursive=True)
        # endif
    # endfor

    return lNames


# enddef


######################################################
# Enable/disable render for object hierarchy
def EnableObjectHierarchy(*, objMain, bRender=None, bView=None, bViewport=None, sRegExIgnore=None):
    lNames = [objMain.name]
    lNames += GetObjectChildrenNames(objMain, Recursive=True)

    if sRegExIgnore is not None:
        reIgnore = re.compile(sRegExIgnore)
        lNames = [sName for sName in lNames if reIgnore.match(sName) is None]
    # endif

    for sName in lNames:
        try:
            objX = bpy.data.objects.get(sName)
            if isinstance(bRender, bool):
                objX.hide_render = not bRender
            # endif
            if isinstance(bView, bool):
                objX.hide_set(not bView)
            # endif
            if isinstance(bViewport, bool):
                objX.hide_viewport = not bViewport
            # endif
        except Exception:
            print("AnyCam Warning: Cannot hide object '{0}'".format(objX.name))
        # endtry
    # endfor


# enddef


######################################################
# Store the various hide states of an object
def StoreObjectHierarchyEnableStates(*, objMain, sRegExIgnore=None):
    lNames = [objMain.name]
    lNames += GetObjectChildrenNames(objMain, Recursive=True)

    if sRegExIgnore is not None:
        reIgnore = re.compile(sRegExIgnore)
        lNames = [sName for sName in lNames if reIgnore.match(sName) is None]
    # endif

    for sName in lNames:
        objX = bpy.data.objects.get(sName)
        dicData = {
            "bRender": objX.hide_render,
            "bView": objX.hide_get(),
            "bViewport": objX.hide_viewport,
        }
        objX["AnyCam.Enable"] = json.dumps(dicData)
    # endfor


# enddef


######################################################
# Load previously stored hide states of an object
def LoadObjectHierarchyEnableStates(*, objMain, sRegExIgnore=None):
    lNames = [objMain.name]
    lNames += GetObjectChildrenNames(objMain, Recursive=True)

    if sRegExIgnore is not None:
        reIgnore = re.compile(sRegExIgnore)
        lNames = [sName for sName in lNames if reIgnore.match(sName) is None]
    # endif

    for sName in lNames:
        objX = bpy.data.objects.get(sName)
        sData = objX.get("AnyCam.Enable")
        if sData is not None:
            dicData = json.loads(sData)
            bHide = dicData.get("bRender")
            if isinstance(bHide, bool):
                objX.hide_render = bHide
            # endif
            bHide = dicData.get("bView")
            if isinstance(bHide, bool):
                objX.hide_set(bHide)
            # endif
            bHide = dicData.get("bViewport")
            if isinstance(bHide, bool):
                objX.hide_viewport = bHide
            # endif
        # endif
    # endfor


# enddef


######################################################
# Delete object hierarchy
def DeleteObjectHierarchy(objMain):
    # bpy.ops.object.select_all(action='DESELECT')

    lNames = [objMain.name]
    lNames += GetObjectChildrenNames(objMain, Recursive=True)

    # print(lNames)
    for sName in lNames:
        objX = bpy.data.objects.get(sName)
        objX.animation_data_clear()
        bpy.data.objects.remove(objX)
    # endfor
    #
    # lObjects = bpy.data.objects

    # [lObjects[sName].select_set(True) for sName in lNames]

    # # Remove the animation from the all the child objects
    # for sName in lNames:
    # 	bpy.data.objects[sName].animation_data_clear()
    # # endfor

    # sResult = bpy.ops.object.delete()
    # return sResult


# enddef


######################################################
# Delete Collection Hierarchy
def DeleteCollectionHierarchy(_cnMain):
    for objX in _cnMain.objects:
        bpy.data.objects.remove(objX)
    # endfor

    bpy.data.collections.remove(_cnMain)


# enddef


##################################################################
# Preprocess package data for use in libs
def PreparePkgData(_sDataType, _dicData, _dicSrcPkg):
    if _sDataType == "media":
        dicMedia = _dicData.get("mMedia")
        for sMedia in dicMedia:
            dicData = dicMedia[sMedia]
            dicRefIdx = dicData["mRefIdx"] = {}

            for lRefMap in dicData["lRefIdx"]:
                dicRefIdx[lRefMap[0]] = lRefMap[1]
            # endfor
        # endfor
    # endif

    _dicData["_sSrcPkgId"] = _dicSrcPkg.get("sId")


# enddef


##################################################################
def IsCameraDbPackage(_sPath, _sFile):
    dicR = config.Load((_sPath, _sFile), sDTI="/package/anycam/camera-db:1.*", bDoThrow=False)
    return dicR.get("bOK")


# enddef


##################################################################
# Function to load all camera modules in a user specified path
def LoadDataPkg(_sMainPkgPath):
    # Get all subfolders of the user provided path, that contain a file '__init__.py'.
    # These are the packages we are interested in.
    sMainPkgPath = _sMainPkgPath
    if os.path.exists(os.path.join(sMainPkgPath, "package.json")):
        if IsCameraDbPackage(sMainPkgPath, "package.json"):
            xP = Path(sMainPkgPath)
            lPackageNames = [xP.name]
            sMainPkgPath = xP.parent.as_posix()
        # endif
    else:
        lPackageNames = [
            f.name for f in os.scandir(sMainPkgPath) if f.is_dir() and IsCameraDbPackage(f.path, "package.json")
        ]
    # endif

    # Debug info
    # print(lPackageNames)

    # Initialize dictionary of all data in package
    dicAcDb = {}
    dicPkgDb = dicAcDb["_mSrcPkgDb"] = {}

    # Check if any packages were found
    if len(lPackageNames) > 0:
        for sPkgName in lPackageNames:
            sPkgPath = os.path.normpath(os.path.join(sMainPkgPath, sPkgName))
            dicPkg = config.Load((sPkgPath, "package.json"), sDTI="/package/anycam/camera-db:1.*")
            dicPkgDb[dicPkg.get("sId")] = dicPkg

            for sRoot, lDirs, lFiles in os.walk(sPkgPath):
                for sFile in lFiles:
                    if sFile.endswith(".json") or sFile.endswith(".json5") or sFile.endswith(".ison"):
                        try:
                            dicData = config.Load((sRoot, sFile), sDTI="/anycam/db/*:*", bAddPathVars=True)
                            dicDti = config.SplitDti(dicData.get("sDTI"))
                            sDataType = dicDti["lType"][2]
                            if sDataType not in dicAcDb:
                                dicAcDb[sDataType] = {}
                            # endif
                            dicTypeDb = dicAcDb[sDataType]

                            # Get the relative path from the package dir
                            sRelPath = os.path.relpath(sRoot, sPkgPath)
                            lRelPath = sRelPath.split(os.path.sep)

                            sId = dicData.get("sId", None)
                            if sId is not None:
                                PreparePkgData(sDataType, dicData, dicPkg)
                                lRelPath.append(sId)
                                sId = "/".join(lRelPath)
                                dicTypeDb[sId] = dicData
                            # endif
                        except Exception as xEx:
                            print("Ignoring config file: {0}\n> {1}\n".format(os.path.join(sRoot, sFile), str(xEx)))
                            pass
                        # endtry
                    # endif
                # endfor
            # endfor
        # endfor

        # Debug info
        # print(lCamNames)
        # print(dicCamMod)
    # endif

    return dicAcDb


# enddef


#######################################################################################
# Get camera type from DTI of AnyCam DB data block
def GetAnyCamDbType(_dicCam):
    dicCamType = config.SplitDti(_dicCam.get("sDTI"))
    lCamType = dicCamType.get("lType")
    iCamTypeCnt = len(lCamType)

    if iCamTypeCnt < 4:
        raise RuntimeError("Invalid camera type: {}".format(_dicCam.get("sDTI")))
    # endif

    sType = lCamType[3]

    # print(f"_dicCam: {_dicCam}")
    sProjectId = _dicCam.get("sProjectId")
    if sProjectId is None:
        if sType == "pin":
            sProjectId = _dicCam.get("sPinholeId")
        elif sType == "pano":
            sProjectId = _dicCam.get("sPanoId")
        elif sType == "poly":
            sProjectId = _dicCam.get("sPolyId")
        # endif
    # endif

    if sProjectId is not None:
        # sys.stderr.write(f"ac_global.dicAnyCamDb['project']: {ac_global.dicAnyCamDb['project']}\n")
        # sys.stderr.write(f"sProjectId: {sProjectId}")

        dicPrj = ac_global.dicAnyCamDb["project"].get(sProjectId)
        if dicPrj is None:
            raise RuntimeError(f"Projection id '{sProjectId}' not found in camera DB")
        # endif
        # sys.stderr.write(f"dicPrj: {dicPrj}")
        # sys.stderr.flush()

        dicPrjType = config.SplitDti(dicPrj.get("sDTI"))
        lPrjType = dicPrjType.get("lType")
        if len(lPrjType) >= 5:
            sSubType = "/".join(lPrjType[4:])
            sTypeName = "{0}/{1}".format(sType, sSubType)
        else:
            sSubType = ""
            sTypeName = sType
        # endif
    else:
        sSubType = ""
        sTypeName = sType
    # endif

    return {"sType": sType, "sSubType": sSubType, "sTypeName": sTypeName}


# enddef


#######################################################################################
def AddAnyCamDb(_dicAnyCamDb: dict, *, _xContext: bpy.types.Context = None):
    xCtx: bpy.types.Context = None
    if _xContext is not None:
        xCtx = _xContext
    else:
        xCtx = bpy.context
    # endif

    xAcProps = xCtx.window_manager.AcProps

    ac_global.dicAnyCamDb.update(_dicAnyCamDb)
    # print(ac_global.dicAnyCamDb)

    ###############################################
    # Initialize UI List Data
    # Clear camera info collection
    xAcProps.clCamDb.clear()

    # Add loaded camera names to list
    dicCamDb = ac_global.dicAnyCamDb.get("camera", None)
    if dicCamDb is not None:
        for sCamId in dicCamDb:
            dicCam = dicCamDb[sCamId]
            dicCamType = GetAnyCamDbType(dicCam)

            xItem = xAcProps.clCamDb.add()
            xItem.sLabel = dicCam["sName"]
            xItem.sType = dicCamType.get("sTypeName")
            xItem.sId = sCamId
            xItem.sToolTip = "{0}, {1}".format(xItem.sLabel, xItem.sType)
        # endfor
    # endif


# enddef


#######################################################################################
# Combine all Media databases into one
def CombineMediaDbs(_dicMediaPkgs):
    dicMediaDb = {}

    for sId in _dicMediaPkgs:
        dicMediaDb.update(_dicMediaPkgs[sId]["mMedia"])
    # endfor

    return dicMediaDb


# endif


#######################################################################################
def CreateFullCameraName(_sUserName, _sCamId, *, _dicAnyCamDb: dict):
    dicCamList = _dicAnyCamDb.get("camera")
    if dicCamList is None:
        raise RuntimeError("AnCam database does not contain camera dictionary")
    # endif

    dicCam = dicCamList.get(_sCamId)
    if dicCam is None:
        raise Exception("Camera id '{0}' not found in database".format(_sCamId))
    # endif

    dicCamType = config.SplitDti(dicCam.get("sDTI"))
    sCamType = dicCamType.get("lType")[3]
    sCamName = dicCam.get("sName")
    sUserName = _sUserName.replace(" ", "_").replace(".", "_")

    sHalfCamName = "{0}.{1}".format(sUserName, sCamName.replace(" ", "_"))

    if sCamType == "lft":
        sFullCamName = obj.camera_lft.CreateName(sHalfCamName)
    elif sCamType == "lut":
        sFullCamName = obj.camera_lut.CreateName(sHalfCamName)
    elif sCamType == "pin":
        sFullCamName = obj.camera_pinhole.CreateName(sHalfCamName)
    elif sCamType == "pingen":
        sFullCamName = obj.camera_pin_gen.CreateName(sHalfCamName)
    elif sCamType == "pano":
        sFullCamName = obj.camera_pano.CreateName(sHalfCamName)
    elif sCamType == "poly":
        sFullCamName = obj.camera_poly.CreateName(sHalfCamName)
    else:
        raise Exception("Camera type '{0}' not supported.".format(sCamType))
    # endif

    return sFullCamName


# enddef


#######################################################################################
# Create a camera from database data
def CreateCameraFromDb(_sName, _sCamId, _bOverwrite, fScale=1.0, *, _dicAnyCamDb: dict = None):
    if _dicAnyCamDb is None:
        dicAnyCamDb = ac_global.dicAnyCamDb
    else:
        dicAnyCamDb = _dicAnyCamDb
    # endif

    dicCamList = dicAnyCamDb.get("camera")
    if dicCamList is None:
        raise RuntimeError("Given camera database does not contain cameras")
    # endif

    dicCam = dicCamList.get(_sCamId)
    if dicCam is None:
        return {"bResult": False, "sMsg": "Camera Id '{0}' not found.".format(_sCamId)}
    # endif

    # print("-------------")
    # print(_sCamId)
    # print(dicCam)
    # print("-------------")

    dicAnyCamEx = {}
    sSrcPkg = dicCam.get("_sSrcPkgId")
    dicSrcPkgDb = dicAnyCamDb.get("_mSrcPkgDb")
    if sSrcPkg is not None and dicSrcPkgDb is not None:
        dicSrcPkg = dicSrcPkgDb.get(sSrcPkg)
        if dicSrcPkg is not None:
            dicAnyCamEx["mSrcPkg"] = isondata.StripVarsFromData(dicSrcPkg)
            dicAnyCamEx["sSrcCamId"] = _sCamId
        # endif
    # endif

    dicCamType = config.SplitDti(dicCam.get("sDTI"))
    sCamType = dicCamType.get("lType")[3]

    if sCamType == "lft":
        dicRet = CreateCameraLftFromDb(
            _sName, dicCam, _bOverwrite, dicAnyCamEx=dicAnyCamEx, fScale=fScale, _dicAnyCamDb=dicAnyCamDb
        )
    elif sCamType == "lut":
        dicRet = CreateCameraLutFromDb(
            _sName, dicCam, _bOverwrite, dicAnyCamEx=dicAnyCamEx, fScale=fScale, _dicAnyCamDb=dicAnyCamDb
        )
    elif sCamType == "pin":
        dicRet = CreateCameraPinholeFromDb(
            _sName, dicCam, _bOverwrite, dicAnyCamEx=dicAnyCamEx, fScale=fScale, _dicAnyCamDb=dicAnyCamDb
        )
    elif sCamType == "pingen":
        dicRet = CreateCameraPinGenFromDb(
            _sName, dicCam, _bOverwrite, dicAnyCamEx=dicAnyCamEx, fScale=fScale, _dicAnyCamDb=dicAnyCamDb
        )
    elif sCamType == "pano":
        dicRet = CreateCameraPanoFromDb(
            _sName, dicCam, _bOverwrite, dicAnyCamEx=dicAnyCamEx, fScale=fScale, _dicAnyCamDb=dicAnyCamDb
        )
    elif sCamType == "poly":
        dicRet = CreateCameraPolyFromDb(
            _sName, dicCam, _bOverwrite, dicAnyCamEx=dicAnyCamEx, fScale=fScale, _dicAnyCamDb=dicAnyCamDb
        )
    else:
        dicRet = {
            "bResult": False,
            "sMsg": "Camera type '{0}' not supported.".format(sCamType),
        }
    # endif

    return dicRet


# enddef


#######################################################################################
# Create Lft Camera
def CreateCameraLftFromDb(_sName, _dicCam, _bOverwrite, dicAnyCamEx=None, fScale=1.0, *, _dicAnyCamDb: dict):
    sSensorId = _dicCam.get("sSensorId")
    sLensSystemId = _dicCam.get("sLensSystemId", _dicCam.get("sProjectId"))

    if sSensorId is None:
        raise CAnyExcept("No sensor specified for camera '{0}'".format(_sName))
    # endif

    if sLensSystemId is None:
        raise CAnyExcept("No lens system specified for camera '{0}'".format(_sName))
    # endif

    dicSensor = _dicAnyCamDb.get("sensor").get(sSensorId)
    dicLensSys = _dicAnyCamDb.get("opticalsystem").get(sLensSystemId)

    if dicSensor is None:
        raise CAnyExcept("Sensor '{0}' not found in database".format(sSensorId))
    # endif

    if dicLensSys is None:
        raise CAnyExcept("Lens system '{0}' not found in database".format(sLensSystemId))
    # endif

    dicMedia = CombineMediaDbs(_dicAnyCamDb.get("media"))
    if dicMedia is None:
        raise CAnyExcept("Media dictionary cannot be found")
    # endif

    dicCamera = {}
    dicCamera["sName"] = _dicCam["sName"]
    dicCamera["dicMedia"] = dicMedia
    dicCamera["dicLensSys"] = dicLensSys
    dicCamera["dicSensor"] = dicSensor
    dicCamera["dicLftPars"] = _dicCam["mLftPars"]

    dicAnyCamEx["mSensor"] = isondata.StripVarsFromData(dicSensor)

    bRenewMaterials = False

    return CreateCameraLft(
        _sName.replace(" ", "_").replace(".", "_"),
        dicCamera,
        bOverwrite=_bOverwrite,
        bForce=bRenewMaterials,
        fScale=fScale,
        dicAnyCamEx=dicAnyCamEx,
    )


# enddef


#######################################################################################
# Create LUT Camera
def CreateCameraLutFromDb(_sName, _dicCam, _bOverwrite, dicAnyCamEx=None, fScale=1.0, *, _dicAnyCamDb: dict):
    # sSensorId = _dicCam.get("sSensorId")
    sProjectId = _dicCam.get("sProjectId")

    # if sSensorId is None:
    #     raise CAnyExcept("No sensor specified for camera '{0}'".format(_sName))
    # # endif

    if sProjectId is None:
        raise CAnyExcept("No projection specified for camera '{0}'".format(_sName))
    # endif

    # dicSensor = _dicAnyCamDb.get("sensor").get(sSensorId)
    dicProject = _dicAnyCamDb.get("project").get(sProjectId)

    # if dicSensor is None:
    #     raise CAnyExcept("Sensor '{0}' not found in database".format(sSensorId))
    # # endif

    if dicProject is None:
        raise CAnyExcept("Projection '{0}' not found in database".format(sProjectId))
    # endif

    dicCamera = {}
    dicCamera["sName"] = _dicCam.get("sName")
    # dicCamera["dicSensor"] = dicSensor
    dicCamera["dicProject"] = dicProject

    # dicAnyCamEx["mSensor"] = dicSensor

    fScale *= _dicCam.get("fSensorScale", 1.0)

    return CreateCameraLut(
        _sName.replace(" ", "_").replace(".", "_"),
        dicCamera,
        bOverwrite=_bOverwrite,
        fScale=fScale,
        dicAnyCamEx=dicAnyCamEx,
    )


# enddef


#######################################################################################
# Create Pinhole Camera
def CreateCameraPinholeFromDb(_sName, _dicCam, _bOverwrite, dicAnyCamEx=None, fScale=1.0, *, _dicAnyCamDb: dict):
    sSensorId = _dicCam.get("sSensorId")
    sPinholeId = _dicCam.get("sPinholeId", _dicCam.get("sProjectId"))

    if sSensorId is None:
        raise CAnyExcept("No sensor specified for camera '{0}'".format(_sName))
    # endif

    if sPinholeId is None:
        raise CAnyExcept("No pinhole specified for camera '{0}'".format(_sName))
    # endif

    dicSensor = _dicAnyCamDb.get("sensor").get(sSensorId)
    dicPinhole = _dicAnyCamDb.get("project").get(sPinholeId)

    if dicSensor is None:
        raise CAnyExcept("Sensor '{0}' not found in database".format(sSensorId))
    # endif

    if dicPinhole is None:
        raise CAnyExcept("Pinhole '{0}' not found in database".format(sPinholeId))
    # endif

    dicCamera = {}
    dicCamera["sName"] = _dicCam.get("sName")
    dicCamera["dicSensor"] = dicSensor
    dicCamera["dicPinhole"] = dicPinhole
    dicCamera["iEnsureSquarePixel"] = _dicCam.get("iEnsureSquarePixel", 0)

    dicAnyCamEx["mSensor"] = isondata.StripVarsFromData(dicSensor)

    return CreateCameraPinhole(
        _sName.replace(" ", "_").replace(".", "_"),
        dicCamera,
        bOverwrite=_bOverwrite,
        fScale=fScale,
        dicAnyCamEx=dicAnyCamEx,
    )


# enddef


#######################################################################################
# Create Generalized Pinhole Camera
def CreateCameraPinGenFromDb(_sName, _dicCam, _bOverwrite, dicAnyCamEx=None, fScale=1.0, *, _dicAnyCamDb: dict):
    sSensorId = _dicCam.get("sSensorId")
    sProjectId = _dicCam.get("sProjectId")

    if sSensorId is None:
        raise CAnyExcept("No sensor specified for camera '{0}'".format(_sName))
    # endif

    if sProjectId is None:
        raise CAnyExcept("No projection specified for camera '{0}'".format(_sName))
    # endif

    dicSensor = _dicAnyCamDb.get("sensor").get(sSensorId)
    dicProject = _dicAnyCamDb.get("project").get(sProjectId)

    if dicSensor is None:
        raise CAnyExcept("Sensor '{0}' not found in database".format(sSensorId))
    # endif

    if dicProject is None:
        raise CAnyExcept("Projection '{0}' not found in database".format(sProjectId))
    # endif

    dicCamera = {}
    dicCamera["sName"] = _dicCam.get("sName")
    dicCamera["dicSensor"] = dicSensor
    dicCamera["dicProject"] = dicProject

    dicAnyCamEx["mSensor"] = isondata.StripVarsFromData(dicSensor)

    fScale *= _dicCam.get("fSensorScale", 1.0)

    return CreateCameraPinholeGeneralized(
        _sName.replace(" ", "_").replace(".", "_"),
        dicCamera,
        bOverwrite=_bOverwrite,
        fScale=fScale,
        dicAnyCamEx=dicAnyCamEx,
    )


# enddef


#######################################################################################
# Create Pano Camera
def CreateCameraPanoFromDb(_sName, _dicCam, _bOverwrite, dicAnyCamEx=None, fScale=1.0, *, _dicAnyCamDb: dict):
    sSensorId = _dicCam.get("sSensorId")
    sPanoId = _dicCam.get("sPanoId", _dicCam.get("sProjectId"))

    if sSensorId is None:
        raise CAnyExcept("No sensor specified for camera '{0}'".format(_sName))
    # endif

    if sPanoId is None:
        raise CAnyExcept("No panoramic projection specified for camera '{0}'".format(_sName))
    # endif

    dicSensor = _dicAnyCamDb.get("sensor").get(sSensorId)
    dicPano = _dicAnyCamDb.get("project").get(sPanoId)

    if dicSensor is None:
        raise CAnyExcept("Sensor '{0}' not found in database".format(sSensorId))
    # endif

    if dicPano is None:
        raise CAnyExcept("Panoramic projection '{0}' not found in database".format(sPanoId))
    # endif

    dicCamera = {}
    dicCamera["sName"] = _dicCam.get("sName")
    dicCamera["dicSensor"] = dicSensor
    dicCamera["dicPano"] = dicPano
    dicCamera["iEnsureSquarePixel"] = _dicCam.get("iEnsureSquarePixel", 0)

    dicAnyCamEx["mSensor"] = isondata.StripVarsFromData(dicSensor)

    return CreateCameraPano(
        _sName.replace(" ", "_").replace(".", "_"),
        dicCamera,
        bOverwrite=_bOverwrite,
        fScale=fScale,
        dicAnyCamEx=dicAnyCamEx,
    )


# enddef


#######################################################################################
# Create Pano Camera
def CreateCameraPolyFromDb(_sName, _dicCam, _bOverwrite, dicAnyCamEx=None, fScale=1.0, *, _dicAnyCamDb: dict):
    sSensorId = _dicCam.get("sSensorId")
    sPolyId = _dicCam.get("sPolyId", _dicCam.get("sProjectId"))

    if sSensorId is None:
        raise CAnyExcept("No sensor specified for camera '{0}'".format(_sName))
    # endif

    if sPolyId is None:
        raise CAnyExcept("No panoramic projection specified for camera '{0}'".format(_sName))
    # endif

    dicSensor = _dicAnyCamDb.get("sensor").get(sSensorId)
    dicPoly = _dicAnyCamDb.get("project").get(sPolyId)

    if dicSensor is None:
        raise CAnyExcept("Sensor '{0}' not found in database".format(sSensorId))
    # endif

    if dicPoly is None:
        raise CAnyExcept("Panoramic projection '{0}' not found in database".format(sPolyId))
    # endif

    dicCamera = {}
    dicCamera["sName"] = _dicCam["sName"]
    dicCamera["dicSensor"] = dicSensor
    dicCamera["dicPoly"] = dicPoly

    dicAnyCamEx["mSensor"] = isondata.StripVarsFromData(dicSensor)

    return CreateCameraPoly(
        _sName.replace(" ", "_").replace(".", "_"),
        dicCamera,
        bOverwrite=_bOverwrite,
        fScale=fScale,
        dicAnyCamEx=dicAnyCamEx,
    )


# enddef


#################################################################
# Create a LFT camera
def CreateCameraLft(_sName, _dicCamera, bOverwrite=False, bForce=False, fScale=1.0, dicAnyCamEx=None):
    sCamName = "{0}.{1}".format(_sName, _dicCamera["sName"].replace(" ", "_"))
    return obj.camera_lft.Create(
        sCamName,
        _dicCamera,
        bOverwrite=bOverwrite,
        bForce=bForce,
        fScale=fScale,
        dicAnyCamEx=dicAnyCamEx,
    )


# enddef


#################################################################
# Create a lut camera
def CreateCameraLut(_sName, _dicCamera, bOverwrite=False, fScale=1.0, dicAnyCamEx=None):
    sCamName = "{0}.{1}".format(_sName, _dicCamera["sName"].replace(" ", "_"))
    return obj.camera_lut.Create(
        sCamName,
        _dicCamera,
        bOverwrite=bOverwrite,
        fScale=fScale,
        bCreateFrustum=True,
        dicAnyCamEx=dicAnyCamEx,
    )


# enddef


#################################################################
# Create a pinhole camera
def CreateCameraPinhole(_sName, _dicCamera, bOverwrite=False, fScale=1.0, dicAnyCamEx=None):
    sCamName = "{0}.{1}".format(_sName, _dicCamera["sName"].replace(" ", "_"))
    return obj.camera_pinhole.Create(
        sCamName,
        _dicCamera,
        bOverwrite=bOverwrite,
        fScale=fScale,
        bCreateFrustum=True,
        dicAnyCamEx=dicAnyCamEx,
    )


# enddef


#################################################################
# Create a pinhole camera
def CreateCameraPinholeGeneralized(_sName, _dicCamera, bOverwrite=False, fScale=1.0, dicAnyCamEx=None):
    sCamName = "{0}.{1}".format(_sName, _dicCamera["sName"].replace(" ", "_"))
    return obj.camera_pin_gen.Create(
        sCamName,
        _dicCamera,
        bOverwrite=bOverwrite,
        fScale=fScale,
        bCreateFrustum=True,
        dicAnyCamEx=dicAnyCamEx,
    )


# enddef


#################################################################
# Create a pano camera
def CreateCameraPano(_sName, _dicCamera, bOverwrite=False, fScale=1.0, dicAnyCamEx=None):
    sCamName = "{0}.{1}".format(_sName, _dicCamera["sName"].replace(" ", "_"))
    return obj.camera_pano.Create(
        sCamName,
        _dicCamera,
        bOverwrite=bOverwrite,
        fScale=fScale,
        bCreateFrustum=True,
        dicAnyCamEx=dicAnyCamEx,
    )


# enddef


#################################################################
# Create a poly camera


def CreateCameraPoly(_sName, _dicCamera, bOverwrite=False, fScale=1.0, dicAnyCamEx=None):
    sCamName = "{0}.{1}".format(_sName, _dicCamera["sName"].replace(" ", "_"))
    return obj.camera_poly.Create(
        sCamName,
        _dicCamera,
        bOverwrite=bOverwrite,
        fScale=fScale,
        bCreateFrustum=True,
        dicAnyCamEx=dicAnyCamEx,
    )


# enddef


#######################################################################################
def GetBlenderPars(_xCtx, _dicParDef):
    dicData = {}

    for sPar in _dicParDef:
        if sPar == "_values_":
            lNames = _dicParDef[sPar]
            for sName in lNames:
                dicData[sName] = getattr(_xCtx, sName)
            # endfor
        else:
            xSubCtx = getattr(_xCtx, sPar)
            dicData[sPar] = GetBlenderPars(xSubCtx, _dicParDef[sPar])
        # endif
    # endfor

    return dicData


# enddef


#######################################################################################
def SetBlenderPars(_xCtx, _dicParDef, _dicValues):
    for sPar in _dicParDef:
        if sPar == "_values_":
            lNames = _dicParDef[sPar]
            for sName in lNames:
                xValue = _dicValues.get(sName, None)
                if xValue is not None:
                    setattr(_xCtx, sName, _dicValues[sName])
                # endif
            # endfor
        else:
            dicSubVals = _dicValues.get(sPar, None)
            if dicSubVals is not None:
                xSubCtx = getattr(_xCtx, sPar)
                SetBlenderPars(xSubCtx, _dicParDef[sPar], dicSubVals)
            # endif
        # endif
    # endfor


# enddef


#######################################################################################
# Apply render parameters of camera
def ApplyCameraRenderPars(_xContext, _sCamId, bOptionalApply=True):
    objCam = bpy.data.objects.get(_sCamId, None)
    if objCam is None:
        raise Exception("Camera '{0}' not found.".format(_sCamId))
    # endif

    sAnyCam = objCam.get("AnyCam")
    if sAnyCam is None:
        if bOptionalApply is True:
            return
        else:
            raise Exception("Selected camera has no 'AnyCam' parameters.")
        # endif
    else:
        dicAnyCam = json.loads(sAnyCam)
    # endif

    dicPars = dicAnyCam.get("mRenderPars", None)
    if dicPars is None:
        if bOptionalApply is True:
            return
        else:
            raise Exception("Selected camera has no render parameters stored.")
        # endif
    # endif

    SetBlenderPars(_xContext.scene, ac_global.dicRenderParsDef, dicPars)


# enddef


#######################################################################################
def GetAnyCamView(_xContext: bpy.types.Context, _sCamId: str, *, _bAddExtrinsics: bool = False):
    dicCam: dict = GetAnyCam(_xContext, _sCamId)
    dicAnyCam: dict = dicCam.get("dicAnyCam")

    if _bAddExtrinsics is True:
        fMeterPerBU: float = bpy.context.scene.unit_settings.scale_length
        objCam: bpy.types.Object = dicCam["objCam"]
        matCamera = objCam.matrix_world
        dicAnyCam["lAxes"] = [list(x) for x in matCamera.to_euler().to_matrix().transposed()]
        dicAnyCam["lOrigin"] = [x * fMeterPerBU for x in matCamera.translation]
    # endif

    # Try to get a camera
    return obj.camera.CreateCameraView(dicAnyCam, bDoThrow=False)


# enddef


#######################################################################################
def GetAnyCamHorizFov_deg(_objCam, _dicAnyCam):
    # Try to get horizontal FoV for camera
    fFovHoriz_deg = None
    lFov_deg = _dicAnyCam.get("lFov_deg")
    if lFov_deg is None or not isinstance(lFov_deg, list) or len(lFov_deg) != 2 or lFov_deg[0] == 0:
        xView = obj.camera.CreateCameraView(_dicAnyCam, bDoThrow=False)
        if xView is not None:
            fFovHoriz_deg = xView.lFov_deg[0]
        else:
            fFovHoriz_deg = None  # math.degrees(_objCam.data.angle)
        # endif
    else:
        fFovHoriz_deg = lFov_deg[0]
    # endif

    return fFovHoriz_deg


# enddef


#######################################################################################
def GetAnyCamFov_deg(_objCam, _dicAnyCam):
    # Try to get horizontal FoV for camera
    lFov_deg = _dicAnyCam.get("lFov_deg")
    if lFov_deg is None or not isinstance(lFov_deg, list) or len(lFov_deg) != 2 or lFov_deg[0] == 0 or lFov_deg[1] == 0:
        xView = obj.camera.CreateCameraView(_dicAnyCam, bDoThrow=False)
        if xView is not None:
            lFov_deg = xView.lFov_deg
        else:
            lFov_deg = None
        # endif
    # endif

    return lFov_deg.copy()


# enddef


#######################################################################################
def GetCameraHorizFov_deg(_xContext, _sCamId):
    dicCam = GetAnyCam(_xContext, _sCamId)
    objCam = dicCam.get("objCam")
    dicAnyCam = dicCam.get("dicAnyCam")
    return GetAnyCamHorizFov_deg(objCam, dicAnyCam)


# endif


#######################################################################################
# Activate selected camera
def ActivateCamera(
    _xContext,
    _sCamId,
    iResX=1920,
    iResY=1080,
    bApplyRenderPars=True,
    bDisableAllOther=True,
):
    scMain = _xContext.scene
    dicCam = GetAnyCam(_xContext, _sCamId)
    objCam = dicCam.get("objCam")
    dicAnyCam = dicCam.get("dicAnyCam")

    sOrigin = dicAnyCam.get("sOrigin")
    objCamOrig = objCam
    if sOrigin is not None:
        objOrig = bpy.data.objects.get(sOrigin)
        if objOrig is not None:
            objCamOrig = objOrig
        # endif
    # endif

    EnableObjectHierarchy(
        objMain=objCamOrig,
        bRender=True,
        bView=True,
        bViewport=True,
        sRegExIgnore="^Frustum\..*",
    )
    if bDisableAllOther:
        lCamList = GetCameraObjects()
        for dicCam in lCamList:
            objC = dicCam.get("objCam")
            dicAC = dicCam.get("dicAnyCam")
            if objC.name == objCam.name:
                continue
            # endif
            objCO = objC
            if dicAC is not None:
                sO = dicAC.get("sOrigin")
                if sO is not None:
                    objO = bpy.data.objects.get(sO)
                    if objO is not None:
                        objCO = objO
                    # endif
                # endif
            # endif
            EnableObjectHierarchy(
                objMain=objCO,
                bRender=False,
                bView=False,
                bViewport=False,
                sRegExIgnore="^Frustum\..*",
            )
        # endfor
    # endif

    scMain.camera = objCam

    # bpy.ops.object.select_all(action='DESELECT')
    for objX in bpy.data.objects:
        objX.select_set(False)
    # endfor

    objCam.select_set(True)
    _xContext.view_layer.objects.active = objCam

    sCamDti = dicAnyCam.get("sDTI")
    if sCamDti is None:
        raise Exception("No AnyCam DTI type information string given in anycam data")
    # endif

    dicCamType = config.CheckDti(sCamDti, "/anycam/camera/*:1")
    if dicCamType.get("bOK") is False:
        raise Exception("Error activating camera: {0}".format(dicCamType.get("sMsg")))
    # endif

    sCamType = dicCamType.get("lCfgType")[2]

    scMain.render.resolution_x = dicAnyCam.get("iRenderResX", dicAnyCam.get("iSenResX", iResX))
    scMain.render.resolution_y = dicAnyCam.get("iRenderResY", dicAnyCam.get("iSenResY", iResY))
    scMain.render.resolution_percentage = 100
    scMain.render.pixel_aspect_x = dicAnyCam.get("fAspectX", 1.0)
    scMain.render.pixel_aspect_y = dicAnyCam.get("fAspectY", 1.0)

    lCrop = dicAnyCam.get("lCrop")
    if lCrop is not None:
        scMain.render.use_border = True
        scMain.render.use_crop_to_border = True
        scMain.render.border_min_x = lCrop[0]
        scMain.render.border_max_x = lCrop[1]
        scMain.render.border_min_y = lCrop[2]
        scMain.render.border_max_y = lCrop[3]
    else:
        scMain.render.use_border = False
        scMain.render.use_crop_to_border = False
        scMain.render.border_min_x = 0.0
        scMain.render.border_max_x = 1.0
        scMain.render.border_min_y = 0.0
        scMain.render.border_max_y = 1.0
    # endif

    if bApplyRenderPars:
        ApplyCameraRenderPars(_xContext, _sCamId)
    # endif

    if sCamType == "lft":
        if scMain.render.engine != "CYCLES":
            raise Exception("Activated camera only works with Cycles render engine.")
        else:
            iRefractSurfCnt = dicAnyCam.get("iRefractSurfCnt", None)
            if iRefractSurfCnt is not None:
                if scMain.cycles.max_bounces < iRefractSurfCnt:
                    scMain.cycles.max_bounces = iRefractSurfCnt
                    raise Exception("The Cycles maximal bounces are set to {0}.".format(iRefractSurfCnt))
                # endif
                if scMain.cycles.transmission_bounces < iRefractSurfCnt:
                    scMain.cycles.transmission_bounces = iRefractSurfCnt
                    raise Exception("The Cycles maximal transmission bounces are set to {0}.".format(iRefractSurfCnt))
                # endif
            # endif
        # endif
    # endif

    # Try to get horizontal FoV for camera
    fFovHoriz_deg = GetAnyCamHorizFov_deg(objCam, dicAnyCam)

    # Loop over all node trees and set AnyCam input variable default values.
    for ngX in bpy.data.node_groups:
        for ndX in ngX.nodes:
            for skIn in ndX.inputs:
                if skIn.name == "AnyCam.Active.Origin":
                    skIn.default_value = objCam
                elif fFovHoriz_deg is not None and skIn.name == "AnyCam.Active.hFoV":
                    skIn.default_value = fFovHoriz_deg
                # endif
            # endfor
        # endfor
    # endfor

    # Loop over all modifiers and check their input fields
    for objX in bpy.data.objects:
        for modX in objX.modifiers:
            if not hasattr(modX, "node_group"):
                continue
            # endif
            ngX = modX.node_group
            if hasattr(ngX, "inputs"):
                for inX in ngX.inputs:
                    if inX.name == "AnyCam.Active.Origin":
                        modX[inX.identifier] = objCam
                    elif fFovHoriz_deg is not None and inX.name == "AnyCam.Active.hFoV":
                        modX[inX.identifier] = float(fFovHoriz_deg)
                    # endif
                # endfor inputs
            elif hasattr(ngX, "interface"):
                for itemX in ngX.interface.items_tree:
                    if itemX.in_out != "INPUT":
                        continue
                    # endif

                    if itemX.name == "AnyCam.Active.Origin":
                        modX[itemX.identifier] = objCam
                    elif fFovHoriz_deg is not None and itemX.name == "AnyCam.Active.hFoV":
                        modX[itemX.identifier] = float(fFovHoriz_deg)
                    # endif
                # endfor items
            else:
                raise RuntimeError("Unsupported node group interface. Maybe incompatible Blender version.")
            # endif
        # endfor modifiers
    # endfor objects


# enddef


#######################################################################################
# Activate selected camera
def WriteCameraAnyCamData(_xContext, _sCamId, _sFilePath):
    dicAnyCam = GetAnyCam(_xContext, _sCamId).get("dicAnyCam")

    file.SaveJson(_sFilePath, dicAnyCam)


# enddef


#######################################################################################
# Find the next unique id given a basename and a starting index
def FindUniqueId(_sBaseName, _iStartIdx, _lIdList):
    iIdx = _iStartIdx
    while True:
        sId = "{0}.{1:03d}".format(_sBaseName, iIdx)
        if sId not in _lIdList:
            break
        # endif
        iIdx += 1
    # endwhile

    return sId


# enddef


#######################################################################################
# Ensure that the given name is unique in list, if not create a new one
def ProvideUniqueId(_sId, _lIdList, sDefaultBaseName="Element"):
    if _sId is None:
        sId = FindUniqueId(sDefaultBaseName, 0, _lIdList)
    else:
        if _sId in _lIdList:
            xMatch = re.match(r"(.*)\.(\d+)$", _sId)
            if xMatch is None:
                sId = FindUniqueId(_sId, 0, _lIdList)
            else:
                sId = FindUniqueId(xMatch.group(1), int(xMatch.group(2)) + 1, _lIdList)
            # endif
        else:
            sId = _sId
        # endif
    # endif

    return sId


# enddef


#######################################################################################
def UpdateItemToolTip(_xItem):
    _xItem.sToolTip = "\n{0}\n{1}x{2}\n{3}\n{4}".format(
        _xItem.sLabel, _xItem.iResX, _xItem.iResY, _xItem.sTypeName, _xItem.sRenderPars
    )


# enddef


#######################################################################################
# Update AnyCam camera object list
def CamObjUpdate(_clCamObj):
    lObjList = GetCameraObjects()

    _clCamObj.clear()

    for xObj in lObjList:
        xItem = _clCamObj.add()
        dicAnyCam = xObj.get("dicAnyCam")
        if dicAnyCam is not None:
            xItem.sLabel = xObj.get("objCam").name
            dicCamType = GetAnyCamType(dicAnyCam)
            xItem.sType = dicCamType.get("sType")
            xItem.sSubType = dicCamType.get("sSubType")
            xItem.sTypeName = dicCamType.get("sTypeName")

            if xItem.sType in ["lft", "poly", "pin", "pano", "pingen", "lut"]:
                lNames = xItem.sLabel.split(".")
                xItem.sName = lNames[2]
                xItem.sDesign = lNames[3]
            else:
                xItem.sName = xItem.sLabel
                xItem.sDesign = ""
            # endif
            xItem.iResX = dicAnyCam.get("iSenResX")
            xItem.iResY = dicAnyCam.get("iSenResY")
            xItem.bHasRenderPars = dicAnyCam.get("mRenderPars") is not None

            dicRenderPars = dicAnyCam.get("mRenderPars")
            if dicRenderPars is None:
                xItem.sRenderPars = ""
            else:
                xItem.sRenderPars = json.dumps(dicRenderPars, indent=2)
            # endif

            UpdateItemToolTip(xItem)
        # endif
    # endfor


# enddef


#######################################################################################
def _TransformObjectsWorldMatrix(*, xObjects, matX):
    global c_sWorldMatrixName

    for objX in xObjects:
        if (
            objX.parent is None
            and all((x.type != "FOLLOW_PATH" for x in objX.constraints))
            and objX.get("AnyVehicle") is None
        ):
            objX[c_sWorldMatrixName] = [[col for col in row] for row in objX.matrix_world]
            objX.matrix_world = matX @ objX.matrix_world
        # endif
    # endfor objects


# enddef


#######################################################################################
def _RestoreObjectsWorldMatrix(*, xObjects):
    global c_sWorldMatrixName

    for objX in xObjects:
        lMatOrig = objX.get(c_sWorldMatrixName)
        if lMatOrig is not None:
            objX.matrix_world = mathutils.Matrix(lMatOrig)
            del objX[c_sWorldMatrixName]
        # endif
    # endfor objects


# enddef


#######################################################################################
def _SetRotationShader(*, ngMain, sLabel, tAngles):
    iRotNodeCnt = 0

    ndRot = next((x for x in ngMain if x.label == sLabel), None)
    if ndRot is not None:
        ndRot.rotation_type = "EULER_XYZ"
        ndRot.inputs["Rotation"].default_value = tAngles
        iRotNodeCnt += 1
    # endif

    for ndX in ngMain:
        if ndX.type == "GROUP":
            iRotNodeCnt += _SetRotationShader(ngMain=ndX.node_tree.nodes, sLabel=sLabel, tAngles=tAngles)
        # endif
    # endfor

    return iRotNodeCnt


# enddef


#######################################################################################
def _SetWorldShaderRotation(*, xContext, tAngles):
    sRotNodeLabel = "AnyCam.World.Rotate"
    ngWorld = xContext.scene.world.node_tree.nodes

    iRotNodeCnt = _SetRotationShader(ngMain=ngWorld, sLabel=sRotNodeLabel, tAngles=tAngles)
    if iRotNodeCnt == 0:
        print(
            "WARNING: World shader has no rotation node with label 'AnyCam.World.Rotate'. "
            "World background may not be rotated correctly."
        )
    # endif


# enddef


#######################################################################################
def TransformSceneToCameraFrame(*, xContext: bpy.context):
    global c_sOriginName
    # Try to revert any previous transformation before applying a new one
    RevertTransformSceneToCameraFrame(xContext=xContext, bDoThrow=False)

    objCam = xContext.scene.camera
    matCam = objCam.matrix_world
    objCam[c_sOriginName] = [[col for col in row] for row in matCam]
    # print("Active Camera: {}".format(objCam.name))

    matCamInv = matCam.inverted()

    _TransformObjectsWorldMatrix(xObjects=xContext.scene.objects, matX=matCamInv)

    eulX = objCam.matrix_world.to_euler()
    tAngles = (eulX.x, eulX.y, eulX.z)
    _SetWorldShaderRotation(xContext=xContext, tAngles=tAngles)

    # Set frame again, so that frame handler are executed again.
    # This updates the position of any vehicles with an AnyVehicle animation.
    iFrameCur = xContext.scene.frame_current
    xContext.scene.frame_set(iFrameCur + 1)
    xContext.scene.frame_set(iFrameCur)

    layer: bpy.types.ViewLayer
    for layer in xContext.scene.view_layers:
        layer.update()
    # endfor

    return True


# enddef


#######################################################################################
def GetTransformCameraFrame() -> list:
    global c_sOriginName
    # assume that there is at most one camera object with
    # the original world coordinate system as a property.
    # This may not be the currently active camera.
    lMatOrig: list = None
    for objX in bpy.data.objects:
        if objX.type == "CAMERA":
            lMatOrig = objX.get(c_sOriginName)
            if lMatOrig is not None:
                # lMatOrig = list(lMatOrig)
                lMatOrig = [[col for col in row] for row in lMatOrig]
                break
            # endif
        # endif
    # endfor

    return lMatOrig


# endif


#######################################################################################
def RevertTransformSceneToCameraFrame(*, xContext: bpy.context, bDoThrow: bool=True):
    global c_sOriginName
    # assume that there is at most one camera object with
    # the original world coordinate system as a property.
    # This may not be the currently active camera.
    objCam = None
    lMatOrig = None
    for objX in bpy.data.objects:
        if objX.type == "CAMERA":
            lMatOrig = objX.get(c_sOriginName)
            if lMatOrig is not None:
                objCam = objX
                break
            # endif
        # endif
    # endfor

    if objCam is None:
        if bDoThrow is True:
            raise RuntimeError("Original origin not stored in active camera")
        else:
            return False
        # endif
    # endif

    # matOrig = mathutils.Matrix(lMatOrig)
    # _TransformObjectsWorldMatrix(xObjects=xContext.view_layer.objects, matX=matOrig)

    _RestoreObjectsWorldMatrix(xObjects=xContext.scene.objects)
    _SetWorldShaderRotation(xContext=xContext, tAngles=(0, 0, 0))

    del objCam[c_sOriginName]

    # Set frame again, so that frame handler are executed again.
    # This updates the position of any vehicles with an AnyVehicle animation.
    iFrameCur = xContext.scene.frame_current
    xContext.scene.frame_set(iFrameCur + 1)
    xContext.scene.frame_set(iFrameCur)

    layer: bpy.types.ViewLayer
    for layer in xContext.scene.view_layers:
        layer.update()
    # endfor

    return True


# enddef
