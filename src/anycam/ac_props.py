#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /ac_props.py
# Created Date: Thursday, October 22nd 2020, 2:51:42 pm
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
from . import ac_global
from . import ac_func
from . import ops
from . import node

#######################################################################################
# Camera Info Collection Item


class CPgAcCamDbItem(bpy.types.PropertyGroup):

    sId: bpy.props.StringProperty(default="")
    sLabel: bpy.props.StringProperty(default="")
    sType: bpy.props.StringProperty(default="")
    sSubType: bpy.props.StringProperty(default="")
    sToolTip: bpy.props.StringProperty(default="")


# endclass

#######################################################################################
# AnyCam Cameras Collection Item


class CPgAcCamListItem(bpy.types.PropertyGroup):

    sLabel: bpy.props.StringProperty(default="")
    sName: bpy.props.StringProperty(default="")
    sDesign: bpy.props.StringProperty(default="")
    sType: bpy.props.StringProperty(default="")
    sSubType: bpy.props.StringProperty(default="")
    sTypeName: bpy.props.StringProperty(default="")
    iResX: bpy.props.IntProperty(default=0)
    iResY: bpy.props.IntProperty(default=0)
    bHasRenderPars: bpy.props.BoolProperty(default=False)
    sToolTip: bpy.props.StringProperty(default="")
    sRenderPars: bpy.props.StringProperty(default="")


# endclass

##########################################################################
def GetLftWavelength(self):
    return int(node.grp.render_pars.GetWavelength())


# enddef

##########################################################################
def SetLftWavelength(self, _iWavelength):
    node.grp.render_pars.SetWavelength(_iWavelength)


# enddef

##########################################################################
def _GetSelCamObjItem():
    xAcProps = bpy.context.window_manager.AcProps
    iSelCamIdx = xAcProps.iCamObjSelIdx
    return xAcProps.clCamObj[iSelCamIdx]


# enddef

##########################################################################
def GetCamResX(self):
    return _GetSelCamObjItem().iResX


# enddef

##########################################################################
def SetCamResX(self, _iValue):
    xItem = _GetSelCamObjItem()
    xItem.iResX = _iValue
    ops.UpdateItemToolTip(xItem)
    ops.SetAnyCamSenResX(bpy.context, xItem.sLabel, _iValue)


# enddef

##########################################################################
def GetCamResY(self):
    return _GetSelCamObjItem().iResY


# enddef

##########################################################################
def SetCamResY(self, _iValue):
    xItem = _GetSelCamObjItem()
    xItem.iResY = _iValue
    ops.UpdateItemToolTip(xItem)
    ops.SetAnyCamSenResY(bpy.context, xItem.sLabel, _iValue)


# enddef

#######################################################################################
def Update_TransformSceneToCameraFrame(self, context):

    bRevert = not self.bTransformSceneToCameraFrame
    bpy.ops.ac.transform_scene_to_camera_frame(bRevert=bRevert)


# enddef


#######################################################################################
def Update_PathCamDbUpdate(self, context):
    bpy.ops.ac.update_camera_db()


# enddef


#######################################################################################
# LFT property classes


class CPgAcPropsWnd(bpy.types.PropertyGroup):
    """Class to register properties to window, not saved with settings or file"""

    # String Property for LFT camera data path
    sPathCamData: bpy.props.StringProperty(
        name="Data Path",
        description="Folder that contains AnyCam data packages.",
        subtype="DIR_PATH",
        update=Update_PathCamDbUpdate,
        # update = ac_func.PathCamDbUpdate,
        default="//",
    )

    # Camera UIList Collection
    clCamDb: bpy.props.CollectionProperty(type=CPgAcCamDbItem)

    # Camera UIList Active Item
    iCamDbSelIdx: bpy.props.IntProperty(default=0)

    # Available AnyCam Cameras UIList Collection
    clCamObj: bpy.props.CollectionProperty(type=CPgAcCamListItem)
    iCamObjSelIdx: bpy.props.IntProperty(default=0, update=ac_func.SelectCamera)

    iCamResX: bpy.props.IntProperty(default=0, get=GetCamResX, set=SetCamResX)
    iCamResY: bpy.props.IntProperty(default=0, get=GetCamResY, set=SetCamResY)
    bShowRenderPars: bpy.props.BoolProperty(default=False)

    bAutoUpdateCamObjList: bpy.props.BoolProperty(default=False)
    bOverwriteCamera: bpy.props.BoolProperty(default=False)
    fCameraScale: bpy.props.FloatProperty(name="Scale", default=1.0, min=0.1, max=10000)

    sCamName: bpy.props.StringProperty(default="Std")

    bApplyRenderParsOnActivation: bpy.props.BoolProperty(default=True)
    bTransformSceneToCameraFrame: bpy.props.BoolProperty(default=False, update=Update_TransformSceneToCameraFrame)

    iLftRenderWavelength: bpy.props.IntProperty(
        default=520,
        get=GetLftWavelength,
        set=SetLftWavelength,
        min=300,
        max=1100,
        soft_min=380,
        soft_max=750,
        description="The wavelength used to calculate the refractive index of LFT lenses.",
    )

    ##########################################################################
    def clear(self):
        self.clCamDb.clear()
        self.iCamDbSelIdx = 0

        self.clCamObj.clear()
        self.iCamObjSelIdx = 0

        self.bAutoUpdateCamObjList = False
        self.bApplyRenderParsOnActivation = True
        self.bOverwriteCamera = False

        self.iLftRenderWavelength = 520

    # enddef

    @property
    def iCameraCount(self):
        return len(self.clCamObj)

    # enddef

    @property
    def bValidCamSel(self):
        return self.iCamObjSelIdx >= 0 and self.iCamObjSelIdx < self.iCameraCount

    # enddef

    @property
    def SelectedCamera(self):
        if not self.bValidCamSel:
            return None
        # endif
        return self.clCamObj[self.iCamObjSelIdx]

    # enddef

    def SelectCameraObject(self, _sLabel):

        for iIdx in range(self.iCameraCount):
            if self.clCamObj[iIdx].sLabel == _sLabel:
                self.iCamObjSelIdx = iIdx
                break
            # endif
        # endfor

    # enddef


# endclass

#######################################################################################
# Register


def register():
    bpy.utils.register_class(CPgAcCamDbItem)
    bpy.utils.register_class(CPgAcCamListItem)
    bpy.utils.register_class(CPgAcPropsWnd)

    bpy.types.WindowManager.AcProps = bpy.props.PointerProperty(type=CPgAcPropsWnd)


# enddef


def unregister():
    # Clear all window properties, to start fresh, when registering again.
    bpy.context.window_manager.AcProps.clear()

    del bpy.types.WindowManager.AcProps

    bpy.utils.unregister_class(CPgAcPropsWnd)
    bpy.utils.unregister_class(CPgAcCamDbItem)
    bpy.utils.unregister_class(CPgAcCamListItem)


# enddef
