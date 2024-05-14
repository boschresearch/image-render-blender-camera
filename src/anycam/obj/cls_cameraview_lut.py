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

from typing import Union
from pathlib import Path
from anybase import path as anypath
import numpy as np
from .cls_cameraview import CCameraView
from ..model.cls_camera_lut import CCameraLut


class CCameraViewLut(CCameraView):

    #############################################################################
    def __init__(self):
        super().__init__()

        self._xCamLut: CCameraLut = None
        self._pathFile: str = None

    # enddef

    #############################################################################
    def GetDataDict(self):

        dicData = {
            "sDTI": "/anycam/cameraview/lut/std:1.0",
            "iLutBorderPixel": self._xCamLut.iLutBorderPixel,
            "iLutSuperSampling": self._xCamLut.iLutSuperSampling,
            "lLutCenterRC": list(self._xCamLut.tLutCenterRC),
            "sFilePath": self._pathFile.as_posix(),
        }

        dicData.update(super().GetDataDict())

        return dicData

    # enddef

    #############################################################################
    def Init(
        self,
        *,
        aImage: np.ndarray,
        iLutBorderPixel: int,
        iLutSuperSampling: int,
        lLutCenterRC: list[float],
        lAxes: list = None,
        lOrig_m: list = None,
        xFilePath: Union[str, list, tuple, Path] = None,
    ):
        self._pathFile: Path = None
        if xFilePath is not None:
            self._pathFile = anypath.MakeNormPath(xFilePath)
        # endif

        self._xCamLut = CCameraLut()

        if aImage is not None:
            self._xCamLut.FromArray(
                _imgLut=aImage,
                _iLutBorderPixel=iLutBorderPixel,
                _iLutSuperSampling=iLutSuperSampling,
                _fLutCenterRow=lLutCenterRC[0],
                _fLutCenterCol=lLutCenterRC[1],
            )
        elif self._pathFile is not None:
            self._xCamLut.FromFile(
                _xFilePath=self._pathFile,
                _iLutBorderPixel=iLutBorderPixel,
                _iLutSuperSampling=iLutSuperSampling,
                _fLutCenterRow=lLutCenterRC[0],
                _fLutCenterCol=lLutCenterRC[1],
            )
        else:
            raise RuntimeError("Neither an image nor a file path were given to initialize LUT camera")
        # endif

        super().Init(
            lPixCntXY=list(self._xCamLut.tImgPixCntRC[::-1]),
            fPixSize_um=1.0,
            fFovMax_deg=2.0 * self._xCamLut.fRadAngleMax_deg,
            lFovXY_deg=list(self._xCamLut.tLutFovXY_deg),
            lFovRangeXY_deg=[list(self._xCamLut.tLutAngleRangeX_deg), list(self._xCamLut.tLutAngleRangeY_deg)],
            bEnsureSquarePixel=False,
            lAxesXYZ=lAxes,
            lOrigXYZ_m=lOrig_m,
        )

    # enddef

    #############################################################################
    def DirsToCameraFrame(self, _lDirs):
        aDirs = np.array(_lDirs)
        aMatrix = np.array(self._lAxes).transpose()
        return aDirs @ aMatrix

    # enddef

    #############################################################################
    def ProjectToImage(self, _lPointsXYZ_m, *, _bDetailedFlags: bool = False):
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
        lPixPosRC, lPixelValid = self._xCamLut.RayDirsToPixelsRC(aLocPnts_m, _bNormalize=True)

        aPixPosRC = np.array(lPixPosRC)

        # Transform pixel positions, from pixel centered to pixel top-left.
        aPixPosRC += 0.5

        # Flip row-column to x-y order
        aPixPosXY = aPixPosRC[:, ::-1]

        # Filter out pixels outside the imager
        lPixelValid = [
            v
            & (p[0] < self._lPixCnt[0])
            & (p[1] < self._lPixCnt[1])
            & (p[0] > 0)
            & (p[1] > 0)
            for p, v in zip(aPixPosXY, lPixelValid)
        ]

        if _bDetailedFlags is True:
            return aPixPosXY.tolist(), lPixelValid, lPixelValid
        else:
            return aPixPosXY.tolist(), lPixelValid
        # endif

    # enddef


# endclass
