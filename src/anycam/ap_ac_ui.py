#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ap_ac_ui.py
# Created Date: Monday, September 19th 2022, 4:55:59 pm
# Created by: Jochen Kall
# <LICENSE id="All-Rights-Reserved">
# Copyright (c) 2022 Robert Bosch GmbH and its subsidiaries
# </LICENSE>
###

# Provides Anycam GUI integration for Assetplacement map generation

import bpy


class AC_PT_VisibilityMaps(bpy.types.Panel):
    """Creates a Panel in the Object properties window of Anycam"""

    bl_label = "Asset Placement"
    bl_idname = "AC_PT_VisibilityMaps"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AnyCam"

    def draw(self, context):
        xCPAssetPlacement = context.window_manager.AssetPlacementProps
        layout = self.layout

        yRow = layout.row()
        yRow.prop(xCPAssetPlacement, "fR", text="Asset Radius [m]")
        yRow = layout.row()
        yRow.prop(xCPAssetPlacement, "clnWalls", text="Obstacle Collection")
        # Displaying selected Camera/Location pair
        yRow = layout.row()
        yRow.label(text="Selected camera/location:")
        yRow = layout.box()
        if context.scene.AcPropsCamSets.Selected is not None and context.scene.AcPropsCamSets.Selected.bValidSelection:
            iSelected = context.scene.AcPropsCamSets.Selected.iSelIdx
            xCamera = context.scene.AcPropsCamSets.Selected.clCameras[iSelected]
            yRow.label(text=xCamera.sId)
        else:
            yRow.label(text="No Camera/Location pair selected")
        # Displaying Selected Assetplanes
        yRow = layout.row()
        yRow.label(text="Selected Assetplanes:")
        yRow = layout.box()
        if len(context.selected_objects) == 0:
            yRow.label(text="No Asset Plane selected")
        for objPlane in context.selected_objects:
            yRow.label(text=objPlane.name)
        yRow = layout.row()
        yRow.operator(
            "object.generate_cam_visibility_map",
            text="Calculate Camera Visibility Map",
            # emboss=True,
        )
        # No camset selected
        if not context.scene.AcPropsCamSets.bValidSelection:
            yRow.enabled = False
        # No camera x Position pair selected
        elif not context.scene.AcPropsCamSets.Selected.bValidSelection:
            yRow.enabled = False
        # no Wall Collection selected
        if context.window_manager.AssetPlacementProps.clnWalls is None:
            yRow.enabled = False


class AC_PT_GeometricPlacementMaps(bpy.types.Panel):
    """Creates a Panel in the Object properties window for Geometric placement maps"""

    bl_label = "Asset Placement"
    bl_idname = "AC_PT_AssetPlacementGeometric"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Asset Placement"

    def draw(self, context):
        # xAcProps = context.window_manager.AcProps
        xCPAssetPlacement = context.window_manager.AssetPlacementProps
        layout = self.layout

        yRow = layout.row()
        yRow.prop(xCPAssetPlacement, "fR", text="Asset Radius [m]")
        yRow = layout.row()
        yRow.prop(xCPAssetPlacement, "fH", text="Asset Height [m]")
        yRow = layout.row()
        yRow.prop(xCPAssetPlacement, "sVertexGroupNameGeometricPlacement", text="Vertexgroup")
        # Displaying selected Assetplanes
        yRow = layout.row()
        yRow.label(text="Selected Assetplanes:")
        yRow = layout.box()
        if len(context.selected_objects) == 0:
            yRow.label(text="No Asset Plane selected")
        for objPlane in context.selected_objects:
            yRow.label(text=objPlane.name)
        yRow = layout.row()
        yRow.operator(
            "object.generate_geometric_placement_map",
            text="Calculate Geometric Placement Map",
            # emboss=True,
        )


def register():
    bpy.utils.register_class(AC_PT_VisibilityMaps)
    bpy.utils.register_class(AC_PT_GeometricPlacementMaps)


##############################################################################
# Unregister


def unregister():
    bpy.utils.unregister_class(AC_PT_VisibilityMaps)
    bpy.utils.unregister_class(AC_PT_GeometricPlacementMaps)


if __name__ == "main":
    register()
