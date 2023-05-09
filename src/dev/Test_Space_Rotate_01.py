#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \_dev\Test_Space_Rotate_01.py
# Created Date: Tuesday, January 25th 2022, 9:01:12 am
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


def TransformObjectsWorldMatrix(*, xObjects, matX):

    for objX in xObjects:
        if objX.parent is None and all(
            (x.type != "FOLLOW_PATH" for x in objX.constraints)
        ):

            objX.matrix_world = matX @ objX.matrix_world
        # endif
    # endfor objects


# enddef


def SetRotationShader(*, ngMain, sLabel, tAngles):

    iRotNodeCnt = 0

    ndRot = next((x for x in ngMain if x.label == sLabel), None)
    if ndRot is not None:
        ndRot.rotation_type = "EULER_XYZ"
        ndRot.inputs["Rotation"].default_value = tAngles
        iRotNodeCnt += 1
    else:
        print("Node not found")
    # endif

    for ndX in ngMain:
        print(ndX.type)
        if ndX.type == "GROUP":
            print("Try group {}".format(ndX.name))
            iRotNodeCnt += SetRotationShader(
                ngMain=ndX.node_tree.nodes, sLabel=sLabel, tAngles=tAngles
            )
        # endif
    # endfor

    return iRotNodeCnt


# enddef


def SetWorldShaderRotation(*, xContext, tAngles):

    sRotNodeLabel = "AnyCam.World.Rotate"
    ngWorld = xContext.scene.world.node_tree.nodes

    iRotNodeCnt = SetRotationShader(
        ngMain=ngWorld, sLabel=sRotNodeLabel, tAngles=tAngles
    )
    if iRotNodeCnt == 0:
        print(
            "WARNING: World shader has no rotation node with label 'AnyCam.World.Rotate'. "
            "World background may not be rotated correctly."
        )
    # endif


# enddef


def TransformCameraAsOrigin(*, xContext):

    sOriginName = ".temp.AnyCam.Origin.World"
    objOrigin = bpy.data.objects.get(sOriginName)

    if objOrigin is not None:
        RevertTransformCameraAsOrigin(xContext=xContext)
    # endif

    objOrigin = bpy.data.objects.new(sOriginName, None)
    xContext.view_layer.layer_collection.collection.objects.link(objOrigin)

    objOrigin.location = (0, 0, 0)

    objCam = xContext.scene.camera
    matCamInv = objCam.matrix_world.inverted()

    TransformObjectsWorldMatrix(xObjects=xContext.view_layer.objects, matX=matCamInv)

    eulX = objCam.matrix_world.to_euler()
    tAngles = (eulX.x, eulX.y, eulX.z)
    SetWorldShaderRotation(xContext=xContext, tAngles=tAngles)

    return True


# enddef


def RevertTransformCameraAsOrigin(*, xContext, bDoThrow=True):

    sOriginName = ".temp.AnyCam.Origin.World"
    objOrigin = bpy.data.objects.get(sOriginName)
    if objOrigin is None:
        if bDoThrow is True:
            raise RuntimeError("Original origin object not found")
        else:
            return False
        # endif
    # endif

    matOrigInv = objOrigin.matrix_world.inverted()

    TransformObjectsWorldMatrix(xObjects=xContext.view_layer.objects, matX=matOrigInv)
    SetWorldShaderRotation(xContext=xContext, tAngles=(0, 0, 0))

    bpy.data.objects.remove(objOrigin)
    return True


# enddef


try:
    xContext = bpy.context

    # TransformCameraAsOrigin(xContext=xContext)
    RevertTransformCameraAsOrigin(xContext=xContext)
except Exception as xEx:
    print("Exception: {}".format(str(xEx)))
# endtry
