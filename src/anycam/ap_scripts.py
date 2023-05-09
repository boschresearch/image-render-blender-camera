#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ap_scripts.py
# Created Date: Thursday, September 29th 2022, 2:56:35 pm
# Created by: Jochen Kall
# <LICENSE id="All-Rights-Reserved">
# Copyright (c) 2022 Robert Bosch GmbH and its subsidiaries
# </LICENSE>
###

from anyblend.asset_placement import GenerateVisibilityMaps
import bpy

# includes for intellisense purpose only:
from anycam import ac_props_camloc, ac_props_camsetcol


def GenerateAnyCamVisibilityMaps(
    clnAssetPlanes,
    clnObstacles,
    pgCamera: ac_props_camloc.CPgAcCamLoc,
    fR: float = 0.4,
    fFovVertical=180.0,
    fFovHorizontal=180.0,
):
    """Generates Visibility maps for passed Asset Planes, obstacles and anycam Camera Location object

    Parameters
    ----------
    clnAssetPlanes : _type_
        Collection of Blender Grid objects
    clnObstacles : _type_
        Collection of Obstacles/Walls
    pgCamera : anycam.ac_props_camloc.CPgAcCamLoc
        Anycam Object containing combination of Camera and Location to be considered
    fR : float, optional
        fR (float, optional): Radius of the asset to be placed. Defaults to 0.4.
    fFov : int, optional
        Field of View of the camera. Defaults to 180
    """
    sVertexGroupName = f"AnyCam.{pgCamera.loc_sCathPath}"
    objCamLocation = pgCamera.objLocation
    GenerateVisibilityMaps(
        clnAssetPlanes, objCamLocation, clnObstacles, fR, sVertexGroupName, fFovVertical, fFovHorizontal
    )


def GenerateAnycamVisibilityMapsComplete(clnAssetPlanes, clnObstacles, fR=0.4, fFov=180):
    """Generates visibility maps for all camera x Location pairs of all
    Anycam Camsets for all Assetplanes passed w.r.t to the obstacles passed

    Parameters
    ----------
    clnAssetPlanes : _type_
        Collection of Blender Grid objects
    clnObstacles : _type_
        Collection of Obstacles/Walls
    fR : float, optional
        fR (float, optional): Radius of the asset to be placed. Defaults to 0.4.
    fFov : int, optional
        Field of View of the camera. Defaults to 180
    """
    AcPropsCamSets: ac_props_camsetcol.CPgAcCamSetCollection = bpy.context.scene.AcPropsCamSets
    # iterate over all camsets
    lCamsetNames = AcPropsCamSets.GetIdList()
    for i in range(AcPropsCamSets.iCount):
        # Select Cameraset of index i
        AcPropsCamSets.iSelIdx = i
        print(f"""Handling {lCamsetNames[i]}""")
        # iterate camera locations
        pgCamera: ac_props_camloc.CPgAcCamLoc
        for pgCamera in bpy.context.scene.AcPropsCamSets.Selected.clCameras:
            # Generate Visibility maps for the camera x location combination
            GenerateAnyCamVisibilityMaps(clnAssetPlanes, clnObstacles, pgCamera, fR, fFov)
        # Endfor
    # Endfor
