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

import sys
import numpy as np

from anybase.cls_anyexcept import CAnyExcept
from .cls_cameraview import CCameraView


class CCameraViewPanoEquidist(CCameraView):

    #############################################################################
    def __init__(self):
        super().__init__()
        self._lPixCntMax = [0, 0]

    # enddef

    @property
    def iPixCntMaxX(self):
        return self._lPixCntMax[0]

    # enddef

    @property
    def iPixCntMaxY(self):
        return self._lPixCntMax[1]

    # enddef

    #############################################################################
    def GetDataDict(self):

        dicData = {
            "sDTI": "/anycam/cameraview/pano/equidist:1.0",
            "lPixCntMaxXY": self._lPixCntMax,
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

        self._lPixCntMax = [int(round(self._lPixPerDeg[i] * self._fFovMax_deg)) for i in range(2)]

        # sys.stderr.write(f"_lPixCnt: {self._lPixCnt}\n")
        # sys.stderr.write(f"lPixCntMax: {self._lPixCntMax}\n")
        # sys.stderr.write(f"_fFovMax_deg: {self._fFovMax_deg}\n")

        # The maximal pixel count needs to have the same parity
        # as the target pixel resolution. Otherwise, we would
        # need to crop at half-pixels.
        if (self._lPixCntMax[0] % 2) != (self._lPixCnt[0] % 2):
            # We adjust the maximal pixel count to achieve the same parity
            # and then recalculate the maximal FoV, so that the crop
            # calculation works properly.
            self._lPixCntMax[0] += 1
            self._fFovMax_deg = self._lPixCntMax[0] / self._lPixPerDeg[0]
            # sys.stderr.write(f"_lPixCntMax: {self._lPixCntMax[0]}\n")
            # sys.stderr.write(f"_fFovMax_deg: {self._fFovMax_deg}\n")
        # endif

        # sys.stderr.flush()

    # enddef

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
        # print("\n\n")

        fDegPerRad = 180.0 / np.pi
        aZ = np.array([0.0, 0.0, -1.0])

        aLocPnts_m = self.PointsToCameraFrame(_lPointsXYZ_m)

        # Normalize vectors to location
        aLocPntsUnit = aLocPnts_m / np.linalg.norm(aLocPnts_m, axis=1)[:, np.newaxis]

        # Evaluate angle of normalized vectors to optical axis
        aLocPntsUnit_x_Z = -np.cross(aLocPntsUnit, aZ)
        aLocPntsUnit_d_Z = np.dot(aLocPntsUnit, aZ)
        aRadAngle_deg = np.arctan2(np.linalg.norm(aLocPntsUnit_x_Z, axis=1), aLocPntsUnit_d_Z) * fDegPerRad

        # print("RadAngle_deg: {}".format(aRadAngle_deg[0]))

        # All points that are within the angle range, can be projected into the image
        aInFront = aRadAngle_deg <= self._fFovMax_deg
        # print("InFront: {}".format(aInFront[0]))

        # Offset from optical center to bottom-left corner
        aOffset_pix = np.array([self.lFovRange_deg[0][0], self.lFovRange_deg[1][0]]) * self._lPixPerDeg[0]

        # Convert angle of projection ray into pixels by constant factor
        aRadPix = aRadAngle_deg * self._lPixPerDeg[0]
        # print("RadPix: {}".format(aRadPix[0]))

        # The direction where the image point is relative to the image center
        # The vector is not yet normalized
        # aImgDir = np.array([-aLocPntsUnit_x_Z[:, 1], aLocPntsUnit_x_Z[:, 0]]).T
        aImgDir = aLocPntsUnit - aZ * aLocPntsUnit_d_Z[:, np.newaxis]
        # print("ImgDir: {}".format(aImgDir[0]))

        aImgDir = aImgDir[:, 0:2]
        # print("ImgDir: {}".format(aImgDir[0]))

        # Normalize only those vectors in aImgDir that have a norm >= 1e-6
        aImgDirNorm = np.linalg.norm(aImgDir, axis=1)
        aMask = aImgDirNorm >= 1e-6
        aImgDir = np.divide(aImgDir, aImgDirNorm[:, np.newaxis], where=aMask[:, np.newaxis])
        # print("ImgDir norm: {}".format(aImgDir[0]))

        # Ensure that vectors with norm < 1e-6 are set to zero
        aImgDir[~aMask, :] = 0.0
        # print("ImgDir norm masked: {}".format(aImgDir[0]))

        # Evaluate the pixel position in the image of the projected point
        aPrjPnts_pix = aImgDir * aRadPix[:, np.newaxis] - aOffset_pix
        # print("PrjPnts_pix: {}".format(aPrjPnts_pix[0]))

        # Flip the y-axis to output image coordinates in CV-coordinate frame,
        # instead of camera frame
        aPrjPnts_pix[:, 1] = self._lPixCnt[1] - aPrjPnts_pix[:, 1]
        # print("PrjPnts_pix flipped y: {}".format(aPrjPnts_pix[0]))

        aPrjPntsInt_pix = np.round(aPrjPnts_pix)

        # Flag whether projection is in image
        aInImage = np.logical_and(aInFront, aPrjPntsInt_pix[:, 0] < self.iPixCntX)
        aInImage = np.logical_and(aInImage, aPrjPntsInt_pix[:, 0] >= 0.0)
        aInImage = np.logical_and(aInImage, aPrjPntsInt_pix[:, 1] < self.iPixCntY)
        aInImage = np.logical_and(aInImage, aPrjPntsInt_pix[:, 1] >= 0.0)
        # print("InFront final: {}".format(aInFront[0]))
        # print("\n\n")

        if _bDetailedFlags is True:
            return aPrjPnts_pix.tolist(), aInFront.tolist(), aInImage.tolist()
        else:
            return aPrjPnts_pix.tolist(), aInImage.tolist()
        # endif

    # enddef

    #############################################################################
    def _AdjustFov(self):

        # if one of the components of lFov_deg is zero, then calculate it from
        # the pixel resolution aspect ratio
        fZero_deg = 0.01
        if self._lFov_deg[0] <= fZero_deg and self._lFov_deg[1] > fZero_deg:
            self._lFov_deg[0] = self._lFov_deg[1] / self._fPixResAspectYX
            self._lFovRange_deg[0] = [-self._lFov_deg[0] / 2.0, self._lFov_deg[0] / 2]

        elif self._lFov_deg[1] <= fZero_deg and self._lFov_deg[0] > fZero_deg:
            self._lFov_deg[1] = self._lFov_deg[0] * self._fPixResAspectYX
            self._lFovRange_deg[1] = [-self._lFov_deg[1] / 2.0, self._lFov_deg[1] / 2]

        elif self._lFov_deg[1] <= fZero_deg and self._lFov_deg[0] <= fZero_deg:
            raise CAnyExcept("Error: Zero field of view given")
        # endif

    # enddef

    #############################################################################
    def _AdjustAspect(self):

        # if square pixel have to be ensured, then expand the field of view
        # so that it fits the pixel resolution aspect ratio
        if self._bEnsureSquarePixel:
            if self._fFovAspectYX != self._fPixResAspectYX:
                if self._lFov_deg[0] >= self._lFov_deg[1]:
                    self._lFov_deg[1] = self._lFov_deg[0] * self._fPixResAspectYX
                else:
                    self._lFov_deg[0] = self._lFov_deg[1] / self._fPixResAspectYX
                # endif
                self._fFovAspectYX = self._fPixResAspectYX
            # endif
            self._fAspectX = 1.0
            self._fAspectY = 1.0
        else:
            fValue = self._fPixResAspectYX / self._fFovAspectYX
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
    def EvalCrop(self):

        lPixIdxMin = [
            int(
                round(
                    (self._lFovCenter_deg[i] - self._lFov_deg[i] / 2.0) * self._lPixPerDeg[i]
                    + self._lPixCntMax[i] / 2.0
                )
            )
            for i in range(2)
        ]

        fCropLeft = lPixIdxMin[0] / self.iPixCntMaxX
        fCropRight = (lPixIdxMin[0] + self.iPixCntX) / self.iPixCntMaxX
        fCropBot = lPixIdxMin[1] / self.iPixCntMaxY
        fCropTop = (lPixIdxMin[1] + self.iPixCntY) / self.iPixCntMaxY

        return [fCropLeft, fCropRight, fCropBot, fCropTop]

    # enddef


# endclass
