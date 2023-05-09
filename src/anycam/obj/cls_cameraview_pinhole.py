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

import math
import numpy as np
from typing import Union
from anybase.cls_anyexcept import CAnyExcept
from .cls_cameraview import CCameraView


class CCameraViewPinhole(CCameraView):

    #############################################################################
    def __init__(self):
        super().__init__()

        self._fFocLen_mm = 10.0
        self._lSenCtr_mm = [0, 0]
        self._fSenAspectYX = 0.0

    # enddef

    @property
    def fFocLen_mm(self):
        return self._fFocLen_mm

    # enddef

    @property
    def fSenCtrX_mm(self):
        return self._lSenCtr_mm[0]

    # enddef

    @property
    def fSenCtrY_mm(self):
        return self._lSenCtr_mm[1]

    # enddef

    #############################################################################
    def GetDataDict(self):

        # Since Blender pinhole cameras only have a single focal length,
        # the focal length is fixed here and the effective sensor size
        # is adjusted. The data output generated here, converts all values
        # back to pixel units.

        # Pixel indices index the center of a pixel.
        # For example, if a pixel array is 2 pixels wide, the center of the
        # array is at pixel index 0.5. If it is 3 pixels wide, the center
        # is at index 1.

        lEffPixSize_mm = [self._lSenSize_mm[i] / self._lPixCnt[i] for i in range(2)]
        lEffFocLen_pix = [self.fFocLen_mm / lEffPixSize_mm[i] for i in range(2)]
        lEffSenCtr_pix = [self._lSenCtr_mm[i] / lEffPixSize_mm[i] for i in range(2)]

        dicData = {
            "sDTI": "/anycam/cameraview/pin/std:1.0",
            "lFocLenXY_pix": lEffFocLen_pix,
            "lImgCtrXY_pix": lEffSenCtr_pix,
            "lImgCtrXY_pix/doc": "Optical image center relative to sensor center in pixel. X-axis points RIGHT, Y axis points UP",
        }

        dicData.update(super().GetDataDict())

        return dicData

    # enddef

    #############################################################################
    def Init(
        self,
        *,
        lPixCnt,
        fPixSize_um,
        fFovMax_deg=None,
        lFov_deg=None,
        lFovRange_deg=None,
        bEnsureSquarePixel=False,
        lAxes=None,
        lOrig_m=None
    ):

        super().Init(
            lPixCntXY=lPixCnt,
            fPixSize_um=fPixSize_um,
            fFovMax_deg=fFovMax_deg,
            lFovXY_deg=lFov_deg,
            lFovRangeXY_deg=lFovRange_deg,
            bEnsureSquarePixel=bEnsureSquarePixel,
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
    def ProjectToImage(
        self, _lPoints_m: Union[list[list[float]], np.ndarray], *, _bDetailedFlags: bool = False
    ) -> list[list[float]]:
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

        aLocPnts_m = self.PointsToCameraFrame(_lPoints_m)
        aInFront = aLocPnts_m[:, 2] < 0.0

        aScale = -self.fFocLen_mm / aLocPnts_m[:, 2]
        aPrjPnts_mm = aLocPnts_m[:, 0:2] * aScale[:, None]

        aSenCtr_mm = np.array(self._lSenCtr_mm)
        aSenSize_mm = np.array(self._lSenSize_mm)
        aSenOffset_mm = aSenSize_mm / 2.0 - aSenCtr_mm
        aPixPerMM = np.array(self._lPixCnt) / np.array(self._lSenSize_mm)

        aPrjPnts_pix = (aPrjPnts_mm + aSenOffset_mm) * aPixPerMM
        aPrjPnts_pix[:, 1] = self._lPixCnt[1] - aPrjPnts_pix[:, 1]

        aPrjPntsInt_pix = np.round(aPrjPnts_pix)

        # Flag whether projection is in image
        aInImage = np.logical_and(aInFront, aPrjPntsInt_pix[:, 0] < self.iPixCntX)
        aInImage = np.logical_and(aInImage, aPrjPntsInt_pix[:, 0] >= 0.0)
        aInImage = np.logical_and(aInImage, aPrjPntsInt_pix[:, 1] < self.iPixCntY)
        aInImage = np.logical_and(aInImage, aPrjPntsInt_pix[:, 1] >= 0.0)

        if _bDetailedFlags is True:
            return aPrjPnts_pix.tolist(), aInFront.tolist(), aInImage.tolist()
        else:
            return aPrjPnts_pix.tolist(), aInImage.tolist()
        # endif

    # enddef

    #############################################################################
    def _EvalFocLen_mm(self, iIdx):
        fHalfFov_rad = math.radians(self._lFov_deg[iIdx] / 2.0)
        return self._lSenSize_mm[iIdx] / (2.0 * math.tan(fHalfFov_rad))

    # enddef

    #############################################################################
    def _EvalFov_deg(self, iIdx):
        return math.degrees(math.atan(self._lSenSize_mm[iIdx] / 2.0 / self._lFocLen_mm[iIdx]))

    # enddef

    #############################################################################
    def _EvalSenSizeCenter_mm(self, _iAxis):

        lAngle_deg = [
            self._lFovCenter_deg[_iAxis] - self._lFov_deg[_iAxis] / 2.0,
            self._lFovCenter_deg[_iAxis] + self._lFov_deg[_iAxis] / 2.0,
        ]

        lPos_mm = [self._fFocLen_mm * math.tan(math.radians(lAngle_deg[i])) for i in range(2)]

        fSenSize_mm = lPos_mm[1] - lPos_mm[0]
        fSenCtr_mm = lPos_mm[0] + fSenSize_mm / 2.0

        return fSenSize_mm, fSenCtr_mm

    # enddef

    #############################################################################
    def _EvalFovRangeCenter_deg(self, _iAxis):

        lFovRange_deg = [
            math.degrees(math.atan((self._lSenCtr_mm[_iAxis] - self._lSenSize_mm[_iAxis] / 2.0) / self._fFocLen_mm)),
            math.degrees(math.atan((self._lSenCtr_mm[_iAxis] + self._lSenSize_mm[_iAxis] / 2.0) / self._fFocLen_mm)),
        ]

        fFovCtr_deg = lFovRange_deg[0] + (lFovRange_deg[1] - lFovRange_deg[0]) / 2.0

        return lFovRange_deg, fFovCtr_deg

    # enddef

    #############################################################################
    def _AdjustFov(self):

        # if one of the components of lFov_deg is zero, then calculate it from
        # the pixel resolution aspect ratio
        fZero_deg = 0.01
        if self._lFov_deg[0] <= fZero_deg and self._lFov_deg[1] > fZero_deg:
            self._lSenSize_mm[1], self._lSenCtr_mm[1] = self._EvalSenSizeCenter_mm(1)

            self._lSenSize_mm[0] = self._lSenSize_mm[1] / self._fPixResAspectYX
            self._lSenCtr_mm[0] = 0.0
            (
                self._lFovRange_deg[0],
                self._lFovCenter_deg[0],
            ) = self._EvalFovRangeCenter_deg(0)
            self._lFov_deg[0] = self._lFovRange_deg[0][1] - self._lFovRange_deg[0][0]

        elif self._lFov_deg[1] <= fZero_deg and self._lFov_deg[0] > fZero_deg:
            self._lSenSize_mm[0], self._lSenCtr_mm[0] = self._EvalSenSizeCenter_mm(0)

            self._lSenSize_mm[1] = self._lSenSize_mm[0] * self._fPixResAspectYX
            self._lSenCtr_mm[1] = 0.0
            (
                self._lFovRange_deg[1],
                self._lFovCenter_deg[1],
            ) = self._EvalFovRangeCenter_deg(1)
            self._lFov_deg[1] = self._lFovRange_deg[1][1] - self._lFovRange_deg[1][0]

        elif self._lFov_deg[1] <= fZero_deg and self._lFov_deg[0] <= fZero_deg:
            raise CAnyExcept("Error: Zero field of view given")
        # endif

        for i in range(2):
            self._lSenSize_mm[i], self._lSenCtr_mm[i] = self._EvalSenSizeCenter_mm(i)
        # endfor
        self._fSenAspectYX = self._lSenSize_mm[1] / self._lSenSize_mm[0]

    # enddef

    #############################################################################
    def _AdjustAspect(self):

        # if square pixel have to be ensured, then expand the field of view
        # so that it fits the pixel resolution aspect ratio
        if self._bEnsureSquarePixel:
            if self._fSenAspectYX != self._fPixResAspectYX:
                if self._lSenSize_mm[0] >= self._lSenSize_mm[1]:
                    self._lSenSize_mm[1] = self._lSenSize_mm[0] * self._fPixResAspectYX
                    (
                        self._lFovRange_deg[1],
                        self._lFovCenter_deg[1],
                    ) = self._EvalFovRangeCenter_deg(1)
                    self._lFov_deg[1] = self._lFovRange_deg[1][1] - self._lFovRange_deg[1][0]
                else:
                    self._lSenSize_mm[0] = self._lSenSize_mm[1] / self._fPixResAspectYX
                    (
                        self._lFovRange_deg[0],
                        self._lFovCenter_deg[0],
                    ) = self._EvalFovRangeCenter_deg(0)
                    self._lFov_deg[0] = self._lFovRange_deg[0][1] - self._lFovRange_deg[0][0]
                # endif
                self._fSenAspectYX = self._lSenSize_mm[1] / self._lSenSize_mm[0]
            # endif

            self._fFovAspectYX = self._lFov_deg[1] / self._lFov_deg[0]
            self._fAspectX = 1.0
            self._fAspectY = 1.0

        else:
            fValue = self._fPixResAspectYX / self._fSenAspectYX
            if fValue >= 1.0:
                self._fAspectX = fValue
                self._fAspectY = 1.0
            else:
                self._fAspectX = 1.0
                self._fAspectY = 1.0 / fValue
            # endif
        # endif

    # enddef

    #############################################################################
    def EvalShift(self):

        lShift = [
            self._lSenCtr_mm[0] / self.fSenSizeMax_mm,
            self._lSenCtr_mm[1] / self.fSenSizeMax_mm,
        ]

        return lShift

    # enddef


# endclass
