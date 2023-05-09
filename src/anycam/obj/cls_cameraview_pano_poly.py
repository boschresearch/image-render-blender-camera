#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \obj\cls_cameraview_pano_equidist.py
# Created Date: Thursday, April 29th 2021, 9:45:00 am
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

import copy
import numpy as np
from typing import Optional, Union
from pathlib import Path

from anyblend.mesh.types import CMeshData

from ..model.cls_camera_pano_poly import CCameraPanoPoly
from .cls_cameraview import CCameraView


class CCameraViewPanoPoly(CCameraView):

    #############################################################################
    def __init__(self):
        super().__init__()

        self._xCamPoly: CCameraPanoPoly = None

    # enddef

    @property
    def lPolyCoef_rad_mm(self) -> list[float]:
        return self._xCamPoly.lPolyCoef_rad_mm

    # enddef

    @property
    def lCenterOffsetXY_mm(self) -> list[float]:
        return self._xCamPoly.lCenterOffsetXY_mm

    # enddef

    @property
    def lPolyFitQuality(self) -> list:
        return self._xCamPoly.lPolyFitQuality

    # enddef

    #############################################################################
    def GetDataDict(self):

        dicData = {
            "sDTI": "/anycam/cameraview/pano/poly:1.0",
            "lPolyCoef_rad_mm": self._xCamPoly.lPolyCoef_rad_mm,
            "lCenterOffsetXY_mm": self._xCamPoly.lCenterOffsetXY_mm,
        }

        dicData.update(super().GetDataDict())

        return dicData

    # enddef

    #############################################################################
    def Init(
        self,
        *,
        lPixCnt: list[int],
        fPixSize_um: float,
        lPolyCoef_rad_mm: list[float] = None,
        lCenterOffsetXY_mm: list[float] = None,
        fFovMax_deg: Optional[float] = None,
        lAxes: list[list[float]] = None,
        lOrig_m: list[float] = None,
        # ##########################
        aImage: np.ndarray = None,
        iLutBorderPixel: int = 0,
        iLutSuperSampling: int = 1,
        lLutCenterRC: list[float] = None,
        xFilePath: Union[str, list, tuple, Path] = None,
    ):

        self._lPixCnt = copy.deepcopy(lPixCnt)
        self._fPixSize_um = fPixSize_um

        if lAxes is None:
            self._lAxes = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        else:
            self._lAxes = lAxes.copy()
        # endif

        if lOrig_m is None:
            self._lOrig_m = [0, 0, 0]
        else:
            self._lOrig_m = lOrig_m.copy()
        # endif

        self._xCamPoly = CCameraPanoPoly()

        if lPolyCoef_rad_mm is not None and lCenterOffsetXY_mm is not None:
            self._xCamPoly.FromCoef(
                _lPixCntXY=self._lPixCnt,
                _fPixSize_um=self._fPixSize_um,
                _lPolyCoef_rad_mm=lPolyCoef_rad_mm,
                _lCenterOffsetXY_mm=lCenterOffsetXY_mm,
                _fFovMax_deg=fFovMax_deg,
            )
        elif aImage is not None or xFilePath is not None:
            self._xCamPoly.FromLut(
                _lPixCntXY=self._lPixCnt,
                _fPixSize_um=self._fPixSize_um,
                _fFovMax_deg=fFovMax_deg,
                _imgLut=aImage,
                _iLutBorderPixel=iLutBorderPixel,
                _iLutSuperSampling=iLutSuperSampling,
                _lLutCenterRC=lLutCenterRC,
                _xFilePath=xFilePath,
            )
        else:
            raise RuntimeError("Insufficient arguments provided to initialize polynomial camera.")
        # endif

        self._fMaxAngle_deg = self._xCamPoly.fMaxRadAngle_deg
        self._fFovMax_deg = self._xCamPoly.fFovMax_deg

        self._lFov_deg = self._xCamPoly.lFov_deg
        self._lFovRange_deg = [list(self._xCamPoly.tAngleRangeX_deg), list(self._xCamPoly.tAngleRangeY_deg)]
        self._lFovCenter_deg = [
            self._lFovRange_deg[0][0] + self._lFov_deg[0] / 2.0,
            self._lFovRange_deg[1][0] + self._lFov_deg[1] / 2.0,
        ]

        self._bEnsureSquarePixel = True
        self._fPixResAspectYX = 1.0
        self._fFovAspectYX = self._lFov_deg[1] / self._lFov_deg[0]

        self._lSenSize_mm = self._xCamPoly.lSenSizeXY_mm
        self._lPixPerDeg = [self._lPixCnt[0] / self._lFov_deg[0], self._lPixCnt[1] / self._lFov_deg[1]]

        self._fAspectX = 1.0
        self._fAspectY = 1.0

    # enddef

    #############################################################################
    # Get relative shift from sensor center to principle point
    def GetPrinciplePointShift(self) -> tuple[float, float]:
        return (
            -self._xCamPoly.lCenterOffsetXY_mm[0] / self._xCamPoly.lSenSizeXY_mm[0],
            -self._xCamPoly.lCenterOffsetXY_mm[1] / self._xCamPoly.lSenSizeXY_mm[1],
        )

    # enddef

    #############################################################################
    # Evaluate Distortion Polynomial
    # def GetRayAnglesAtPos_mm(self, _aPosXY_mm: np.ndarray) -> np.ndarray:

    #############################################################################
    def DirsToCameraFrame(self, _lDirs):
        aDirs = np.array(_lDirs)
        aMatrix = np.array(self._lAxes).transpose()
        return aDirs @ aMatrix

    # enddef

    #############################################################################
    def ProjectToImage(self, _lPointsXYZ_m: list[list[float]], *, _bDetailedFlags: bool = False):
        """Project 3D-world point to image.

        Parameters
        ----------
        _lPointsXYZ_m : list[list[float]]
            Coordinates of 3D-points in world coordinate system.

        Returns
        -------
        list[list[float]]
            2D-pixel coordinates (X,Y) in CV-image coordinate system,
            with origin at top-left of image and x-axis pointing right,
            y-axis pointing down.
        """

        # Transform world points to points in camera frame
        aLocPnts_m = self.PointsToCameraFrame(_lPointsXYZ_m)

        # Map 3D-points in camera frame to pixel centered pixel positions
        # Set _bInvertPixelDir = True, if the camera object is rotated 180° about Z
        # and the polynomial coefficients are not negated.
        aPixPosXY, aPixelValid = self._xCamPoly.RayDirsToPixelsXY(aLocPnts_m, _bNormalize=True, _bInvertPixelDir=False)

        # Map to CV-Coordinate system, with origin at top-left and y-axis pointing down.
        aPixPosXY[:, 1] = self._xCamPoly.lPixCntXY[1] - aPixPosXY[:, 1]

        if _bDetailedFlags is True:
            return aPixPosXY.tolist(), aPixelValid.tolist(), aPixelValid.tolist()
        else:
            return aPixPosXY.tolist(), aPixelValid.tolist()
        # endif

    # enddef

    #############################################################################
    def GetFrustumMesh(
        self, *, _fRayLen: float, _fMaxEdgeAngle_deg: float = 1.0, _fSurfAngleStep_deg: float = 10.0
    ) -> CMeshData:

        return self._xCamPoly.GetFrustumMesh(
            _fRayLen=_fRayLen, _fMaxEdgeAngle_deg=_fMaxEdgeAngle_deg, _fSurfAngleStep_deg=_fSurfAngleStep_deg
        )

    # enddef


# endclass
