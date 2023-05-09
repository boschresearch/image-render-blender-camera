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
from typing import Optional
import re
from . import ops
from anybase.cls_anyexcept import CAnyExcept
import anyblend
from .material.cls_plastic import CPlastic


g_reFrustumCopy = re.compile(
    r"(?P<camset>[^:]+):Frustum\.(?P<camtype>[^\.]+)\.(?P<type>[LS])\.(?P<name>.+)\.(?P<copy>\d{3})$"
)
g_reFrustum = re.compile(r"(?P<camset>[^:]+):Frustum\.(?P<camtype>[^\.]+)\.(?P<type>[LS])\.(?P<name>.+)")
g_reCamera = re.compile(r"Cam\.(?P<camtype>[^\.]+)\.(?P<camname>.+)")
g_reCameraEx = re.compile(r"Cam\.(?P<camtype>[^\.]+)\.(?P<username>[^\.]+)\.(?P<dbname>.+)")


#######################################################################################
def AddCameraFrustumToObject(_xContext, _sCamSetId, _sCamId, _objParent):

    dicCam = ops.GetAnyCam(_xContext, _sCamId)
    objCam = dicCam.get("objCam")

    if _objParent is None:
        return
    # endif

    clAct = anyblend.collection.FindCollectionOfObject(_xContext, _objParent)

    lCamId = _sCamId.split(".")
    sFrustPattern = "Frustum.{0}".format(lCamId[1])

    lFrustObj = [x for x in objCam.children if x.name.startswith(sFrustPattern)]
    lChildNames = [x.name for x in _objParent.children]

    for objF in lFrustObj:
        sNewFrustName = "{0}:{1}".format(_sCamSetId, objF.name)

        if not any(x.startswith(sNewFrustName) for x in lChildNames):
            objFC = objF.copy()
            objFC.data = objF.data.copy()
            objFC.name = sNewFrustName
            clAct.objects.link(objFC)
            anyblend.object.ParentObject(_objParent, objFC, bKeepTransform=False)
        # endif
    # endfor


# enddef


#######################################################################################
def SetFrustumMaterialType(_sCamSetId, _sCamId, _objParent, *, sMaterialId, sMaterialType):

    if sMaterialType == "plastic":
        xMat = CPlastic(sName=sMaterialId, bForce=True)
    else:
        raise CAnyExcept("Material type '{0}' not supported".format(sMaterialType))
    # endif

    lFrustum, lMatch = FindCameraFrustums(_sCamSetId, _sCamId, _objParent.children)

    for objF in lFrustum:
        objF.active_material = xMat.xMaterial
    # endfor


# enddef


#######################################################################################
def SetFrustumMaterialColor(_sCamSetId, _sCamId, _objParent, _tColor):

    lFrustum, lMatch = FindCameraFrustums(_sCamSetId, _sCamId, _objParent.children)

    for objF in lFrustum:
        matF = objF.active_material
        if matF is None:
            raise Exception("Frustum of camera '{0}' for parent '{1}' has no material".format(_sCamId, _objParent.name))
        # endif
        bFound = False
        for xNode in matF.node_tree.nodes:
            if xNode.type == "GROUP" and xNode.node_tree.name.startswith("AnyCam.Input."):
                xColor = xNode.inputs.get("Color")
                if xColor is not None:
                    xColor.default_value = _tColor
                    bFound = True
                    break
                # endif
            # endif
        # endfor

        if not bFound:
            raise Exception(
                "Frustum of camera '{0}' for parent '{1}' has no 'AnyCam.Input' node group with a 'Color' input".format(
                    _sCamId, _objParent.name
                )
            )
        # endif
    # endfor


# enddef


#######################################################################################
def FindCameraFrustums(_sCamSetId, _sCamId, _lObjects):

    global g_reFrustum
    global g_reFrustumCopy
    global g_reCamera

    xMatchCam = g_reCamera.match(_sCamId)
    if xMatchCam is None:
        raise Exception("Camera '{0}' not a valid anycam camera name".format(_sCamId))
    # endif

    lFrustum = []
    lMatch = []
    for objX in _lObjects:
        xMatchFrust = g_reFrustumCopy.match(objX.name)
        if xMatchFrust is None:
            xMatchFrust = g_reFrustum.match(objX.name)
            if xMatchFrust is None:
                continue
            # endif
        # endif

        sCamType = xMatchCam.group("camtype")
        sCamName = xMatchCam.group("camname")

        sFrustCamSet = xMatchFrust.group("camset")
        sFrustCamType = xMatchFrust.group("camtype")
        sFrustName = xMatchFrust.group("name")

        if sFrustCamSet == _sCamSetId and sCamType == sFrustCamType and sCamName == sFrustName:
            lFrustum.append(objX)
            lMatch.append(xMatchFrust)
        # endif
    # endfor

    return lFrustum, lMatch


# enddef

