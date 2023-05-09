#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ac_props_camset.py
# Created Date: Friday, April 30th 2021, 7:48:29 am
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
import os
from . import ops
from . import ac_func_camset
from . import ops_camset
from .ac_props_camloc import CPgAcCamLoc
from . import ac_props_camloc
import anyblend

###################################################################################
def _PollMeshObject(this, objX):
    return objX.type == "MESH"


# enddef

########################################################
def _UpdateIntersectObject(self, context):

    for xCamera in self.clCameras:
        ops_camset.SetFrustumIntersectionObjectForCamera(
            context,
            sCamSetId=self.sId,
            sCamId=xCamera.sAnyCamLabel,
            objParent=xCamera.objLocation,
            objIntersect=self.objIntersect,
        )

        xCamera.bHasIntersection = self.objIntersect is not None
    # endfor


# enddef

########################################################
def _Show(self, context):

    for xCamera in self.clCameras:
        xCamera.bCanShow = self.bShow
    # endfor


# enddef

########################################################
def _ShowFrustum(self, context):

    for xCamera in self.clCameras:
        xCamera.bCanShowCameraFrustum = self.bShowFrustum
    # endfor


# enddef

########################################################
def _ShowIntersection(self, context):

    for xCamera in self.clCameras:
        xCamera.bCanShowIntersection = self.bShowIntersection
    # endfor


# enddef

########################################################
def _GetId(self):
    return self.loc_sId


# enddef


def _SetId(self, _sValue):
    xAcCamSetList = bpy.context.scene.AcPropsCamSets

    if xAcCamSetList is not None:
        if _sValue != self.loc_sId:
            sValue = _sValue.replace(" ", ".").replace(":", "-")
            lCamSetIds = xAcCamSetList.GetIdList()
            sValue = ops.ProvideUniqueId(
                sValue, lCamSetIds, sDefaultBaseName="CameraSet"
            )

            # Rename all frustums of component cameras
            for xCamLoc in self.clCameras:
                lFrustum, lMatch = ops_camset.FindCameraFrustums(
                    self.loc_sId, xCamLoc.sAnyCamLabel, xCamLoc.objLocation.children
                )
                for objF in lFrustum:
                    lName = objF.name.split(":")
                    objF.name = "{0}:{1}".format(sValue, lName[1])
                # endfor
                xCamLoc.sCamSetId = sValue
            # endfor
            self.loc_sId = sValue
        # endif
    else:
        self.loc_sId = _sValue
    # endif


# enddef

#######################################################################################
def _SelCamSetEl(self, context):
    xAcProps = context.window_manager.AcProps
    xAcCamSetList = context.scene.AcPropsCamSets
    if xAcCamSetList is None:
        raise Exception("Camera Data not available")
    # endif

    if xAcCamSetList.bValidSelection:
        xAcCamSet = xAcCamSetList.Selected
        if xAcCamSet.bValidSelection:
            xAcCamera = xAcCamSet.Selected

            xAcProps.SelectCameraObject(xAcCamera.sAnyCamLabel)
            context.view_layer.objects.active = xAcCamera.objLocation
            anyblend.object.ParentObject(
                xAcCamera.objLocation, xAcCamera.objCamera, bKeepTransform=False
            )
        # endif
    # endif


# enddef

#######################################################################################
def _ExportFileExists(self):
    sPath = self.GetExportFilePath()
    return os.path.exists(sPath)


# enddef

###################################################################################
def _GetFrustumViewScale(self):
    return self.loc_fFrustumViewScale


# enddef

###################################################################################
def _SetFrustumViewScale(self, _fValue):

    for xCamLoc in self.clCameras:
        xCamLoc.fFrustumViewScale = _fValue
    # endfor

    self.loc_fFrustumViewScale = _fValue


# enddef

###################################################################################
def _GetFrustumIntersectScale(self):
    return self.loc_fFrustumIntersectScale


# enddef

###################################################################################
def _SetFrustumIntersectScale(self, _fValue):

    for xCamLoc in self.clCameras:
        xCamLoc.fFrustumIntersectScale = _fValue
    # endfor

    self.loc_fFrustumIntersectScale = _fValue


# enddef

