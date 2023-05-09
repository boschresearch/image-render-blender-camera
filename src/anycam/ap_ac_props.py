#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ap_ac_props.py
# Created Date: Monday, September 19th 2022, 4:56:19 pm
# Created by: Jochen Kall
# <LICENSE id="All-Rights-Reserved">
# Copyright (c) 2022 Robert Bosch GmbH and its subsidiaries
# </LICENSE>
###

# Provides the Property group for geometric asset placement and visibility map generation within AnyCam

import bpy


# Asset placement Property group
class CPgAssetPlacement(bpy.types.PropertyGroup):
    """Class to register properties to window, not saved with settings or file"""

    # Shared Property
    fR: bpy.props.FloatProperty(name="AssetRadius", default=0.4, min=0.1, max=1000)  # noqa
    # Properties for Geometric Placement map generation
    fH: bpy.props.FloatProperty(name="AssetHeight", default=1.8, min=0.1, max=1000)  # noqa
    sVertexGroupNameGeometricPlacement: bpy.props.StringProperty(
        name="VertexGroup",  # noqa
        description="Name of the Vertex group to be generated.",
        default="AnyCam.geometric_placement_mask",  # noqa
    )

    # Properties for Camera Visibility map generation
    # Obstacle Collection / Walls
    clnWalls: bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Walls",
        description="Collection containing visibility blocking geometry",
    )


def register():
    bpy.utils.register_class(CPgAssetPlacement)

    bpy.types.WindowManager.AssetPlacementProps = bpy.props.PointerProperty(type=CPgAssetPlacement)


##############################################################################
# Unregister


def unregister():
    bpy.utils.unregister_class(CPgAssetPlacement)

    del bpy.types.WindowManager.AssetPlacementProps
