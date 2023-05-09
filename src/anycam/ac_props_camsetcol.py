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
from bpy.app.handlers import persistent
from pathlib import Path

import os
from . import ops

from . import ops_camset
from .ac_props_camset import CPgAcCamSet
from . import ac_props_camset


###################################################################################
def _ImportFileExists(self):
    xPath = Path(self.GetImportFilePath())
    if len(xPath.suffix) == 0:
        sFp = xPath.as_posix() + ".json"
    else:
        sFp = xPath.as_posix()
    # endif
    return os.path.exists(sFp)


# enddef


###################################################################################
class CPgAcCamSetCollection(bpy.types.PropertyGroup):

    clCamSets: bpy.props.CollectionProperty(type=CPgAcCamSet)
    iSelIdx: bpy.props.IntProperty(default=0)

    bImportFileExists: bpy.props.BoolProperty(name="Import File Exists", default=False, get=_ImportFileExists)

    sFilePathImport: bpy.props.StringProperty(
        name="Import File",
        description="Path to camera set JSON configuration file",
        subtype="FILE_PATH",
        default="//",
    )

    def clear(self):
        self.clCamSets.clear()
        self.iSelIdx = 0

    # enddef

    def GetIdList(self):
        return [x.sId for x in self.clCamSets]

    # enddef

    def Get(self, _sId: str) -> CPgAcCamSet:
        lCamSetIds = self.GetIdList()
        if _sId in lCamSetIds:
            return self.clCamSets[lCamSetIds.index(_sId)]
        # endif
        return None

    # enddef

    def Add(self, sId=None):

        lCamSetIds = self.GetIdList()
        sCamSetId = ops.ProvideUniqueId(sId, lCamSetIds, sDefaultBaseName="CameraSet")
        xCamSet = self.clCamSets.add()
        xCamSet.clear()
        xCamSet.name = sCamSetId
        xCamSet.sId = sCamSetId
        return xCamSet

    # enddef

    def Remove(self, xCamSet):
        lCamSetIds = self.GetIdList()
        if xCamSet.sId in lCamSetIds:
            self.clCamSets.remove(lCamSetIds.index(xCamSet.sId))
        # endif

    # enddef

    def GetImportFilePath(self):
        return os.path.normpath(bpy.path.abspath(self.sFilePathImport))

    # enddef

    @property
    def iCount(self):
        return len(self.clCamSets)

    # enddef

    @property
    def bValidSelection(self):
        return self.iSelIdx >= 0 and self.iSelIdx < self.iCount

    # enddef

    @property
    def Selected(self) -> CPgAcCamSet:
        if not self.bValidSelection:
            return None
        # endif
        return self.clCamSets[self.iSelIdx]

    # enddef


# endclass


@persistent
def AnyCam_SceneUpdatePre(_xScene):
    ops_camset.CheckConsistency(_xScene)


# enddef

###################################################################################
# Register


def register():

    ac_props_camset.register()
    bpy.utils.register_class(CPgAcCamSetCollection)

    bpy.types.Scene.AcPropsCamSets = bpy.props.PointerProperty(type=CPgAcCamSetCollection)

    # add handler if not in app.handlers
    if AnyCam_SceneUpdatePre not in bpy.app.handlers.depsgraph_update_pre:
        bpy.app.handlers.depsgraph_update_pre.append(AnyCam_SceneUpdatePre)


# enddef


def unregister():
    # remove handler if not in app.handlers
    if AnyCam_SceneUpdatePre in bpy.app.handlers.depsgraph_update_pre:
        bpy.app.handlers.depsgraph_update_pre.remove(AnyCam_SceneUpdatePre)

    bpy.utils.unregister_class(CPgAcCamSetCollection)
    ac_props_camset.unregister()


# enddef
