#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ac_func_camset.py
# Created Date: Friday, April 30th 2021, 8:38:36 am
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
from . import ops
from . import ops_camset
from . import ops_camset_file
import anyblend

#######################################################################################
def AddCamSet(self, context):

    try:
        xAcCamSetList = context.scene.AcPropsCamSets
        if xAcCamSetList is None:
            return
        # endif

        xAcCamSetList.Add()
    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endif


# enddef

#######################################################################################
def CopyCamSet(self, context):

    try:
        xAcCamSetList = context.scene.AcPropsCamSets
        if xAcCamSetList is None or not xAcCamSetList.bValidSelection:
            return
        # endif

        xCamSet = xAcCamSetList.Selected
        ops_camset.CopyCamSet(context, xCamSet)

    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endif


# enddef

#######################################################################################
def GetSelectedCameraLocation(self, context):

    try:
        xAcProps = context.window_manager.AcProps
        xAcCamSetList = context.scene.AcPropsCamSets
        if xAcCamSetList is None or xAcProps is None:
            raise Exception("Camera Data not available")
        # endif

        xAcCamSet = xAcCamSetList.Selected
        if xAcCamSet is None:
            raise Exception("No camera set selected")
        # endif

        objAct = context.active_object
        if objAct is None:
            raise Exception("No location object selected")
        # endif

        xCam = xAcProps.SelectedCamera
        if xCam is None:
            raise Exception("No camera selected")
        # endif

        sAnyCamLabel = xCam.sLabel
        dicCam = ops.GetAnyCam(context, xCam.sLabel)
        dicAnyCam = dicCam.get("dicAnyCam")
        if dicAnyCam is None:
            objCam = dicCam.get("objCam")
        else:
            sOrigin = dicAnyCam.get("sOrigin")
            if sOrigin is None:
                objCam = dicCam.get("objCam")
            else:
                objCam = context.scene.objects.get(sOrigin)
            # endif
        # endif

        if objCam is None:
            raise Exception("Camera selection invalid")
        # endif

    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
        objCam = None
        objAct = None
        sAnyCamLabel = None
    # endif

    return {"objCam": objCam, "objLoc": objAct, "sAnyCamLabel": sAnyCamLabel}


# endif

#######################################################################################
def AddCamLoc(self, context):

    try:
        xAcCamSetList = context.scene.AcPropsCamSets
        if xAcCamSetList is None:
            raise Exception("Camera Data not available")
        # endif

        xAcCamSet = xAcCamSetList.Selected
        if xAcCamSet is None:
            raise Exception("No camera set selected")
        # endif

        dicSel = GetSelectedCameraLocation(self, context)
        objCam = dicSel.get("objCam")
        objLoc = dicSel.get("objLoc")
        sAnyCamLabel = dicSel.get("sAnyCamLabel")
        if objCam is None:
            raise Exception("No valid camera / location pair selected")
        # endif

        ops_camset.AddCamLoc(
            context,
            xCamSet=xAcCamSet,
            objCam=objCam,
            objLoc=objLoc,
            sAnyCamLabel=sAnyCamLabel,
        )

    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endif


# enddef

#######################################################################################
def RemoveSelectedCamLoc(self, context):

    try:
        xAcCamSetList = context.scene.AcPropsCamSets
        if xAcCamSetList.bValidSelection:
            xAcCamSet = xAcCamSetList.Selected
            if xAcCamSet.bValidSelection:
                xAcCamLoc = xAcCamSet.Selected
                objCam = xAcCamLoc.objCamera
                objLoc = xAcCamLoc.objLocation
                sAnyCamLabel = xAcCamLoc.sAnyCamLabel
                xAcCamSet.Remove(objCamera=objCam, objLocation=objLoc)

                if objCam.parent == objLoc:
                    objCam.parent = None
                # endif

                ops_camset.RemoveCameraFrustumFromObject(
                    xAcCamSet.sId, sAnyCamLabel, objLoc
                )
            # endif
        # endif
        xAcCamSet.iSelIdx = 0
    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endif


# enddef

#######################################################################################
def RemoveAllCamLocs(self, context):

    try:
        xAcCamSetList = context.scene.AcPropsCamSets
        if xAcCamSetList.bValidSelection:

            xAcCamSet = xAcCamSetList.Selected
            for xCamLoc in xAcCamSet.clCameras:
                objCam = xCamLoc.objCamera
                objLoc = xCamLoc.objLocation
                sAnyCamLabel = xCamLoc.sAnyCamLabel

                if objCam.parent == objLoc:
                    objCam.parent = None
                # endif

                ops_camset.RemoveCameraFrustumFromObject(
                    xAcCamSet.sId, sAnyCamLabel, objLoc
                )
            # endfor
            xAcCamSet.clCameras.clear()
        # endif

        xAcCamSet.iSelIdx = 0
    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endif


# enddef

#######################################################################################
def RemoveSelectedCameraSet(self, context):

    try:
        xAcCamSetList = context.scene.AcPropsCamSets
        if xAcCamSetList.bValidSelection:
            xAcCamSet = xAcCamSetList.Selected

            RemoveAllCamLocs(self, context)
            xAcCamSetList.Remove(xAcCamSet)
        # endif
        xAcCamSetList.iSelIdx = 0
    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endif


# enddef

#######################################################################################
# Auto Generate Catharsys Paths
def CamSetAutoGenCathPaths(self, context):

    try:
        ops_camset.AutoGenCathPaths(context)
    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endtry


# enddef

#######################################################################################
# Export Camera Set
def CamSetExport(self, context):

    try:
        bResult, sMsg = ops_camset_file.Export(context)
        if bResult:
            self.report({"INFO"}, "Camera set exported to: {0}".format(sMsg))
        else:
            self.report({"WARNING"}, sMsg)
        # endif
    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endtry


# enddef

#######################################################################################
# Export Camera Set
def CamSetImport(self, context):

    try:
        bResult, sMsg = ops_camset_file.Import(context)
        if bResult:
            self.report({"INFO"}, "Camera set imported from: {0}".format(sMsg))
        else:
            self.report({"WARNING"}, sMsg)
        # endif
    except Exception as xEx:
        self.report({"ERROR"}, str(xEx))
    # endtry


# enddef
