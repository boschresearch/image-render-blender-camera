#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \util.py
# Created Date: Tuesday, March 23rd 2021, 11:18:57 am
# Author: Christian Perwass (CR/AEC5), Maarten Bieshaar (CR/AEC4)
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

import numpy as np


def MapToVirtualPinholeCamera(
    _SrcCamera,
    _fDstFocalLengthX,
    _fDstFocalLengthY,
    _fDstPrinciplePointX,
    _fDstPrinciplePointY,
    _lDstImageWidth,
    _lDstImageHeight,
    _aRotationMatrix=None,
):
    """Get a virtual pinhole camera for a given source camera model.

    Parameters
    ----------
    _SrcCamera : CCameraView
        Camera model which to use as source
    _fDstFocalLengthX : float
        Focal length in x direction of virtual pinhole camera.
    _fDstFocalLengthY : float
        Focal length in y direction of virtual pinhole camera.
    _fDstPrinciplePointX : float
        X coordinate of principle point.
    _fDstPrinciplePointY : float
        Y coordinate of principle point.
    _lDstImageWidth : int
        Width of destination image.
    _lDstImageHeight : int
        Height of destination image.
    _aRotationMatrix: np.ndarray, optional.
        Rotation matrix indicating rotation of virtual camera with respect to source camera, default None.

    Returns
    -------
    aDstIntrincics: np.ndarray (3x3)
        Intrinsics of virtual pinhole matrix.
    aDstWorld2CamRotationMatrix: np.ndarray (3x4)
        Transformation matrix indicating rotation and translation of virtual camera with respect
        to the origin of the source camera.
    aMapX: np.ndarray
        Mapping function in the x direction for realization of look-up virtual camera to source camera.
    aMapY: np.ndarray
        Mapping function in the y direction for realization of look-up virtual camera to source camera.
    aPointsInFoV: np.ndarray
        Mask which points are within the cameras field of view. Array of size (_lDstImageHeight x _lDstImageWidth).
    """
    # create intrinsic camera of virtual pinhole camera
    aDstIntrincics = np.array(
        [
            [_fDstFocalLengthX, 0, _fDstPrinciplePointX],
            [0, _fDstFocalLengthY, _fDstPrinciplePointY],
            [0, 0, 1],
        ]
    )
    # invert intrinsic of virtual pinhol camera
    aDstIntrincicsInv = np.linalg.inv(aDstIntrincics)

    # get indicies of image of the virtual pinhole camera virtual
    # the idea is to use these pixel coordinates and compute their respective mapping in the source image using
    # the source camera model
    aIndexY, aIndexX = np.indices((_lDstImageHeight, _lDstImageWidth))
    # get pixels
    aPoints_pix = np.array(
        [aIndexX.ravel(), aIndexY.ravel(), np.ones_like(aIndexX).ravel()]
    ).T

    if type(_aRotationMatrix) is np.ndarray:
        aRotationMatrix = np.copy(_aRotationMatrix)
    else:
        aRotationMatrix = np.eye(3)
    # endif

    aSrcCamOrigin = np.array(_SrcCamera._lOrig_m)
    aSrcCam2WorldRotationMatrix = np.array(_SrcCamera._lAxes)
    aOverallRotatonMatrix = aRotationMatrix @ aSrcCam2WorldRotationMatrix

    # want to have directional vectors from camera plane towards the "outer" world.
    # Actually for a standard pinhole model this is given by (-x, -y, f),
    # where f is the focal length. However, since our z-axis is pointing
    # towards the camera, we have to invert this. Hence, we have (-x, -y, -f) und thus we have
    # ot multiply by -1.
    # However, as the camera model (to be used later) flips the y-axis, we have to flip it in advance
    # Hence it remains "untouched". Hence, we also multiply by -1.
    aFlipMat = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])

    # convert to normalized image coordinates by applying the inverted intrinsic matrix
    # then rotate normalized image coordinates (virtual camera is now looking into the specified direction).
    aPointsWorld = aPoints_pix @ aDstIntrincicsInv.T @ aFlipMat @ aOverallRotatonMatrix

    # subsequently cope with translation
    aDirectionVectors = aPointsWorld + aSrcCamOrigin.reshape((1, -1))

    # apply the source camera model to obtain the mapping of the virtual camera points in the source camera/ image.
    aProjPoints, aPointsInFoV = _SrcCamera.ProjectToImage(aDirectionVectors)
    aProjPoints = np.array(aProjPoints)
    aPointsInFoV = np.array(aPointsInFoV)

    # create map_x and map-y
    aMapX = (
        aProjPoints[:, 0]
        .reshape((_lDstImageHeight, _lDstImageWidth))
        .astype(np.float32)
    )
    aMapY = (
        aProjPoints[:, 1]
        .reshape((_lDstImageHeight, _lDstImageWidth))
        .astype(np.float32)
    )

    # construct matrix for conversion of 3D world points into new virtual camera
    aDstWorld2CamRotationMatrix = aSrcCam2WorldRotationMatrix
    # construct world to blender camera matrix
    aDstWorld2CamRotationMatrix = np.hstack(
        (
            aDstWorld2CamRotationMatrix,
            -aDstWorld2CamRotationMatrix @ aSrcCamOrigin.reshape((-1, 1)),
        )
    )
    # rotate by specified rotation matrix
    aDstWorld2CamRotationMatrix = (
        aFlipMat @ aRotationMatrix @ aDstWorld2CamRotationMatrix
    )

    return (
        aDstIntrincics,
        aDstWorld2CamRotationMatrix,
        aMapX,
        aMapY,
        aPointsInFoV.reshape((_lDstImageHeight, _lDstImageWidth)),
    )


# enddef