#######################################################################################
def FindAllCameraFrustums(_lObjects):

    global g_reFrustum
    global g_reFrustumCopy
    global g_reCamera

    lFrustum = []
    lMatch = []
    for objX in _lObjects:
        xMatchFrust = g_reFrustumCopy.match(objX.name)
        if xMatchFrust is None:
            xMatchFrust = g_reFrustum.match(objX.name)
            if xMatchFrust is None:
                continue
            # endif
        # endif

        lFrustum.append(objX)
        lMatch.append(xMatchFrust)
    # endfor

    return lFrustum, lMatch


# enddef


#######################################################################################
def RemoveCameraFrustumFromObject(_sCamSetId, _sCamId, _objParent):

    if _objParent is None:
        return
    # endif

    lFrustum, lMatch = FindCameraFrustums(_sCamSetId, _sCamId, _objParent.children)

    for xF in lFrustum:
        bpy.data.objects.remove(xF)
    # endfor


# enddef


#######################################################################################
def SetFrustumHideStateForCamera(_sCamSetId, _sCamId, _objParent, _sType, _bHideView, _bHideRender):

    if _objParent is None:
        return
    # endif

    lFrustum, lMatch = FindCameraFrustums(_sCamSetId, _sCamId, _objParent.children)

    for iIdx, xF in enumerate(lFrustum):
        xMatch = lMatch[iIdx]
        if xMatch.group("type") in _sType:
            anyblend.object.Hide(xF, bHide=_bHideView, bHideRender=_bHideRender, bHideInAllViewports=_bHideView)
        # endif
    # endfor


# enddef


#######################################################################################
def SetFrustumIntersectionObjectForCamera(_xContext, *, sCamSetId, sCamId, objParent, objIntersect):

    bValidIntersect = True
    if objIntersect is None or objIntersect.type != "MESH":
        bValidIntersect = False
    # endif

    lFrustum, lMatch = FindCameraFrustums(sCamSetId, sCamId, objParent.children)

    for iIdx, objF in enumerate(lFrustum):
        xMatch = lMatch[iIdx]
        if xMatch.group("type") != "L":
            continue
        # endif

        clX = anyblend.collection.FindCollectionOfObject(_xContext, objF)
        if clX.name == "AnyCam":
            continue
        # endif

        lmodF = objF.modifiers
        lmodF.clear()

        if bValidIntersect:
            modBool = lmodF.new("Intersect", "BOOLEAN")
            modBool.operation = "INTERSECT"
            modBool.object = objIntersect

            modWire = lmodF.new("Wire", "WIREFRAME")
            modWire.thickness = 0.1
        # endif
    # endfor

    if bValidIntersect:
        objIntersect.hide_set(True)
        objIntersect.hide_render = True
    # endif

    return True


# enddef


###################################################################################
def CopyCamSet(_xContext, xCamSet):

    xAcCamSetList = _xContext.scene.AcPropsCamSets
    xNewCamSet = xAcCamSetList.Add(sId=xCamSet.sId)

    for xCamLoc in xCamSet.clCameras:

        AddCamLoc(
            _xContext,
            xCamSet=xNewCamSet,
            objCam=xCamLoc.objCamera,
            objLoc=xCamLoc.objLocation,
            sAnyCamLabel=xCamLoc.sAnyCamLabel,
        )

    # endfor

    return xNewCamSet


# enddef


###################################################################################
def AddCamLoc(_xContext, *, xCamSet, objCam, objLoc, sAnyCamLabel):

    if objCam is None:
        raise Exception("Invalid camera object")
    # endif

    if objLoc is None:
        raise Exception("Invalid location object")
    # endif

    sCamSetElId = xCamSet.CreateId(objCamera=objCam, objLocation=objLoc)

    xCamera = xCamSet.Add(objCamera=objCam, objLocation=objLoc, sAnyCamLabel=sAnyCamLabel)
    if xCamera is None:
        raise Exception("Error creating camera / location pair")
    # endif
    anyblend.object.ParentObject(objLoc, objCam, bKeepTransform=False)

    AddCameraFrustumToObject(_xContext, xCamSet.sId, sAnyCamLabel, objLoc)
    SetFrustumMaterialType(
        xCamSet.sId,
        sAnyCamLabel,
        objLoc,
        sMaterialId=sCamSetElId,
        sMaterialType=xCamera.sMaterialType,
    )

    xCamera.bShowCameraFrustum = True

    bHasIntersection = xCamSet.objIntersect is not None
    xCamera.bShowIntersection = bHasIntersection
    xCamera.bHasIntersection = bHasIntersection
    if bHasIntersection:
        SetFrustumIntersectionObjectForCamera(
            _xContext,
            sCamSetId=xCamSet.sId,
            sCamId=sAnyCamLabel,
            objParent=objLoc,
            objIntersect=xCamSet.objIntersect,
        )
    # endif

    xCamera.fFrustumViewScale = xCamSet.fFrustumViewScale
    xCamera.fFrustumIntersectScale = xCamSet.fFrustumIntersectScale

    return xCamera


