#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_camera_pano_poly.py
# Created Date: Wednesday, January 25th 2023, 9:08:16 am
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


import os
from typing import Optional, Union

# need to enable OpenExr explicitly
import numpy as np
from numpy.polynomial.polynomial import Polynomial
import math

from pathlib import Path
from anyblend.mesh.types import CMeshData

from .cls_camera_lut import CCameraLut


# ##########################################################################################################
class CCameraPanoPoly:
    def __init__(self):
        self._aPixCntXY: np.ndarray = None
        self._fPixSize_um: float = None
        self._fPixSize_mm: float = None
        self._fFovMax_deg: float = None

        self._polyAngle_rad_mm: Polynomial = None
        self._polyRadius_mm_rad: Polynomial = None
        self._fPolyRadiusFit_ResidualMax_mm: float = None
        self._fPolyRadiusFit_ResidualMax_pix: float = None

        self._aCenterOffsetXY_mm: np.ndarray = None
        self._aCenterPosXY_mm: np.ndarray = None
        self._aSenSizeXY_mm: np.ndarray = None

        self._fSenMaxRad_mm: float = None
        self._fMaxRadAngle_deg: float = None
        self._tAngleRangeX_deg: tuple[float, float] = None
        self._tAngleRangeY_deg: tuple[float, float] = None

        self._lPolyFitQuality: list = None

    # enddef

    @property
    def lFov_deg(self) -> list[float]:
        return [
            self._tAngleRangeX_deg[1] - self._tAngleRangeX_deg[0],
            self._tAngleRangeY_deg[1] - self._tAngleRangeY_deg[0],
        ]

    # enddef

    @property
    def lPolyCoef_rad_mm(self) -> list[float]:
        lCoef = [0.0, 0.0, 0.0, 0.0, 0.0]

        for iIdx, fValue in enumerate(self._polyAngle_rad_mm.convert().coef.tolist()):
            if iIdx > 4:
                break
            # endif

            lCoef[iIdx] = fValue
        # endfor

        return lCoef

    # enddef

    @property
    def lPolyFitQuality(self) -> list:
        return self._lPolyFitQuality

    # enddef

    @property
    def polyAngle_rad_mm(self) -> Polynomial:
        return self._polyAngle_rad_mm.copy()

    # enddef

    @property
    def polyRadius_mm_rad(self) -> Polynomial:
        return self._polyRadius_mm_rad.copy()

    # enddef

    @property
    def fPolyRadiusFit_ResidualMax_mm(self) -> float:
        return self._fPolyRadiusFit_ResidualMax_mm

    # enddef

    @property
    def fPolyRadiusFit_ResidualMax_pix(self) -> float:
        return self._fPolyRadiusFit_ResidualMax_pix

    # enddef

    @property
    def fMaxRadAngle_deg(self) -> float:
        return self._fMaxRadAngle_deg

    # enddef

    @property
    def fFovMax_deg(self) -> float:
        return self._fFovMax_deg

    # enddef

    @property
    def tAngleRangeX_deg(self) -> tuple[float, float]:
        return self._tAngleRangeX_deg

    # enddef

    @property
    def tAngleRangeY_deg(self) -> tuple[float, float]:
        return self._tAngleRangeY_deg

    # enddef

    @property
    def lPixCntXY(self) -> list[int]:
        return self._aPixCntXY.tolist()

    # enddef

    @property
    def lSenSizeXY_mm(self) -> list[float]:
        return self._aSenSizeXY_mm.tolist()

    # enddef

    @property
    def lCenterOffsetXY_mm(self) -> list[float]:
        return self._aCenterOffsetXY_mm.tolist()

    # enddef

    # #########################################################################################
    def FromCoef(
        self,
        *,
        _lPixCntXY: list[int],
        _fPixSize_um: float,
        _lPolyCoef_rad_mm: list[float],
        _lCenterOffsetXY_mm: list[float],
        _fFovMax_deg: float = None,
    ):
        """Initialize panoramic polynomial camera from polynomial coefficients.

        Parameters
        ----------
        _lPixCntXY : list[float]
            The number of pixels in the sensor (horizontal, vertical)
        _fPixSize_um : float
            The pixel size in microns
        _lPolyCoef_rad_mm : list[float]
            The polynomial coefficients for a polynomial that maps millimeter to radians
        _lCenterOffsetXY_mm : list[float]
            The offset of the principle point from the center of the sensor in millimeters,
            where the x-coordinate is the value to the right of the sensor center,
            and the y-coordinate is the value ABOVE the sensor center. That is, the
            x-axis points right and the y-axis up.
        """
        self._aPixCntXY = np.array(_lPixCntXY)
        self._fPixSize_um = _fPixSize_um
        self._fPixSize_mm = self._fPixSize_um * 1e-3
        self._aSenSizeXY_mm = (self._fPixSize_um * 1e-3) * self._aPixCntXY
        self._aCenterOffsetXY_mm = np.array(_lCenterOffsetXY_mm)

        # Position of principle point relative to bottom-left of sensor,
        # with x-axis pointing RIGHT and y-axis pointing UP.
        self._aCenterPosXY_mm = self._aSenSizeXY_mm / 2.0 + self._aCenterOffsetXY_mm

        self._fSenMaxRad_mm = (
            np.linalg.norm(self._aSenSizeXY_mm / 2.0 + np.abs(self._aCenterOffsetXY_mm)) + self._fPixSize_mm
        )

        # Default is a null polynomial
        lPolyCoef_rad_mm: list[float] = [0.0, 0.0, 0.0, 0.0, 0.0]

        # Replace default coefficients
        for iIdx, fVal in enumerate(_lPolyCoef_rad_mm):
            if iIdx > 4:
                break
            # endif
            lPolyCoef_rad_mm[iIdx] = fVal
        # endfor

        self._polyAngle_rad_mm: Polynomial = Polynomial(lPolyCoef_rad_mm)

        self._EvalAngleRanges(_fFovMax_deg)
        self._EvalInversePoly()

    # enddef FromCoef()

    # #########################################################################################
    def FromLut(
        self,
        *,
        _lPixCntXY: list[int],
        _fPixSize_um: float,
        _fFovMax_deg: float = None,
        _imgLut: np.ndarray = None,
        _xFilePath: Union[str, list, tuple, Path] = None,
        _iLutBorderPixel: int = 0,
        _iLutSuperSampling: int = 1,
        _lLutCenterRC: Optional[list[float]] = None,
    ):
        xCamLut = CCameraLut()

        fLutCenterRow: float = None
        fLutCenterCol: float = None
        if isinstance(_lLutCenterRC, list):
            fLutCenterRow = _lLutCenterRC[0]
            fLutCenterCol = _lLutCenterRC[1]
        # endif

        if _imgLut is not None:
            xCamLut.FromArray(
                _imgLut=_imgLut,
                _iLutBorderPixel=_iLutBorderPixel,
                _iLutSuperSampling=_iLutSuperSampling,
                _fLutCenterRow=fLutCenterRow,
                _fLutCenterCol=fLutCenterCol,
            )
        elif _xFilePath is not None:
            xCamLut.FromFile(
                _xFilePath=_xFilePath,
                _iLutBorderPixel=_iLutBorderPixel,
                _iLutSuperSampling=_iLutSuperSampling,
                _fLutCenterRow=fLutCenterRow,
                _fLutCenterCol=fLutCenterCol,
            )
        else:
            raise RuntimeError("Insufficient arguments supplied to initialize polynomial camera from LUT")
        # endif

        self._aPixCntXY = np.array(_lPixCntXY)
        self._fPixSize_um = _fPixSize_um
        self._fPixSize_mm = self._fPixSize_um * 1e-3
        self._aSenSizeXY_mm = self._fPixSize_mm * self._aPixCntXY
        iTotalPixCnt: int = int(self._aPixCntXY[0] * self._aPixCntXY[1])

        # Position of principle point relative to center of sensor,
        # with x-axis pointing RIGHT and y-axis pointing UP.
        self._aCenterOffsetXY_mm = self._fPixSize_mm * np.array(
            [
                xCamLut.tImgCenterRC[1] + 0.5 - xCamLut.tImgPixCntRC[1] / 2.0,
                xCamLut.tImgPixCntRC[0] / 2.0 - xCamLut.tImgCenterRC[0] + 0.5,
            ]
        )

        self._aCenterPosXY_mm = self._aSenSizeXY_mm / 2.0 + self._aCenterOffsetXY_mm
        self._fSenMaxRad_mm = (
            np.linalg.norm(self._aSenSizeXY_mm / 2.0 + np.abs(self._aCenterOffsetXY_mm)) + self._fPixSize_mm
        )

        aImgRad_mm = xCamLut.GetLutImgPixelRadii().flatten() * self._fPixSize_mm
        aImgAngles_rad = xCamLut.GetLutAngles_rad()[:, :, 0].flatten()

        # To improve the polynomial fit, weigh the data points
        # depending on the number of pixels per radius range.
        iBinCnt = int(np.max(self._aPixCntXY))
        aHistBins = np.linspace(0.0, np.max(aImgRad_mm), num=iBinCnt + 1)
        aHistBins[iBinCnt] += 1.0
        aRadCnt, _ = np.histogram(aImgRad_mm, bins=aHistBins)
        # Get index per radius to which bin it belongs
        aRadBins = np.digitize(aImgRad_mm, aHistBins) - 1

        # Evaluate weights
        aWeights = np.min(aRadCnt, where=aRadCnt > 0, initial=iTotalPixCnt) / (aRadCnt[aRadBins[:, np.newaxis]][:, 0])
        # aWeights = np.min(aRadCnt) / (aRadCnt[aRadBins[:, np.newaxis]][:, 0] * aHistBins.shape[0])
        # aWeights = aImgRad_mm.shape[0] / (aRadCnt[aRadBins[:, np.newaxis]][:, 0] * aHistBins.shape[0])

        # Perform the polynomial fit
        fImgMaxRad_mm = np.max(aImgRad_mm)
        lQuality: list
        self._polyAngle_rad_mm, lQuality = Polynomial.fit(
            aImgRad_mm, aImgAngles_rad, deg=4, w=aWeights, domain=[0.0, fImgMaxRad_mm], window=[0.0, 1.0], full=True
        )

        # Set zero'th element to zero
        lCoef = self._polyAngle_rad_mm.coef
        lCoef[0] = 0.0
        self._polyAngle_rad_mm = Polynomial(lCoef, domain=[0.0, fImgMaxRad_mm], window=[0.0, 1.0])

        self._lPolyFitQuality = [lQuality[0].tolist(), int(lQuality[1]), lQuality[2].tolist(), float(lQuality[3])]

        if _fFovMax_deg is None:
            fFovMax_deg = 2.0 * xCamLut.fRadAngleMax_deg
        else:
            fFovMax_deg = _fFovMax_deg
        # endif

        self._EvalAngleRanges(fFovMax_deg)
        self._EvalInversePoly()

        # ### DEBUG ###
        # print(f"fImgMaxRad_mm: {fImgMaxRad_mm}")
        # lCoefAngle = self._polyAngle_rad_mm.convert().coef.tolist()
        # lCoefRad = self._polyRadius_mm_rad.convert().coef.tolist()
        # print(lCoefAngle)
        # print(lCoefRad)
        # pass
        # ##############

    # enddef FromLut

    # #################################################################################################
    def _EvalAngleRanges(self, _fFovMax_deg: float):

        fSenMaxRadAngle_deg: float = math.degrees(self._polyAngle_rad_mm(self._fSenMaxRad_mm))
        if _fFovMax_deg is not None:
            self._fMaxRadAngle_deg = min(fSenMaxRadAngle_deg, _fFovMax_deg / 2.0)
        else:
            self._fMaxRadAngle_deg = fSenMaxRadAngle_deg
        # endif
        self._fFovMax_deg = 2.0 * self._fMaxRadAngle_deg

        # Maximal ray angles to left and right of sensor
        self._tAngleRangeX_deg = (
            -math.degrees(self._polyAngle_rad_mm(self._aCenterPosXY_mm[0])),
            math.degrees(self._polyAngle_rad_mm(self._aSenSizeXY_mm[0] - self._aCenterPosXY_mm[0])),
        )

        # Maximal ray angles down and up of sensor
        self._tAngleRangeY_deg = (
            -math.degrees(self._polyAngle_rad_mm(self._aCenterPosXY_mm[1])),
            math.degrees(self._polyAngle_rad_mm(self._aSenSizeXY_mm[1] - self._aCenterPosXY_mm[1])),
        )

    # enddef

    # #################################################################################################
    def _EvalInversePoly(self):

        iMaxRadPixCnt = math.ceil(self._fSenMaxRad_mm / self._fPixSize_mm)
        aRadius_mm = np.linspace(0.0, self._fSenMaxRad_mm, num=iMaxRadPixCnt + 1)
        aAngle_rad = self._polyAngle_rad_mm(aRadius_mm)
        fMaxAngle_rad = np.max(aAngle_rad)

        self._polyRadius_mm_rad, lResult = Polynomial.fit(
            aAngle_rad, aRadius_mm, deg=10, domain=[0.0, fMaxAngle_rad], window=[0.0, 1.0], full=True
        )

        # Set zero'th element to zero
        lCoef = self._polyRadius_mm_rad.coef
        lCoef[0] = 0.0
        self._polyRadius_mm_rad = Polynomial(lCoef, domain=[0.0, fMaxAngle_rad], window=[0.0, 1.0])

        aRadDiff_mm = np.abs(self._polyRadius_mm_rad(aAngle_rad) - aRadius_mm)
        self._fPolyRadiusFit_ResidualMax_mm = np.max(aRadDiff_mm)
        self._fPolyRadiusFit_ResidualMax_pix = self._fPolyRadiusFit_ResidualMax_mm / self._fPixSize_mm

        # ### DEBUG ###
        # print(lResult)
        # print(f"self._fPolyRadiusFit_ResidualMax_mm: {self._fPolyRadiusFit_ResidualMax_mm}")
        # print(f"self._fPolyRadiusFit_ResidualMax_pix: {self._fPolyRadiusFit_ResidualMax_pix}")
        # print(f"fMaxAngle_rad: {fMaxAngle_rad}")
        # print(self._lPolyRadiusFitInfo)
        # pass
        # ##############
        
    # enddef

    # ##########################################################################################################
    def RayDirsToPixelsXY(
        self, _aTestDirs: np.ndarray, *, _bInvertPixelDir: bool = False, _bNormalize: bool = False
    ) -> tuple[np.ndarray, np.ndarray]:
        """Map ray directions to 2D-pixel image positions in pixel-edge Blender image-coordinate system,
        with origin at BOTTOM-LEFT, x-axis pointing RIGHT, y-axis pointing UP.
        IMPORTANT: Pixel coordinates are pixel edge coordinates,
        e.g. pixel position value (0,0) is the bottom-left corner of the bottom-left pixel and
        pixel position value (0.5, 0.5) is the center of the bottom-left pixel.

        Parameters
        ----------
        _aTestDirs : np.ndarray
            Array of 3D-direction vectors in camera frame to map to image.
            Input vectors can be normalized, so that you can also pass 3D-point positions in the camera frame.

        _bNormalize : bool
            If true, the input vectors are normalized.

        Returns
        -------
        tuple[list[list[float]], list[bool]]
            Tuple of list of 2D (x, y) pixel positions
            and list of bool flags, whether projection is valid.
            IMPORTANT: Pixel coordinates are pixel edge coordinates,
            e.g. pixel position value (0,0) is the bottom-left corner of the bottom-left pixel and
            pixel position value (0.5, 0.5) is the center of the bottom-left pixel.
        """
        if len(_aTestDirs.shape) != 2:
            raise RuntimeError("Argument '_aRayDirs' must be a 2D array")
        # endif

        if _aTestDirs.shape[1] != 3:
            raise RuntimeError("Ray directions array must have size 3 in second dimension")
        # endif

        aTestDirs = _aTestDirs

        if _bNormalize is True:
            aTestDirsLen = np.linalg.norm(_aTestDirs, axis=1)
            # Normalized input ray directions
            aTestDirs = np.divide(_aTestDirs, aTestDirsLen[:, np.newaxis])
        # endif

        aRadDir = aTestDirs[:, 0:2]
        aRadLen = np.linalg.norm(aRadDir, axis=1)

        aRadZ = -aTestDirs[:, 2]
        aRadTheta = np.arctan2(aRadLen, aRadZ)

        aImgRad_mm = self._polyRadius_mm_rad(aRadTheta)

        aMask = aRadLen > 1e-6
        aScale_mm = np.zeros_like(aImgRad_mm)
        np.divide(aImgRad_mm, aRadLen, where=aMask, out=aScale_mm)

        if _bInvertPixelDir is True:
            aImgPos_mm = -aRadDir * aScale_mm[:, np.newaxis] + self._aCenterPosXY_mm
        else:
            aImgPos_mm = aRadDir * aScale_mm[:, np.newaxis] + self._aCenterPosXY_mm
        # endif

        aImgPos_pix = aImgPos_mm / self._fPixSize_mm

        aIsValid = aImgPos_pix[:, 0] < self._aPixCntXY[0]
        aIsValid = np.logical_and(aIsValid, aImgPos_pix[:, 0] >= 0.0)
        aIsValid = np.logical_and(aIsValid, aImgPos_pix[:, 1] < self._aPixCntXY[1])
        aIsValid = np.logical_and(aIsValid, aImgPos_pix[:, 1] >= 0.0)

        return (aImgPos_pix, aIsValid)

    # enddef

    # ##########################################################################################################
    # Create LUT from polynomial
    def GenLutRayDirs(self, *, _iPixCntX: int = None) -> np.ndarray:
        """Generate a LUT of normalized ray direction vectors from the given radial polynomial.

        Parameters
        ----------
        _iPixCntX : int, optional
            The number of horizontal pixels in the LUT, by default None.
            If None, then use the original resolution.

        Returns
        -------
        np.ndarray
            Row-major LUT of ray directions, ordered top to bottom in the rows and left to right in columns.
            The ray direction coordinate system is as follows:
            X-axis: horizontal left to right.
            Y-axis: vertical bottom to top.
            Z-axis: points opposite to the view direction along the optical axis.
                    That is, the camera optical axis points in (0,0,-1).
        """

        iPixCntX: int = None
        iPixCntY: int = None
        fPixSize_mm: float = None

        if _iPixCntX is None:
            iPixCntX, iPixCntY = self._aPixCntXY.tolist()
            fPixSize_mm = self._fPixSize_mm
        else:
            iPixCntX = int(_iPixCntX)
            fPixSize_mm = self._aSenSizeXY_mm[0] / iPixCntX
            iPixCntY = int(round(self._aSenSizeXY_mm[1] / fPixSize_mm))
        # endif

        if iPixCntX < 3 or iPixCntY < 3:
            raise RuntimeError(
                f"Pixel count for LUT generation must be at least 3 pixel, but has [{iPixCntX}, {iPixCntY}]"
            )
        # endif

        # Pixel positions are pixel-centered with origin at top-left.
        # Columns count from left to right.
        # Rows count from top to bottom.
        aColIdx = np.linspace(0.0, iPixCntX - 1, num=iPixCntX)
        aRowIdx = np.linspace(0.0, iPixCntY - 1, num=iPixCntY)

        aPosX = (aColIdx + 0.5) * fPixSize_mm
        aPosY = self._aSenSizeXY_mm[1] - (aRowIdx + 0.5) * fPixSize_mm

        aGridX, aGridY = np.meshgrid(aPosX, aPosY)
        # Positions on Sensor, with origin at bottom left,
        # with x-axis pointing right and y-axis pointing UP.
        aPosXY_mm = np.concatenate((aGridX[:, :, np.newaxis], aGridY[:, :, np.newaxis]), axis=2)

        # Positions relative to polynomial center
        aRelPosXY_mm = aPosXY_mm - self._aCenterPosXY_mm

        # Radius to relative pixel positions
        aRad_mm = np.linalg.norm(aRelPosXY_mm, axis=2)

        # Angles per pixel
        aAngle_rad = self._polyAngle_rad_mm(aRad_mm)

        # Z-Coordinates
        aTanAngle = np.tan(aAngle_rad)
        aZ_mm = np.ones_like(aTanAngle)
        np.divide(aRad_mm, aTanAngle, where=np.abs(aTanAngle) > 1e-6, out=aZ_mm)

        aRelPosXYZ_mm = np.concatenate((aRelPosXY_mm, -aZ_mm[:, :, np.newaxis]), axis=2)
        aRayDir = aRelPosXYZ_mm / np.expand_dims(np.linalg.norm(aRelPosXYZ_mm, axis=2), axis=2)

        # Null ray dirs outside the maximal viewing angle
        aRayDirFlat = aRayDir.reshape((-1, 3))
        aAngleFlat_rad = aAngle_rad.flatten()

        aRayDirFlat[aAngleFlat_rad > math.radians(self._fMaxRadAngle_deg), :] = 0.0

        return aRayDir

    # enddef

    # ##########################################################################################################
    def GetFrustumMesh(
        self, *, _fRayLen: float, _fMaxEdgeAngle_deg: float = 1.0, _fSurfAngleStep_deg: float = 10.0
    ) -> CMeshData:

        aRayDirs = self.GenLutRayDirs(_iPixCntX=100)

        # Pixel-centered polynomial center as row pixels from top.
        fCenterRow = (self._aSenSizeXY_mm[1] - self._aCenterPosXY_mm[1]) / self._fPixSize_mm - 0.5
        fCenterCol = self._aCenterPosXY_mm[0] / self._fPixSize_mm - 0.5

        xCamLut = CCameraLut()
        xCamLut.FromArray(
            _imgLut=aRayDirs,
            _iLutBorderPixel=0,
            _iLutSuperSampling=1,
            _fLutCenterRow=fCenterRow,
            _fLutCenterCol=fCenterCol,
        )

        return xCamLut.GetFrustumMesh(
            _fRayLen=_fRayLen, _fMaxEdgeAngle_deg=_fMaxEdgeAngle_deg, _fSurfAngleStep_deg=_fSurfAngleStep_deg
        )

    # enddef


# endclass
