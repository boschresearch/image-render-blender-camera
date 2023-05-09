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
import re
import math
from . import ops
from . import ac_func_camset
from . import ops_camset
import anyblend


###################################################################################
def UpdateFrustum(xCamLoc):

    _UpdateFrustumColor(xCamLoc, bpy.context)
    _UpdateFrustumViewScale(xCamLoc)
    _Show(xCamLoc, bpy.context)


# enddef


###################################################################################
def _UpdateFrustumColor(self, context):

    tColor = (self.colCamera.r, self.colCamera.g, self.colCamera.b, 1.0)
    ops_camset.SetFrustumMaterialColor(self.sCamSetId, self.sAnyCamLabel, self.objLocation, tColor)


# enddef


###################################################################################
def _ShowCamFrust(self, context):

    bHide = not (self.bShowCameraFrustum and self.bCanShowCameraFrustum and self.bCanShow)

    ops_camset.SetFrustumHideStateForCamera(
        self.sCamSetId,
        self.sAnyCamLabel,
        self.objLocation,
        "S",
        _bHideView=bHide,
        _bHideRender=bHide,
    )


# enddef

###################################################################################
def _ShowIntersection(self, context):

    bHide = not (self.bShowIntersection and self.bCanShowIntersection and self.bHasIntersection and self.bCanShow)

    ops_camset.SetFrustumHideStateForCamera(
        self.sCamSetId,
        self.sAnyCamLabel,
        self.objLocation,
        "L",
        _bHideView=bHide,
        _bHideRender=bHide,
    )


# enddef

###################################################################################
def _Show(self, context):

    _ShowCamFrust(self, context)
    _ShowIntersection(self, context)


# enddef

###################################################################################
def _CathPath_Get(self):
    return self.loc_sCathPath


# enddef

###################################################################################
def _CathPath_Set(self, _sValue):

    sValue = _sValue
    if len(self.sCathPath) >= 0:

        xAcCamSetList = bpy.context.scene.AcPropsCamSets
        if xAcCamSetList is None:
            raise Exception("Camera Data not available")
        # endif

        if xAcCamSetList.bValidSelection:
            xCamSet = xAcCamSetList.Selected
            lCathPaths = xCamSet.GetCathPaths()
            iIdx = 1
            while sValue in lCathPaths:
                sValue = "{0}/{1:03d}".format(_sValue, iIdx)
                iIdx += 1
            # endwhile
        # endif
    # endif

    self.loc_sCathPath = sValue


# enddef

###################################################################################
def _UpdateFrustumViewScale(self):
    fScale = math.pow(10.0, self.loc_fFrustumViewScale + self.loc_fFrustDeltaViewScale)
    lFrustum, lMatch = ops_camset.FindCameraFrustums(self.sCamSetId, self.sAnyCamLabel, self.objLocation.children)
    for iIdx, objF in enumerate(lFrustum):
        sType = lMatch[iIdx].group("type")
        if sType == "S":
            objF.scale = (fScale, fScale, fScale)
        # endif
    # endfor


# enddef

###################################################################################
def _GetFrustumViewScale(self):
    return self.loc_fFrustumViewScale


# enddef

###################################################################################
def _SetFrustumViewScale(self, _fValue):
    self.loc_fFrustumViewScale = _fValue
    _UpdateFrustumViewScale(self)


# enddef

###################################################################################
def _GetFrustDeltaViewScale(self):
    return self.loc_fFrustDeltaViewScale


# enddef

###################################################################################
def _SetFrustDeltaViewScale(self, _fValue):
    self.loc_fFrustDeltaViewScale = _fValue
    _UpdateFrustumViewScale(self)


# enddef

###################################################################################
def _GetFrustumIntersectScale(self):
    return self.loc_fFrustumIntersectScale


# enddef