# endif


###################################################################################
def AutoGenCathPaths(_xContext):

    xAcCamSetList = _xContext.scene.AcPropsCamSets

    global g_reCameraEx

    if xAcCamSetList.bValidSelection:
        xCamSet = xAcCamSetList.Selected
        lLocNames = xCamSet.GetLocationNames()
        # Find longest common part at beginning of string
        # Only tests blocks separated by a dot
        lLocParts = lLocNames[0].split(".")
        iIdx = 0
        bEnd = False
        sCommon = ""
        for iIdx in range(len(lLocParts)):
            sCommon = ".".join(lLocParts[0 : iIdx + 1])
            for sName in lLocNames:
                if not sName.startswith(sCommon):
                    sCommon = ".".join(lLocParts[0:iIdx])
                    bEnd = True
                    break
                # endif
            # endfor
            if bEnd:
                break
            # endif
        # endfor

        # Test whether the common part is the full name of one location
        if sCommon in lLocNames:
            # if this is the case, the allow one name part to be common
            sCommon = sCommon.strip(".")
            lCommon = sCommon.split(".")
            sCommon = ".".join(lCommon[0:-1])
        # endif
        iCommonCnt = len(sCommon)

        lLocPaths = []
        for sLocName in lLocNames:
            sName = sLocName[iCommonCnt:]
            lName = [x for x in sName.split(".") if len(x) > 0]
            lLocPaths.append("/".join(lName))
        # endfor

        lCamParts = []
        lCamNames = xCamSet.GetCameraNames()
        for sCamName in lCamNames:
            xMatchCam = g_reCameraEx.match(sCamName)
            if xMatchCam is None:
                lCamParts.append([sCamName])
            else:
                lCamParts.append(
                    [
                        xMatchCam.group("camtype"),
                        xMatchCam.group("username"),
                        xMatchCam.group("dbname"),
                    ]
                )
            # endif
        # endfor

        bCommonCamName = True
        sCamName = lCamParts[0][1]
        for lParts in lCamParts:
            if len(lParts) < 2 or sCamName != lParts[1]:
                bCommonCamName = False
                break
            # endif
        # endfor

        # Clear all Catharsys paths, so that generation of unique names works
        for xCamLoc in xCamSet.clCameras:
            xCamLoc.sCathPath = ""
        # endfor

        for iIdx, xCamLoc in enumerate(xCamSet.clCameras):
            if bCommonCamName:
                sCamPath = "{0}/{1}".format(lCamParts[iIdx][0], "/".join(lCamParts[iIdx][2:]))
            else:
                sCamPath = "/".join(lCamParts[iIdx])
            # endif
            xCamLoc.sCathPath = "{0}/{1}".format(lLocPaths[iIdx], sCamPath)
        # endfor

    # endif


# enddef


###################################################################################
def CheckConsistency(_xScene):

    xAcCamSetList = _xScene.AcPropsCamSets

    for xCamSet in xAcCamSetList.clCamSets:
        lRemoveCamLoc = []

        for xCamLoc in xCamSet.clCameras:
            objLoc = xCamLoc.objLocation
            objCam = xCamLoc.objCamera

            if len(xCamLoc.sId) == 0:
                continue
            # endif

            # Check if location or camera object exists in scene
            bHasLocation = objLoc is not None and _xScene.objects.get(objLoc.name) is not None
            bHasCamera = objCam is not None and _xScene.objects.get(objCam.name) is not None
            if not bHasCamera or not bHasLocation:
                lRemoveCamLoc.append(xCamLoc)
                continue
            # endif

            # Check for renaming of parent
            sActId = xCamSet.CreateId(objCamera=xCamLoc.objCamera, objLocation=xCamLoc.objLocation)
            if sActId != xCamLoc.sId:
                SetFrustumMaterialType(
                    xCamSet,
                    xCamLoc.sAnyCamLabel,
                    xCamLoc.objLocation,
                    sMaterialId=sActId,
                    sMaterialType=xCamLoc.sMaterialType,
                )
                xCamLoc.sId = sActId
            # endif

        # endfor

        lCamLocNames = [x.sId.split(";")[1] for x in xCamSet.clCameras]
        lCamLocIds = xCamSet.GetIdList()
        for xCamLoc in lRemoveCamLoc:
            lFrustum, lMatch = FindCameraFrustums(xCamSet, xCamLoc.sAnyCamLabel, _xScene.objects)
            for objF in lFrustum:
                if not objF.parent or objF.parent.name not in lCamLocNames:
                    bpy.data.objects.remove(objF)
                # endif
            # endfor
            xCamSet.clCameras.remove(lCamLocIds.index(xCamLoc.sId))
        # endfor
    # endfor


# enddef