###################################################################################
class CPgAcCamSet(bpy.types.PropertyGroup):

    loc_sId: bpy.props.StringProperty(default="")

    sId: bpy.props.StringProperty(default="", get=_GetId, set=_SetId)
    sLabel: bpy.props.StringProperty(default="")
    sToolTip: bpy.props.StringProperty(default="")

    bExportFileExists: bpy.props.BoolProperty(
        name="Export File Exists", default=False, get=_ExportFileExists
    )

    bExportOverwrite: bpy.props.BoolProperty(name="Export Overwrite", default=False)

    sPathExport: bpy.props.StringProperty(
        name="Export Path", description="Export path", subtype="DIR_PATH", default="//"
    )

    clCameras: bpy.props.CollectionProperty(type=CPgAcCamLoc)
    iSelIdx: bpy.props.IntProperty(default=0, update=_SelCamSetEl)

    objIntersect: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Frustum Intersection",
        description="The frustum intersection object.",
        poll=_PollMeshObject,
        update=_UpdateIntersectObject,
    )

    bShow: bpy.props.BoolProperty(name="Show", default=True, update=_Show)

    bShowFrustum: bpy.props.BoolProperty(
        name="Show Frustum", default=True, update=_ShowFrustum
    )

    bShowIntersection: bpy.props.BoolProperty(
        name="Show Intersection", default=True, update=_ShowIntersection
    )

    bCompactView: bpy.props.BoolProperty(name="Compact View", default=True)

    loc_fFrustumViewScale: bpy.props.FloatProperty()
    fFrustumViewScale: bpy.props.FloatProperty(
        name="View Frustum Scale Power",
        default=1.0,
        min=-2.0,
        max=2.0,
        get=_GetFrustumViewScale,
        set=_SetFrustumViewScale,
    )

    loc_fFrustumIntersectScale: bpy.props.FloatProperty()
    fFrustumIntersectScale: bpy.props.FloatProperty(
        name="Intersect Frustum Scale Power",
        default=1.0,
        min=-2.0,
        max=2.0,
        get=_GetFrustumIntersectScale,
        set=_SetFrustumIntersectScale,
    )

    def clear(self):
        self.clCameras.clear()
        self.sId = ""
        self.sLabel = ""
        self.iSelIdx = 0

    # enddef

    def GetIdList(self):
        return [x.sId for x in self.clCameras]

    # enddef

    def GetLocationNames(self):
        return [x.objLocation.name for x in self.clCameras]

    # enddef

    def GetCameraNames(self):
        return [x.objCamera.name for x in self.clCameras]

    # enddef

    def GetCathPaths(self):
        return [x.sCathPath for x in self.clCameras]

    # enddef

    def GetExportFilePath(self):
        sFilename = self.sId.replace(".", "_")
        return os.path.normpath(
            os.path.join(bpy.path.abspath(self.sPathExport), sFilename + ".json")
        )

    # enddef

    def CreateId(self, *, objCamera, objLocation):
        return "{0};{1}".format(objCamera.name, objLocation.name)

    # enddef

    def HasId(self, _sId):
        return _sId in self.GetIdList()

    # enddef

    def Add(self, *, objCamera, objLocation, sAnyCamLabel):

        sId = self.CreateId(objCamera=objCamera, objLocation=objLocation)
        if self.HasId(sId):
            xCamera = None
        else:
            xCamera = self.clCameras.add()
            xCamera.sAnyCamLabel = sAnyCamLabel
            xCamera.objCamera = objCamera
            xCamera.objLocation = objLocation
            xCamera.sId = sId
            xCamera.sCamSetId = self.sId
        # endif
        return xCamera

    # enddef

    def Remove(self, *, objCamera, objLocation):
        sId = self.CreateId(objCamera=objCamera, objLocation=objLocation)
        lIdList = self.GetIdList()
        if sId not in lIdList:
            return
        # endif
        iIdx = lIdList.index(sId)
        self.clCameras.remove(iIdx)

    # enddef

    @property
    def iCount(self):
        return len(self.clCameras)

    # enddef

    @property
    def bValidSelection(self):
        return self.iSelIdx >= 0 and self.iSelIdx < self.iCount

    # enddef

    @property
    def Selected(self):
        if self.bValidSelection:
            return self.clCameras[self.iSelIdx]
        else:
            return None
        # endif

    # enddef


# endclass

###################################################################################
# Register


def register():
    ac_props_camloc.register()
    bpy.utils.register_class(CPgAcCamSet)


# enddef


def unregister():
    bpy.utils.unregister_class(CPgAcCamSet)
    ac_props_camloc.unregister()


# enddef
