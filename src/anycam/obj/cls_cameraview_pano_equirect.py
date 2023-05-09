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

from anybase.cls_anyexcept import CAnyExcept
from .cls_cameraview import CCameraView


class CCameraViewPanoEquirect(CCameraView):

    #############################################################################
    def __init__(self):
        super().__init__()

    # enddef

    #############################################################################
    def GetDataDict(self):

        dicData = {
            "sDTI": "/anycam/cameraview/pano/equirect:1.0",
        }

        dicData.update(super().GetDataDict())

        return dicData

    # enddef

    #############################################################################
    def Init(
        self, *, lPixCnt, fPixSize_um, fFovMax_deg=None, lFov_deg=None, lFovRange_deg=None, bEnsureSquarePixel=False
    ):

        super().Init(
            lPixCntXY=lPixCnt,
            fPixSize_um=fPixSize_um,
            fFovMax_deg=fFovMax_deg,
            lFovXY_deg=lFov_deg,
            lFovRangeXY_deg=lFovRange_deg,
            bEnsureSquarePixel=bEnsureSquarePixel,
        )

    # enddef

    #############################################################################
    def _AdjustFov(self):

        # if one of the components of lFov_deg is zero, then calculate it from
        # the pixel resolution aspect ratio
        fZero_deg = 0.01
        if self._lFov_deg[0] <= fZero_deg and self._lFov_deg[1] > fZero_deg:
            self._lFov_deg[0] = self._lFov_deg[1] / self._fPixResAspectYX
        elif self._lFov_deg[1] <= fZero_deg and self._lFov_deg[0] > fZero_deg:
            self._lFov_deg[1] = self._lFov_deg[0] * self._fPixResAspectYX
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
            # For equirectangular projection, the non-square pixels are a feature of the optics.
            self._fAspectX = 1.0
            self._fAspectY = 1.0
            # fValue = self._fPixResAspectYX / self._fFovAspectYX
            # if fValue >= 1.0:
            # 	self._fAspectX = fValue
            # 	self._fAspectY = 1.0
            # else:
            # 	self._fAspectX = 1.0
            # 	self._fAspectY = 1.0 / fValue
            # # endif
        # endif

    # enddef


# endclass
