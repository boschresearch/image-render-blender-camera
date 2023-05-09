#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ops_asset_placement_ac.py
# Created Date: Monday, September 19th 2022, 3:00:20 pm
# Created by: Jochen Kall
# <LICENSE id="All-Rights-Reserved">
# Copyright (c) 2022 Robert Bosch GmbH and its subsidiaries
# </LICENSE>
###

# Provides Operators to generate Geometricplacement maps and Camera visibility maps within Blender
# for Anycam GUI integration.

import bpy
import anycam

# from anyblend.asset_placement import GeneratePlacementMap, GenerateVisibilityMap
# from anyblend.asset_placement import GeneratePlacementMap, GenerateVisibilityMap

# from . import asset_placement as ap

# GeneratePlacementMap = ap.GeneratePlacementMap
# GenerateVisibilityMap = ap.GenerateVisibilityMap


class OperatorCameraVisibilityMap(bpy.types.Operator):
    """Generates the Camera Visibility map of the currently selected Anycam Camera/Location pair
    for all Asset Planes currently selected by the user.
    Asset Radius, Camera FoV and Obstacle Collection are queried from the user
    """

    bl_idname = "object.generate_cam_visibility_map"
    bl_label = "Generate Camera visibility map"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Import within execute necessary, since anyblend is not yet availlable within Blender
        # during import time
        from anyblend.asset_placement import GenerateVisibilityMap

        # currently selected camera location index of selected camset
        fR = context.window_manager.AssetPlacementProps.fR
        clnObstacles = context.window_manager.AssetPlacementProps.clnWalls
        iSelected = context.scene.AcPropsCamSets.Selected.iSelIdx
        xCamera = context.scene.AcPropsCamSets.Selected.clCameras[iSelected]
        # iterate all currently selected persons.planes
        for objPlane in context.selected_objects:
            self.report(
                {"INFO"},
                f"Generating Visibily map for Plane: {objPlane.name} and Camera {xCamera.sId}",
            )
            self.report(
                {"INFO"},
                f"using FoV: {fR} and Radius {fR}",
            )
            # Obtaining FoV information
            xCameraView = anycam.ops.GetAnyCamView(context, xCamera.objCamera.name)
            if xCameraView is None:
                self.report(
                    {"INFO"},
                    "Camera View could not be generated, using default FoV 180 degrees",
                )
                fFovHorizontal = 180
                fFovVertical = 180
            else:
                fFovHorizontal = xCameraView.lFov_deg[0]
                fFovVertical = xCameraView.lFov_deg[1]
            # Endif

            GenerateVisibilityMap(
                objPlane,
                xCamera.objLocation,
                clnObstacles,
                fR=fR,
                fFovHorizontal=fFovHorizontal,
                fFovVertical=fFovVertical,
                sVertexGroupName=f"AnyCam.{xCamera.sCathPath}",
            )
        # endfor

        # Add a merged visibility map, if a geometric placement mask already exists
        from anyblend.asset_placement import MultiplyVertexGroups

        if "AnyCam.geometric_placement_mask" in objPlane.vertex_groups.keys():
            MultiplyVertexGroups(
                objPlane,
                "AnyCam.geometric_placement_mask",
                f"AnyCam.{xCamera.sCathPath}",
                f"AnyCam.{xCamera.sCathPath}_merged",
            )
        # Endif
        return {"FINISHED"}

    # Enddef


# endclass


class OperatorPlacementMap(bpy.types.Operator):
    """Generates Geometric Placement maps for all Asset Planes currently selected by the user.
    Asset Radius, Asset Height and Name of the vertex group to be generated are queried from the user
    """

    bl_idname = "object.generate_geometric_placement_map"
    bl_label = "Generate Geometric Placement Map"
    # bl_options = {"REGISTER", "UNDO"}
    bl_options = {"REGISTER"}

    # fH: bpy.props.FloatProperty(name="Asset Height", default=1.8, min=0, max=10000)
    # fR: bpy.props.FloatProperty(name="Asset Radius", default=0.4, min=0, max=10000)
    # sVertexGroupName: bpy.props.StringProperty(
    #    name="Vertex Group Name", default="Anycam.geometric_placement_mask"
    # )

    def execute(self, context):
        # Import within execute necessary, since anyblend is not yet availlable within Blender
        # during import time
        from anyblend.asset_placement import GeneratePlacementMap

        fH = context.window_manager.AssetPlacementProps.fH
        fR = context.window_manager.AssetPlacementProps.fR
        sVertexGroupName = context.window_manager.AssetPlacementProps.sVertexGroupNameGeometricPlacement

        for obj in bpy.context.selected_objects:
            self.report({"INFO"}, f"Generating Geometric Placement map for: {obj.name}")

            GeneratePlacementMap(obj, fR=fR, fH=fH, sVertexGroupName=sVertexGroupName)
        # Endfor
        return {"FINISHED"}

    # Enddef


# Endclass
def register():
    bpy.utils.register_class(OperatorPlacementMap)
    bpy.utils.register_class(OperatorCameraVisibilityMap)


# Enddef
def unregister():
    bpy.utils.unregister_class(OperatorPlacementMap)
    bpy.utils.unregister_class(OperatorCameraVisibilityMap)


# Enddef
if __name__ == "__main__":
    register()
# Endif
