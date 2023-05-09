#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \obj\cls_cameraview.py
# Created Date: Thursday, April 29th 2021, 8:41:47 am
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
from typing import Union
from anybase.cls_anyexcept import CAnyExcept


class CCameraView:
    """Base class camera view class. Contains general information and abstract base functions for camera model."""

    #############################################################################
    def __init__(self):
        self._lPixCnt = [0, 0]
        self._fPixSize_um = 0.0
        self._fFovMax_deg = 0.0
        self._lFov_deg = [0, 0]
        self._lFovRange_deg = [0, 0]
        self._lFovCenter_deg = [0, 0]
        self._bEnsureSquarePixel = False

        self._fPixResAspectYX = 0.0
        self._fFovAspectYX = 0.0
        self._fMaxAngle_deg = 0.0
        self._lPixPerDeg = [0, 0]
        self._lSenSize_mm = [0, 0]

        self._fAspectX = 0.0
        self._fAspectY = 0.0

        # Camera axes X,Y,Z in world frame. X: right, Y: up, Z: behind.
        # Points in front of the camera have negative z-coordinates.
        self._lAxes: list[list[float]] = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

        # Origin (X,Y,Z) in world coordinates
        self._lOrig_m: list[float] = [0, 0, 0]

    # enddef

    @property
    def iPixCntX(self):
        return self._lPixCnt[0]

    # enddef

    @property
    def iPixCntY(self):
        return self._lPixCnt[1]

    # enddef

    @property
    def fPixSize_um(self):
        return self._fPixSize_um

    # enddef

    @property
    def fPixSize_mm(self):
        return 1e-3 * self._fPixSize_um

    # enddef

    @property
    def fAspectX(self):
        return self._fAspectX

    # enddef

    @property
    def fAspectY(self):
        return self._fAspectY

    # enddef

    @property
    def fSenSizeX_mm(self):
        return self._lSenSize_mm[0]

    # enddef

    @property
    def fSenSizeY_mm(self):
        return self._lSenSize_mm[1]

    # enddef

    @property
    def fSenSizeMax_mm(self):
        return max(self.fSenSizeX_mm, self.fSenSizeY_mm)

    # enddef

    @property
    def fFovMax_deg(self):
        return self._fFovMax_deg

    # enddef

    @property
    def fPixPerDegX(self):
        return self._lPixPerDeg[0]

    # enddef

    @property
    def fPixPerDegY(self):
        return self._lPixPerDeg[1]

    # enddef

    @property
    def lPixPerDeg(self):
        return self._lPixPerDeg

    # enddef

    @property
    def lFovCenter_deg(self):
        return self._lFovCenter_deg

    # enddef

    @property
    def lFov_deg(self):
        return self._lFov_deg

    # enddef

    @property
    def lFovRange_deg(self):
        return self._lFovRange_deg

    # enddef

    @property
    def lAxes(self):
        return self._lAxes

    # enddef

    @property
    def lOrig_m(self):
        return self._lOrig_m

    # enddef

    #############################################################################
    def GetDataDict(self):

        return {
            "lPixCntXY": self._lPixCnt,
            "fPixSize_um": self.fPixSize_um,
            "lAspectXY": [self.fAspectX, self.fAspectY],
            "fFovMax_deg": self.fFovMax_deg,
            "lFovCenterXY_deg": self.lFovCenter_deg,
            "lFovXY_deg": self.lFov_deg,
            "lFovRangeXY_deg": self.lFovRange_deg,
            "lAxes": self.lAxes,
            "lAxes/doc": "Right-handed CS with X pointing to right, Y pointing up and -Z pointing in view direction",
            "lOrig_m": self.lOrig_m,
            "lOrig_m/doc": "Given in right-handed world CS",
        }

    # enddef

    #############################################################################
    def _AdjustFov(self):
        return
        # Avoid raise here just so that the linter does not get confused
        # raise CAnyExcept("Function not implemented")

    # enddef

    #############################################################################
    def _AdjustAspect(self):
        return
        # Avoid raise here just so that the linter does not get confused
        # raise CAnyExcept("Function not implemented")

    # enddef

    #############################################################################
    def Init(
        self,
        *,
        lPixCntXY,
        fPixSize_um,
        fFovMax_deg=None,
        lFovXY_deg=None,
        lFovRangeXY_deg=None,
        bEnsureSquarePixel=False,
        lAxesXYZ=None,
        lOrigXYZ_m=None
    ):

        self._lPixCnt = copy.deepcopy(lPixCntXY)
        self._fPixSize_um = fPixSize_um
        self._fFovMax_deg = fFovMax_deg
        self._lFov_deg = copy.deepcopy(lFovXY_deg) if lFovXY_deg is not None else None
        self._lFovRange_deg = copy.deepcopy(lFovRangeXY_deg) if lFovRangeXY_deg is not None else None
        self._bEnsureSquarePixel = bEnsureSquarePixel

        if lAxesXYZ is None:
            self._lAxes = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        else:
            self._lAxes = lAxesXYZ.copy()
        # endif

        if lOrigXYZ_m is None:
            self._lOrig_m = [0, 0, 0]
        else:
            self._lOrig_m = lOrigXYZ_m.copy()
        # endif

        self._fPixResAspectYX = self.iPixCntY / self.iPixCntX
        self._lSenSize_mm = [self.fPixSize_mm * self._lPixCnt[i] for i in range(2)]

        # Check if a mFovRange is given
        if self._lFovRange_deg is None:
            if self._lFov_deg is None:
                raise CAnyExcept("No panoramic field of view given")
            # endif
            self._lFov_deg = [abs(x) for x in self._lFov_deg]
            self._lFovCenter_deg = [0.0, 0.0]

            if self._fFovMax_deg is None:
                self._fFovMax_deg = max(self._lFov_deg[0], self._lFov_deg[1])
            else:
                for i in range(2):
                    if self._lFov_deg[i] > self._fFovMax_deg:
                        self._lFov_deg[i] = self._fFovMax_deg
                    # endif
                # endfor
            # endif

            self._fMaxAngle_deg = self._fFovMax_deg / 2.0
            self._lFovRange_deg = [
                [-self._lFov_deg[0] / 2.0, self._lFov_deg[0] / 2.0],
                [-self._lFov_deg[1] / 2.0, self._lFov_deg[1] / 2.0],
            ]
        else:
            # Maximum view angle from given FoV range
            self._fMaxAngle_deg = max(
                abs(self._lFovRange_deg[0][0]),
                abs(self._lFovRange_deg[0][1]),
                abs(self._lFovRange_deg[1][0]),
                abs(self._lFovRange_deg[1][1]),
            )

            if fFovMax_deg is None:
                self._fFovMax_deg = 2.0 * self._fMaxAngle_deg
            else:
                if self._fMaxAngle_deg > self._fFovMax_deg / 2.0:
                    self._fMaxAngle_deg = self._fFovMax_deg / 2.0
                    for j in range(2):
                        for i in range(2):
                            if self._lFovRange_deg[j][i] < 0.0 and self._lFovRange_deg[j][i] < -self._fMaxAngle_deg:
                                self._lFovRange_deg[j][i] = -self._fMaxAngle_deg
                            elif self._lFovRange_deg[j][i] >= 0.0 and self._lFovRange_deg[j][i] > self._fMaxAngle_deg:
                                self._lFovRange_deg[j][i] = self._fMaxAngle_deg
                            # endif
                        # endfor
                    # endfor
                # endif
            # endif

            self._lFov_deg = [
                abs(self._lFovRange_deg[0][1] - self._lFovRange_deg[0][0]),
                abs(self._lFovRange_deg[1][1] - self._lFovRange_deg[1][0]),
            ]

            self._lFovCenter_deg = [
                self._lFovRange_deg[0][0] + self._lFov_deg[0] / 2.0,
                self._lFovRange_deg[1][0] + self._lFov_deg[1] / 2.0,
            ]
        # endif

        # Adjust the field of view depending on the camera type
        self._AdjustFov()

        # Aspect ratio of the field-of-view
        self._fFovAspectYX = self._lFov_deg[1] / self._lFov_deg[0]

        self._AdjustAspect()
        self._lPixPerDeg = [self._lPixCnt[i] / self._lFov_deg[i] for i in range(2)]

    # enddef

    #############################################################################
    def PointsToCameraFrame(self, _lPointsXYZ_m: Union[list[list[float]], np.ndarray]) -> np.ndarray:
        """Transform 3D-points from world coordinate system to camera coordinate system.

        Parameters
        ----------
        _lPointsXYZ_m : list[list[float]]
            List of (X,Y,Z) coordinate in world frame.

        Returns
        -------
        list[float]
            Numpy array of (X,Y,Z) coordinates in camera frame.
        """
        if isinstance(_lPointsXYZ_m, list):
            aPointsXYZ_m = np.array(_lPointsXYZ_m)
        elif isinstance(_lPointsXYZ_m, np.ndarray):
            aPointsXYZ_m = _lPointsXYZ_m
        else:
            raise RuntimeError("Points argument is of invalid type")
        # endif

        aMatrix = np.array(self._lAxes).transpose()
        aOrig_m = np.array(self._lOrig_m)

        return (aPointsXYZ_m - aOrig_m) @ aMatrix

    # enddef


# enddef
