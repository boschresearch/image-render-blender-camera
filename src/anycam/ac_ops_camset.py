#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ac_ops_camset.py
# Created Date: Friday, April 30th 2021, 8:36:19 am
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
from . import ac_func_camset

#######################################################################
# Create a camera set


class COpAcCameraSetCreate(bpy.types.Operator):
    bl_idname = "ac.camset_create"
    bl_label = "Create Camera Set"
    bl_description = "Click to create a camera set."

    def execute(self, context):
        ac_func_camset.AddCamSet(self, context)
        return {"FINISHED"}

    # enddef


# endclass

#######################################################################
# Copy a camera set


class COpAcCameraSetCopy(bpy.types.Operator):
    bl_idname = "ac.camset_copy"
    bl_label = "Copy Camera Set"
    bl_description = "Click to copy a camera set."

    def execute(self, context):
        ac_func_camset.CopyCamSet(self, context)
        return {"FINISHED"}

    # enddef


# endclass

#######################################################################
# Auto generate Catharsys Paths for camera/locations


class COpAcCameraSetAutoGenCathPath(bpy.types.Operator):
    bl_idname = "ac.camset_auto_gen_cathpath"
    bl_label = "Auto generate catharsys paths"
    bl_description = "Click to auto generate catharsys paths."

    def execute(self, context):
        ac_func_camset.CamSetAutoGenCathPaths(self, context)
        return {"FINISHED"}

    # enddef

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    # enddef


# endclass

#######################################################################
# Check Consistency


class COpAcCameraSetCheckConsistency(bpy.types.Operator):
    bl_idname = "ac.camset_check_consistency"
    bl_label = "Check Consisteny of Camera Set"
    bl_description = "Click to check the consistency of the camera set."

    def execute(self, context):
        ac_func_camset.CheckConsistency(self, context)
        return {"FINISHED"}

    # enddef


# endclass

#######################################################################
# Refresh Camera Db List from Path


class COpAcCameraSetElementCreate(bpy.types.Operator):
    bl_idname = "ac.create_camset_element"
    bl_label = "Create Camera Set Element"
    bl_description = "Click to create a camera type/location pair."

    def execute(self, context):
        ac_func_camset.AddCamLoc(self, context)
        return {"FINISHED"}

    # enddef


# endclass

#######################################################################
# Refresh Camera Db List from Path


class COpAcCameraSetElementRemove(bpy.types.Operator):
    bl_idname = "ac.remove_camset_element"
    bl_label = "Remove Camera Set Element"
    bl_description = "Click to remove a camera type/location pair."

    def execute(self, context):
        ac_func_camset.RemoveSelectedCamLoc(self, context)
        return {"FINISHED"}

    # enddef

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    # enddef


# endclass

#######################################################################
# Remove Camera Set
class COpRemoveSelectedCameraSet(bpy.types.Operator):
    bl_idname = "ac.camset_remove_selected"
    bl_label = "Remove Camera Set"
    bl_description = "Click to remove the currently selected camera set."

    def execute(self, context):
        ac_func_camset.RemoveSelectedCameraSet(self, context)
        return {"FINISHED"}

    # enddef

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    # enddef


# endclass

#######################################################################
# Export camera set


class COpAcCameraSetExport(bpy.types.Operator):
    bl_idname = "ac.camset_export"
    bl_label = "Export"
    bl_description = "Click to export the camera set to JSON. This does not export the camera location in 3D space, but only the reference to the location object."

    def execute(self, context):
        ac_func_camset.CamSetExport(self, context)
        return {"FINISHED"}

    # enddef


# endclass

#######################################################################
# Export camera set


class COpAcCameraSetImport(bpy.types.Operator):
    bl_idname = "ac.camset_import"
    bl_label = "Import"
    bl_description = "Click to import the camera set from JSON. This does not import the camera location in 3D space, but only the reference to the location object."

    def execute(self, context):
        ac_func_camset.CamSetImport(self, context)
        return {"FINISHED"}

    # enddef


# endclass

#######################################################################################
# Register


def register():
    bpy.utils.register_class(COpAcCameraSetCreate)
    bpy.utils.register_class(COpAcCameraSetCopy)
    bpy.utils.register_class(COpAcCameraSetElementCreate)
    bpy.utils.register_class(COpAcCameraSetElementRemove)

    bpy.utils.register_class(COpRemoveSelectedCameraSet)
    bpy.utils.register_class(COpAcCameraSetCheckConsistency)
    bpy.utils.register_class(COpAcCameraSetAutoGenCathPath)
    bpy.utils.register_class(COpAcCameraSetExport)
    bpy.utils.register_class(COpAcCameraSetImport)


# enddef


def unregister():

    bpy.utils.unregister_class(COpAcCameraSetCreate)
    bpy.utils.unregister_class(COpAcCameraSetCopy)
    bpy.utils.unregister_class(COpAcCameraSetElementCreate)
    bpy.utils.unregister_class(COpAcCameraSetElementRemove)

    bpy.utils.unregister_class(COpRemoveSelectedCameraSet)
    bpy.utils.unregister_class(COpAcCameraSetCheckConsistency)
    bpy.utils.unregister_class(COpAcCameraSetAutoGenCathPath)
    bpy.utils.unregister_class(COpAcCameraSetExport)
    bpy.utils.unregister_class(COpAcCameraSetImport)


# enddef
