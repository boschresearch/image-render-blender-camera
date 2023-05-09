#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /camera_lft.py
# Created Date: Thursday, October 22nd 2020, 2:51:35 pm
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
import bmesh
import math
import pyjson5 as json

from . import util
from . import optics
from .. import ops
from .. import node
from .. import material
import anyblend

#####################################################################
# Create the camera name
def CreateName(_sName):
    return "Cam.Lft.{0}".format(_sName)


# enddef

#####################################################################
# Create Light Field Trace Cameras


def Create(_sName, _dicCamera, bOverwrite=False, bForce=False, fScale=1.0, dicAnyCamEx=None):

    #### DEBUG ########
    # bOverwrite = True
    # bForce = True
    ###################

    # Calculate Blender Units per Millimeter
    fBUperMM = fScale * 1e-3 / bpy.context.scene.unit_settings.scale_length

    #####################################################
    # Get camera data
    dicSensor = _dicCamera["dicSensor"]
    dicLensSystem = _dicCamera["dicLensSys"]
    dicMediaCatalog = _dicCamera["dicMedia"]
    dicLftPars = _dicCamera["dicLftPars"]

    #####################################################
    # Create camera empty, that acts as origin for whole camera system
    sCamName = CreateName(_sName)

    cnMain = bpy.data.collections.get("AnyCam")
    if cnMain is None:
        cnMain = bpy.data.collections.new("AnyCam")
        bpy.context.scene.collection.children.link(cnMain)
    # endif

    objCamOrig = bpy.data.objects.get(sCamName)
    if objCamOrig is not None:
        if bOverwrite == True:
            ops.DeleteObjectHierarchy(objCamOrig)
            objCamOrig = None
        else:
            return {
                "bResult": False,
                "objCam": objCamOrig,
                "sMsg": "Camera with selected name already exists.",
            }
        # endif
    # endif

    #####################################################
    # Create Parameter node groups
    node.grp.render_pars.Create(bForce=bForce, fScale=fScale)

    node.grp.objective_pars.Create(dicLensSystem, bForce=bForce)
    node.grp.sensor_pars.Create(dicSensor, bForce=bForce)

    # Create node groups for media refraction for all given media
    node.grp.media.Update(dicMediaCatalog)

    #####################################################

    objCamOrig = bpy.data.objects.new(sCamName, None)
    objCamOrig.location = (0, 0, 0)
    objCamOrig.empty_display_size = 1
    objCamOrig.empty_display_type = "PLAIN_AXES"
    cnMain.objects.link(objCamOrig)

    # bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1, location=(0, 0, 0))
    # objCamOrig = bpy.context.view_layer.objects.active
    # objCamOrig.name = sCamName

    #####################################################
    # Create render pinhole camera
    sSenName = sCamName + ".Sen"

    camX = bpy.data.cameras.get(sSenName)
    if camX is not None:
        bpy.data.cameras.remove(camX)
        camX = None
    # endif

    camX = bpy.data.cameras.new(sSenName)
    objCam = bpy.data.objects.new(name=sSenName, object_data=camX)

    # cnMain = bpy.context.scene.collection
    vlMain = bpy.context.view_layer
    cnMain.objects.link(objCam)
    vlMain.objects.active = objCam
    objCam.select_set(True)

    # Specify camera parameters
    fPixSize_um = dicSensor["fPixSize"]
    iPixCntX = dicSensor["iPixCntX"]
    iPixCntY = dicSensor["iPixCntY"]

    fPixSize_mm = 1e-3 * fPixSize_um
    fSenSizeX_mm = fPixSize_mm * iPixCntX
    fSenSizeY_mm = fPixSize_mm * iPixCntY
    fSenSizeMax_mm = max(fSenSizeX_mm, fSenSizeY_mm)
    fFocLen_mm = fSenSizeMax_mm

    camX.type = "PERSP"
    camX.lens = fFocLen_mm
    camX.lens_unit = "MILLIMETERS"
    # camX.type = 'ORTHO'
    # camX.ortho_scale = fSenSizeMax_mm
    camX.sensor_width = fSenSizeX_mm
    camX.sensor_height = fSenSizeY_mm

    if fSenSizeX_mm >= fSenSizeY_mm:
        camX.sensor_fit = "HORIZONTAL"
    else:
        camX.sensor_fit = "VERTICAL"
    # endif

    camX.shift_x = 0.0
    camX.shift_y = 0.0

    camX.clip_start = fBUperMM * 0.5 * fFocLen_mm
    camX.clip_end = fBUperMM * 1e7
    camX.display_size = max(0.5, fBUperMM * fFocLen_mm)

    # Sensor position relative to camera origin, which is
    # on last glass surface towards environment.
    fLensFocusToFrontLen_mm = abs(dicLensSystem["fSenPosZ"] - dicLensSystem["fEnvPosZ"])
    objCam.location = (0, 0, (fLensFocusToFrontLen_mm + fFocLen_mm) * fBUperMM)
    objCam.rotation_euler = (0, 0, math.radians(180))

    #####################################################
    # Create plane with ray splitter that acts as sensor plane
    sRaySplitName = sSenName + ".RS"
    meshRS = bpy.data.meshes.get(sRaySplitName)
    if meshRS is not None:
        bpy.data.meshes.remove(meshRS)
    # endif

    meshRS = bpy.data.meshes.new(sRaySplitName)
    objRS = bpy.data.objects.new(name=sRaySplitName, object_data=meshRS)
    cnMain.objects.link(objRS)

    objRS.location = (0, 0, fLensFocusToFrontLen_mm * fBUperMM)

    # Get ray splitter material
    # matRS = material.ray_splitter.Hex(
    #     dicLftPars['iHexRingCnt'],
    #     dicSensor['sName'].replace(" ", "_"),
    #     dicLensSystem['sName'].replace(" ", "_"),
    #     bForce=bForce)

    matRS = material.ray_splitter.Simple(
        dicSensor["sName"].replace(" ", "_"),
        dicLensSystem["sName"].replace(" ", "_"),
        bForce=bForce,
    )

    objRS.data.materials.append(matRS)

    xBMesh = bmesh.new()

    # Create Plane with Ray Splitter material
    fW2 = (math.ceil(fSenSizeX_mm * 10.0) / 20.0 + 0.1) * fBUperMM
    fH2 = (math.ceil(fSenSizeY_mm * 10.0) / 20.0 + 0.1) * fBUperMM
    fZ = 0.0

    tNorm = (0, 0, 1)
    v1 = xBMesh.verts.new((-fW2, -fH2, fZ))
    v2 = xBMesh.verts.new((fW2, -fH2, fZ))
    v3 = xBMesh.verts.new((fW2, fH2, fZ))
    v4 = xBMesh.verts.new((-fW2, fH2, fZ))
    xBMesh.faces.new((v1, v2, v3, v4))

    xBMesh.to_mesh(meshRS)
    xBMesh.free()

    #############################################################
    # Create the lens system
    objLensOrig = optics.CreateLensSystem(cnMain, sCamName, dicLensSystem, fScale=fScale, bUseLsTypeInName=False)

    objLensOrig.location = (0, 0, fLensFocusToFrontLen_mm * fBUperMM)

    #############################################################
    # Store AnyCam Data
    if dicAnyCamEx is None:
        dicAnyCamEx = {}
    # endif

    objCam["AnyCam"] = json.dumps(
        {
            "sDTI": "/anycam/camera/lft:1.2",
            "iSenResX": iPixCntX,
            "iSenResY": iPixCntY,
            "iRefractSurfCnt": objLensOrig["iRefractSurfCnt"],
            "sOrigin": objCamOrig.name,
            "mEx": dicAnyCamEx,
        }
    )

    #############################################################
    # Place objects in hierarchical order
    anyblend.viewlayer.Update()
    anyblend.object.ParentObject(objCam, objRS)
    anyblend.object.ParentObject(objCamOrig, objCam)
    anyblend.object.ParentObject(objCamOrig, objLensOrig)

    return {"bResult": True, "objCam": objCamOrig, "objAnyCam": objCam}


# enddef
