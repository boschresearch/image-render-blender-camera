#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /ac_ops.py
# Created Date: Thursday, October 22nd 2020, 2:51:40 pm
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

#######################################################################
# LFT Plugin Operators

import bpy
from . import ac_global
from . import ac_func


#######################################################################
# Update all Frustums
class COpUpdateAllFrustums(bpy.types.Operator):
    bl_idname = "ac.update_all_frustums"
    bl_label = "Update All Frustums"
    bl_description = "Click to update all frustums."

    def execute(self, context):
        ac_func.UpdateAllFrustums()
        return {"FINISHED"}

    # enddef

    def invoke(self, context, event):
        return self.execute(context)

    # enddef


# endclass

#######################################################################
# Refresh Camera Db List from Path
class COpUpdateCameraDb(bpy.types.Operator):
    bl_idname = "ac.update_camera_db"
    bl_label = "Update Camera Data Path"
    bl_description = "Click to update camera data from given path."

    def execute(self, context):
        # self.report({"INFO"}, "Hello World")

        ac_func.PathCamDbUpdate(self, context)
        ac_func.CamObjUpdate(self, context)
        return {"FINISHED"}

    # enddef


# endclass

#######################################################################
# Refresh Camera Object List from Path


class COpUpdateCameraObjList(bpy.types.Operator):
    bl_idname = "ac.update_camera_obj_list"
    bl_label = "Update Camera Object List"
    bl_description = "Click to update camera object list."

    def execute(self, context):
        ac_func.CamObjUpdate(self, context)
        return {"FINISHED"}

    # enddef


# endclass

#######################################################################
# Create selected Camera


class COpCreateSelectedCamera(bpy.types.Operator):
    bl_idname = "ac.create_selected_camera"
    bl_label = "Create Camera"
    bl_description = "Click to create the currently selected camera."

    def execute(self, context):
        ac_func.CreateSelectedCamera(self, context)
        ac_func.CamObjUpdate(self, context)
        return {"FINISHED"}

    # enddef


# endclass

#######################################################################
# Activate selected Camera


class COpActivateSelectedCamera(bpy.types.Operator):
    bl_idname = "ac.activate_selected_camera"
    bl_label = "Activate Camera"
    bl_description = "Click to activate the currently selected camera."

    def execute(self, context):
        ac_func.ActivateSelectedCamera(self, context)
        return {"FINISHED"}

    # enddef


# endclass

#######################################################################
# Remove selected Camera


class COpRemoveSelectedCamera(bpy.types.Operator):
    bl_idname = "ac.remove_selected_camera"
    bl_label = "Remove Camera"
    bl_description = "Click to remove the currently selected camera."

    def execute(self, context):
        ac_func.RemoveSelectedCamera(self, context)
        ac_func.CamObjUpdate(self, context)
        return {"FINISHED"}

    # enddef

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    # enddef


# endclass

#######################################################################
# Select selected Camera


class COpSelectSelectedCamera(bpy.types.Operator):
    bl_idname = "ac.select_selected_camera"
    bl_label = "Select Camera"
    bl_description = "Click to select the currently selected camera in 3D view."

    def execute(self, context):
        ac_func.SelectCamera(self, context)
        return {"FINISHED"}

    # enddef


# endclass

#######################################################################
# Assign render parameters to camera


class COpAssignRenderParsToSelectedCamera(bpy.types.Operator):
    bl_idname = "ac.assign_render_pars_to_selected_camera"
    bl_label = "Assign render pars"
    bl_description = "Click to assign the current render paramters to the selected camera."

    def execute(self, context):
        ac_func.AssignRenderParsToSelectedCamera(self, context)
        ac_func.CamObjUpdate(self, context)
        return {"FINISHED"}

    # enddef


# endclass

#######################################################################
# Apply render parameters from camera


class COpApplyRenderParsFromSelectedCamera(bpy.types.Operator):
    bl_idname = "ac.apply_render_pars_from_selected_camera"
    bl_label = "Apply render pars from camera"
    bl_description = "Click to apply the stored render paramters from the selected camera."

    def execute(self, context):
        ac_func.ApplyRenderParsFromSelectedCamera(self, context)
        return {"FINISHED"}

    # enddef


# endclass


#######################################################################
# Transform World To Camera Frame
class COpTransformSceneToCameraFrame(bpy.types.Operator):
    bl_idname = "ac.transform_scene_to_camera_frame"
    bl_label = "Transform scene to camera frame"
    bl_description = "Click to transform the whole scene to the frame of the currently active camera."

    bRevert: bpy.props.BoolProperty(name="revert", default=False)

    def execute(self, context):
        ac_func.TransformSceneToCameraFrame(self, context, self.bRevert)
        return {"FINISHED"}

    # enddef


# endclass


#######################################################################################
# Register


def register():

    bpy.utils.register_class(COpUpdateCameraDb)
    bpy.utils.register_class(COpUpdateAllFrustums)
    bpy.utils.register_class(COpUpdateCameraObjList)
    bpy.utils.register_class(COpCreateSelectedCamera)
    bpy.utils.register_class(COpActivateSelectedCamera)
    bpy.utils.register_class(COpRemoveSelectedCamera)
    bpy.utils.register_class(COpAssignRenderParsToSelectedCamera)
    bpy.utils.register_class(COpApplyRenderParsFromSelectedCamera)
    bpy.utils.register_class(COpSelectSelectedCamera)
    bpy.utils.register_class(COpTransformSceneToCameraFrame)


# enddef


def unregister():

    bpy.utils.unregister_class(COpSelectSelectedCamera)
    bpy.utils.unregister_class(COpApplyRenderParsFromSelectedCamera)
    bpy.utils.unregister_class(COpAssignRenderParsToSelectedCamera)
    bpy.utils.unregister_class(COpActivateSelectedCamera)
    bpy.utils.unregister_class(COpRemoveSelectedCamera)
    bpy.utils.unregister_class(COpCreateSelectedCamera)
    bpy.utils.unregister_class(COpUpdateCameraObjList)
    bpy.utils.unregister_class(COpUpdateCameraDb)
    bpy.utils.unregister_class(COpTransformSceneToCameraFrame)
    bpy.utils.unregister_class(COpUpdateAllFrustums)


# enddef