###################################################################################
def _SetFrustumIntersectScale(self, _fValue):

    for objX in bpy.context.selected_objects:
        objX.select_set(state=False)
    # endfor
    fCurScale = math.pow(10.0, self.loc_fFrustumIntersectScale)
    fNewScale = math.pow(10.0, _fValue)
    fScale = fNewScale / fCurScale

    lFrustum, lMatch = ops_camset.FindCameraFrustums(self.sCamSetId, self.sAnyCamLabel, self.objLocation.children)
    for iIdx, objF in enumerate(lFrustum):
        sType = lMatch[iIdx].group("type")
        if sType == "L":
            objF.scale = (fScale, fScale, fScale)

            objF.select_set(state=True)
            bpy.context.view_layer.objects.active = objF
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            bpy.context.view_layer.objects.active = None
            objF.select_set(state=False)
        # endif

    # endfor

    self.loc_fFrustumIntersectScale = _fValue


# enddef

###################################################################################
class CPgAcCamLoc(bpy.types.PropertyGroup):

    sId: bpy.props.StringProperty(default="")
    sCamSetId: bpy.props.StringProperty(default="")
    sAnyCamLabel: bpy.props.StringProperty(default="")
    sToolTip: bpy.props.StringProperty(default="")
    sMaterialType: bpy.props.StringProperty(default="plastic")

    # The catharsys configuration path
    loc_sCathPath: bpy.props.StringProperty(default="")
    sCathPath: bpy.props.StringProperty(
        default="",
        get=_CathPath_Get,
        set=_CathPath_Set,
        name="Catharsys Path",
        description="The configuration path used in the Catharsys system",
    )

    objCamera: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Camera",
        description="The camera type at the location.",
    )

    objLocation: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Location",
        description="The location origin for the camera.",
    )

    colCamera: bpy.props.FloatVectorProperty(default=(0.8, 0.8, 0.8), subtype="COLOR", update=_UpdateFrustumColor)

    bShowCameraFrustum: bpy.props.BoolProperty(name="Show Frustum", default=False, update=_ShowCamFrust)

    bCanShowCameraFrustum: bpy.props.BoolProperty(name="Can Show Frustum", default=True, update=_ShowCamFrust)

    bShowIntersection: bpy.props.BoolProperty(name="Show Intersection", default=False, update=_ShowIntersection)

    bCanShowIntersection: bpy.props.BoolProperty(name="Can Show Intersection", default=True, update=_ShowIntersection)

    bHasIntersection: bpy.props.BoolProperty(name="Has Intersection", default=False, update=_ShowIntersection)

    bCanShow: bpy.props.BoolProperty(name="Can Show", default=True, update=_Show)

    loc_fFrustumViewScale: bpy.props.FloatProperty()
    fFrustumViewScale: bpy.props.FloatProperty(
        name="View Frustum Scale Power",
        default=0.0,
        min=-2.0,
        max=2.0,
        get=_GetFrustumViewScale,
        set=_SetFrustumViewScale,
    )

    loc_fFrustDeltaViewScale: bpy.props.FloatProperty()
    fFrustDeltaViewScale: bpy.props.FloatProperty(
        name="View Frustum Delta Scale Power",
        default=0.0,
        min=-2.0,
        max=2.0,
        get=_GetFrustDeltaViewScale,
        set=_SetFrustDeltaViewScale,
    )

    loc_fFrustumIntersectScale: bpy.props.FloatProperty()
    fFrustumIntersectScale: bpy.props.FloatProperty(
        name="Intersect Frustum Scale Power",
        default=0.0,
        min=-2.0,
        max=2.0,
        get=_GetFrustumIntersectScale,
        set=_SetFrustumIntersectScale,
    )

    def UpdateFrustumScale(self):
        _SetFrustumViewScale(self, self.loc_fFrustumViewScale)

    # enddef


# endclass

###################################################################################
# Register


def register():
    bpy.utils.register_class(CPgAcCamLoc)


# enddef


def unregister():
    bpy.utils.unregister_class(CPgAcCamLoc)


# enddef
