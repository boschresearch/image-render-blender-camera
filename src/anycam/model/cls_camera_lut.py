#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_camera_lut.py
# Created Date: Friday, January 6th 2023, 1:12:34 pm
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
from typing import Optional, Union, NamedTuple
from collections.abc import Iterable

# need to enable OpenExr explicitly
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2
import numpy as np
import math

from anybase import assertion
from pathlib import Path
from anybase import path as anypath
from anyblend.mesh.types import CMeshData

from scipy.spatial import KDTree


# ########################################################################################################
# Render crop tuple
class CRenderCrop(NamedTuple):
    fLeft: float
    fRight: float
    fBottom: float
    fTop: float


# endclass


# ########################################################################################################
# The camera LUT class
class CCameraLut:
    def __init__(self):
        # ########################################
        # Member Variables

        # The LUT image. Always contains 4 channels.
        # RGB: Ray direction
        # Alpha: Ray attenuation through vignetting.
        self._imgLut: np.ndarray = None

        # Mask of valid pixels in LUT
        self._aLutMask: np.ndarray = None

        # Number of LUT pixels used as border
        self._iLutBorderPixel: int = None

        # Number of LUT pixels per rendered pixel
        self._iLutSuperSampling: int = None

        # Image pixels per LUT pixel (1 / iLutSuperSampling)
        self._fImgPerLutPix: float = None

        # Number of pixels in LUT image as (rows, columns)
        self._tLutPixCntRC: tuple[int, int] = None

        # LUT principle point where optical axis passes through
        # as (row, column) floating point values.
        # This assumes the ray direction per LUT pixel is the ray direction
        # through the center of that pixel. Therefore, pixel index 0 references
        # the center of the first pixel and the center of an array of 2 by 3 pixels
        # is at (0.5, 1.0).
        # The origin for these coordinates is top/left.
        # Columns are indexed left to right and rows top to bottom.
        self._tLutCenterRC: tuple[float, float] = None

        # Number of image pixels taking in to account LUT border and super sampling.
        self._tImgPixCntRC: tuple[int, int] = None

        # Image pixel coordinates of principle point as (row, column)
        self._tImgCtrRC: tuple[int, int] = None

        # Integer image pixel coordinates to image principle point as (row, column)
        self._tImgCtrPixRC: tuple[int, int] = None

        # Offset from exact principle point to integer pixel coordinates
        self._tImgCtrOffsetRC: tuple[float, float] = None

        # Index to the central render pixel in row and column
        self._iRenderCtrPix: int = None

        # Total number of render pixels along rows and columns. Always odd.
        self._iRenderPixCnt: int = None

        # Camera shift values for fisheye equidistant
        self._tCamShiftXY: tuple[float, float] = None

        # Render FoV in degrees
        self._fRenderFoV_deg: float = None

        # Number of render pixels per degree
        self._fRenderPixPerDeg: float = None

        # Horizontal LUT angle range to be used in LUT camera shader
        self._tRenderLutAngleRangeX_deg: tuple[float, float] = None

        # Vertical LUT angle range to be used in LUT camera shader
        self._tRenderLutAngleRangeY_deg: tuple[float, float] = None

        # Horizontal angle range in degrees
        self._tLutAngleRangeX_deg: tuple[float, float] = None

        # Vertical angle range in degrees
        self._tLutAngleRangeY_deg: tuple[float, float] = None

        # Min and max columns of camera image in render image
        self._tRenderImgPixRangeCol: tuple[int, int] = None

        # Min and max rows of camera image in render image (with origin at top of image)
        self._tRenderImgPixRangeRow: tuple[int, int] = None

        # Render crop values to be used in Blender.
        # In Blender the crop origin is at the BOTTOM/left.
        self._xRenderCrop: CRenderCrop = None

        # Maximal radial view angle of LUT
        self._fRadAngleMax_deg: float = None
        # ########################################

    # enddef

    # ##########################################################################################################
    # Properties

    @property
    def fRadAngleMax_deg(self):
        return self._fRadAngleMax_deg

    # enddef

    @property
    def fRenderFoV_deg(self):
        return self._fRenderFoV_deg

    # enddef

    @property
    def fRenderFoV_rad(self):
        return math.radians(self._fRenderFoV_deg)

    # enddef

    @property
    def tCamShiftXY(self):
        return self._tCamShiftXY

    # enddef

    @property
    def tLutPixCntRC(self):
        return self._tLutPixCntRC

    # enddef

    @property
    def tLutCenterRC(self):
        return self._tLutCenterRC

    # enddef

    @property
    def tImgCenterRC(self):
        return self._tImgCtrRC

    # enddef

    @property
    def tImgPixCntRC(self):
        return self._tImgPixCntRC

    # enddef

    @property
    def iRenderPixCnt(self):
        return self._iRenderPixCnt

    # enddef

    @property
    def imgLut(self):
        return self._imgLut

    # enddef

    @property
    def imgLutFlipped(self):
        return np.flipud(self._imgLut)

    # enddef

    @property
    def aLutMask(self) -> np.ndarray:
        return self._aLutMask

    # enddef

    @property
    def tRenderLutAngleRangeX_deg(self):
        return self._tRenderLutAngleRangeX_deg

    # enddef

    @property
    def tRenderLutAngleRangeY_deg(self):
        return self._tRenderLutAngleRangeY_deg

    # enddef

    @property
    def tLutAngleRangeX_deg(self):
        return self._tLutAngleRangeX_deg

    # enddef

    @property
    def tLutAngleRangeY_deg(self):
        return self._tLutAngleRangeY_deg

    # enddef

    @property
    def tLutFovXY_deg(self):
        return (
            self._tLutAngleRangeX_deg[1] - self._tLutAngleRangeX_deg[0],
            self._tLutAngleRangeY_deg[1] - self._tLutAngleRangeY_deg[0],
        )

    # enddef

    @property
    def xRenderCrop(self):
        return self._xRenderCrop

    # enddef

    @property
    def iLutBorderPixel(self) -> int:
        return self._iLutBorderPixel

    # enddef

    @property
    def iLutSuperSampling(self) -> int:
        return self._iLutSuperSampling

    # enddef

    # ##########################################################################################################
    def LutToImgPixelValue(self, _fLutPix: float) -> float:
        return (_fLutPix - self._iLutBorderPixel - (self._iLutSuperSampling / 2.0 - 0.5)) * self._fImgPerLutPix

    # enddef

    # ##########################################################################################################
    def LutToImgPixel(self, _xLutPix: Iterable):
        return tuple([self.LutToImgPixelValue(x) for x in _xLutPix])

    # enddef

    # ##########################################################################################################
    def ImgToLutPixelValue(self, _fImgPix: float) -> float:
        return _fImgPix / self._fImgPerLutPix + self._iLutBorderPixel + (self._iLutSuperSampling / 2.0 - 0.5)

    # enddef

    # ##########################################################################################################
    def ImgToLutPixel(self, _xImgPix: Iterable):
        return tuple([self.ImgToLutPixelValue(x) for x in _xImgPix])

    # enddef

    # ##########################################################################################################
    def FromFile(
        self,
        *,
        _xFilePath: Union[str, list, tuple, Path],
        _iLutBorderPixel: int = 0,
        _iLutSuperSampling: int = 1,
        _fLutCenterRow: Optional[float] = None,
        _fLutCenterCol: Optional[float] = None,
    ):
        assertion.FuncArgTypes()

        pathLut = anypath.MakeNormPath(_xFilePath)
        if not pathLut.exists():
            raise RuntimeError(f"LUT file not found: {(pathLut.as_posix())}")
        # endif
        sPathLut = pathLut.as_posix()

        imgLut = cv2.imread(sPathLut, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_UNCHANGED)
        if imgLut is None:
            raise RuntimeError("Error loading image: {0}".format(sPathLut))
        # endif

        if len(imgLut.shape) != 3 or imgLut.shape[2] < 3:
            raise RuntimeError("LUT image has less than three channels")
        # endif

        # Flip order of color channel elements, as cv2 stores images as BGR and not RGB.
        if imgLut.shape[2] == 4:
            imgLut = imgLut[:, :, [2, 1, 0, 3]].astype(np.float32)
        else:
            imgLut = imgLut[:, :, ::-1].astype(np.float32)
        # endif

        self.FromArray(
            _imgLut=imgLut,
            _iLutBorderPixel=_iLutBorderPixel,
            _iLutSuperSampling=_iLutSuperSampling,
            _fLutCenterRow=_fLutCenterRow,
            _fLutCenterCol=_fLutCenterCol,
        )

    # enddef

    # ##########################################################################################################
    def FromArray(
        self,
        *,
        _imgLut: np.ndarray,
        _iLutBorderPixel: int = 0,
        _iLutSuperSampling: int = 1,
        _fLutCenterRow: Optional[float] = None,
        _fLutCenterCol: Optional[float] = None,
    ):
        self._iLutBorderPixel = max(0, _iLutBorderPixel)
        self._iLutSuperSampling = max(1, _iLutSuperSampling)
        self._fImgPerLutPix: float = 1.0 / self._iLutSuperSampling

        iLutRows, iLutCols, iLutChnl = _imgLut.shape

        if iLutChnl < 3:
            raise RuntimeError("LUT image has less than three channels")
        # endif

        self._tLutPixCntRC: tuple[int, int] = (iLutRows, iLutCols)

        imgDir = _imgLut[:, :, 0:3]

        # Normalize vectors in LUT image
        aLen = np.linalg.norm(imgDir, axis=2)
        self._aLutMask = np.expand_dims(aLen > 1e-6, axis=2)
        imgDirNorm = np.zeros(imgDir.shape)
        np.divide(imgDir, np.expand_dims(aLen, axis=2), out=imgDirNorm, where=self._aLutMask)

        # Add alpha channel as vignetting values per pixel
        if iLutChnl == 4:
            self._imgLut = np.concatenate(
                (imgDirNorm, np.expand_dims(_imgLut[:, :, 3], axis=2).astype(np.float32)), axis=2
            )
        else:
            self._imgLut = np.concatenate((imgDirNorm, np.ones((iLutRows, iLutCols, 1), dtype=np.float32)), axis=2)
        # endif

        # LUT center refers to the principle point
        fLutCtrRow = _fLutCenterRow
        if not isinstance(fLutCtrRow, float):
            fLutCtrRow = iLutRows / 2.0 - 0.5
        # endif

        fLutCtrCol = _fLutCenterCol
        if not isinstance(fLutCtrCol, float):
            fLutCtrCol = iLutCols / 2.0 - 0.5
        # endif

        # LUT center refers to the principle point
        self._tLutCenterRC: tuple[float, float] = (fLutCtrRow, fLutCtrCol)

        aValidIdx = np.argwhere(aLen > 1e-6)
        aValidRelIdx = aValidIdx - np.array([[fLutCtrRow, fLutCtrRow]])
        aValidIdxRad = np.linalg.norm(aValidRelIdx, axis=1)
        fLutPixRadMax = np.max(aValidIdxRad).item()
        fImgPixRadMax = self.LutToImgPixelValue(fLutPixRadMax)

        fPixCols = (iLutCols - 2 * self._iLutBorderPixel) / self._iLutSuperSampling
        if math.fmod(fPixCols, 1.0) > 1e-3:
            raise RuntimeError(
                f"Inconsistent LUT column size ({iLutCols}) w.r.t. LUT border pixel ({self._iLutBorderPixel}) "
                f"and super sampling ({self._iLutSuperSampling})"
            )
        # endif

        fPixRows = (iLutRows - 2 * self._iLutBorderPixel) / self._iLutSuperSampling
        if math.fmod(fPixRows, 1.0) > 1e-3:
            raise RuntimeError(
                f"Inconsistent LUT row size ({iLutRows}) w.r.t. LUT border pixel ({self._iLutBorderPixel}) "
                f"and super sampling ({self._iLutSuperSampling})"
            )
        # endif

        # Image pixel count
        self._tImgPixCntRC: tuple[int, int] = (int(round(fPixRows)), int(round(fPixCols)))

        # Principle point position in image units without LUT border
        self._tImgCtrRC: tuple[float, float] = self.LutToImgPixel(self._tLutCenterRC)

        # Use the pixel to the top/left of the actual center
        # as the center pixel that maps to a render pixel.
        # The remaining offset can be adjusted by a camera shift.
        self._tImgCtrPixRC: tuple[int, int] = tuple([int(math.floor(x)) for x in self._tImgCtrRC])

        # Assume -Z-axis points into the view direction of the camera
        aRadDir = self._imgLut[:, :, 0:2]
        aRadLen = np.linalg.norm(aRadDir, axis=2)
        aMask2 = aRadLen > 1e-6
        aMask3 = np.expand_dims(aMask2, axis=2)
        aRadDirNorm = np.divide(aRadDir, np.expand_dims(aRadLen, axis=2), where=aMask3)

        aRadZ = -self._imgLut[:, :, 2]
        aRadAngle = np.zeros(aRadLen.shape)
        np.arctan2(aRadLen, aRadZ, out=aRadAngle, where=aMask2)
        aRadAngle_deg = np.degrees(aRadAngle)
        self._fRadAngleMax_deg = math.ceil(np.max(aRadAngle_deg, initial=0.0, where=aMask2))

        aRadAngleDir = np.zeros(aRadDirNorm.shape)
        np.multiply(aRadDirNorm, np.expand_dims(aRadAngle, axis=2), out=aRadAngleDir, where=aMask3)

        aRadAngleDir_deg = np.degrees(aRadAngleDir)

        self._tLutAngleRangeX_deg = (
            np.min(aRadAngleDir_deg[:, :, 0], initial=1000.0, where=aMask2),
            np.max(aRadAngleDir_deg[:, :, 0], initial=-1000.0, where=aMask2),
        )

        self._tLutAngleRangeY_deg = (
            np.min(aRadAngleDir_deg[:, :, 1], initial=1000.0, where=aMask2),
            np.max(aRadAngleDir_deg[:, :, 1], initial=-1000.0, where=aMask2),
        )

        # Index to the central render pixel in row and column.
        # This calculation ensures that the effective image is inside the
        # rendered circle of the generating fisheye camera.
        self._iRenderCtrPix: int = int(math.ceil(fImgPixRadMax + 1.0))

        # Total number pixels along rows and columns. Always odd.
        self._iRenderPixCnt: int = 2 * self._iRenderCtrPix + 1

        self._fRenderFoV_deg: float = 2.0 * self._fRadAngleMax_deg
        self._fRenderPixPerDeg: float = self._iRenderPixCnt / self._fRenderFoV_deg

        fImgLutBorderOffset: float = self._fImgPerLutPix * self._iLutBorderPixel

        self._tRenderImgPixRangeCol: tuple[int, int] = (
            self._iRenderCtrPix - self._tImgCtrPixRC[1],
            self._iRenderCtrPix + self._tImgPixCntRC[1] - self._tImgCtrPixRC[1] - 1,
        )

        self._tRenderImgPixRangeRow: tuple[int, int] = (
            self._iRenderCtrPix - self._tImgCtrPixRC[0],
            self._iRenderCtrPix + self._tImgPixCntRC[0] - self._tImgCtrPixRC[0] - 1,
        )

        self._tRenderLutAngleRangeX_deg: tuple[float, float] = (
            -(self._tImgCtrPixRC[1] + fImgLutBorderOffset) / self._fRenderPixPerDeg,
            (self._tImgPixCntRC[1] - self._tImgCtrPixRC[1] - 1 + fImgLutBorderOffset) / self._fRenderPixPerDeg,
        )

        self._tRenderLutAngleRangeY_deg: tuple[float, float] = (
            -(self._tImgPixCntRC[0] - self._tImgCtrPixRC[0] - 1 + fImgLutBorderOffset) / self._fRenderPixPerDeg,
            (self._tImgCtrPixRC[0] + fImgLutBorderOffset) / self._fRenderPixPerDeg,
        )

        # Camera shift values for fisheye equidistant
        self._tCamShiftXY = (
            (self._tImgCtrPixRC[1] - self._tImgCtrRC[1]) / self._iRenderPixCnt,
            (self._tImgCtrRC[0] - self._tImgCtrPixRC[0]) / self._iRenderPixCnt,
        )

        # It seems we need to add 0.5 Pixel when calculating the crop, to avoid numerical instabilities.
        # As far as I can see Blender calculates the integer pixel position by truncating the fractional pixel value.
        self._xRenderCrop: CRenderCrop = CRenderCrop(
            fLeft=(self._tRenderImgPixRangeCol[0] + 0.5) / self._iRenderPixCnt,
            fRight=(self._tRenderImgPixRangeCol[1] + 1 + 0.5) / self._iRenderPixCnt,
            fBottom=(self._iRenderPixCnt - (self._tRenderImgPixRangeRow[1] + 1) + 0.5) / self._iRenderPixCnt,
            fTop=(self._iRenderPixCnt - self._tRenderImgPixRangeRow[0] + 0.5) / self._iRenderPixCnt,
        )

        # fLeftPix = self._xRenderCrop.fLeft * self._iRenderPixCnt
        # fRightPix = self._xRenderCrop.fRight * self._iRenderPixCnt

        # print(f"{fLeftPix} -> {fRightPix}")

    # enddef

    # ##########################################################################################################
    def GetLutImgPixelRadii(self) -> np.ndarray:
        aLutCtr = np.array(self._tImgCtrRC)

        aLutIdx = np.argwhere(self._aLutMask[:, :, 0])
        aLutRelIdx = aLutIdx - aLutCtr[np.newaxis, :]

        aLutImgRad = np.linalg.norm(aLutRelIdx, axis=1) * self._fImgPerLutPix

        aLutImgRad2d = np.zeros(self._aLutMask.shape[0:2])
        aLutImgRad2d[aLutIdx[:, 0], aLutIdx[:, 1]] = aLutImgRad

        return aLutImgRad2d

    # enddef

    # ##########################################################################################################
    def GetLutAngles_rad(self) -> np.ndarray:
        aRadDir = self._imgLut[:, :, 0:2]
        aRadLen = np.linalg.norm(aRadDir, axis=2)

        aRadZ = -self._imgLut[:, :, 2]
        aRadTheta = np.zeros_like(aRadLen)
        np.arctan2(aRadLen, aRadZ, out=aRadTheta, where=self._aLutMask[:, :, 0])

        aRadPhi = np.zeros_like(aRadLen)
        np.arctan2(aRadDir[:, :, 1], aRadDir[:, :, 0], out=aRadPhi, where=self._aLutMask[:, :, 0])

        aAngles = np.concatenate((aRadTheta[:, :, np.newaxis], aRadPhi[:, :, np.newaxis]), axis=2)

        return aAngles

    # enddef

    # ##########################################################################################################
    def RayDirsToPixelsRC(
        self, _aTestDirs: np.ndarray, *, _bNormalize: bool = False
    ) -> tuple[list[list[float]], list[bool]]:
        """Map ray directions to 2D-pixel image positions in pixel-centered CV-coordinate system,
        with origin at top-left, x-axis pointing right, y-axis pointing down.
        IMPORTANT: Pixel coordinates are pixel centered,
        e.g. pixel (0,0) is the center of the top-left pixel and
        (-0.5, -0.5) is the top-left corner of the top-left pixel.

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
            Tuple of list of 2D (row, column) pixel positions
            and list of bool flags, whether projection is valid.
            IMPORTANT: Pixel coordinates are pixel centered,
            e.g. pixel (0,0) is the center of the top-left pixel and
            (-0.5, -0.5) is the top-left corner of the top-left pixel.
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

        aRayDirs: np.ndarray = self._imgLut[:, :, 0:3]
        iRowCnt, iColCnt, _ = aRayDirs.shape
        iPixCnt = iRowCnt * iColCnt

        aRayDirsFlat = aRayDirs.reshape(iPixCnt, 3)

        iTestDirCnt = aTestDirs.shape[0]
        if iTestDirCnt < 4:
            # original code: brute force computation of distances to find nearest ray
            aTestDirsEx = np.expand_dims(aTestDirs, axis=1)
            aRayDirsFlatEx = np.expand_dims(aRayDirsFlat, axis=0)

            aSub = aRayDirsFlatEx - aTestDirsEx
            aDist = np.linalg.norm(aSub, axis=2)
            aMinIdx = np.argmin(aDist, axis=1)
        else:
            # speed-up if many points need to be projected:
            # use kd-tree to exclude huge parts of the image from the brute force computation
            iPixelCnt = aRayDirsFlat.shape[0]
            xKdTree = KDTree(aRayDirsFlat, leafsize=iPixelCnt // 50)
            _, aMinIdx = xKdTree.query(aTestDirs)
        # endif

        lPixPosRC: list[list[float]] = []
        lPixValid: list[bool] = []

        for iTestIdx, iMinIdx in enumerate(aMinIdx):
            bValid = False
            lPosRC = [0.0, 0.0]

            iRowIdx = iMinIdx // iColCnt
            iColIdx = iMinIdx % iColCnt
            # print(f"{iRowIdx}, {iColIdx}")

            # Dummy loop to enable jumping over remaining code block
            # for invalid points.
            while True:
                aOrig = aRayDirs[iRowIdx, iColIdx]
                # Test whether origin is valid
                if np.linalg.norm(aOrig) < 0.9:
                    break
                # endif

                # #####################################################
                # Linear Interpolation
                if iColIdx >= iColCnt - 1:
                    aPos = aRayDirs[iRowIdx, iColIdx - 1]
                    if np.linalg.norm(aPos) < 0.9:
                        break
                    # endif
                    aX = aOrig - aPos

                else:
                    aPos = aRayDirs[iRowIdx, iColIdx + 1]
                    if np.linalg.norm(aPos) < 0.9:
                        break
                    # endif
                    aX = aPos - aOrig
                # endif

                if iRowIdx >= iRowCnt - 1:
                    aPos = aRayDirs[iRowIdx - 1, iColIdx]
                    if np.linalg.norm(aPos) < 0.9:
                        break
                    # endif
                    aY = aOrig - aPos

                else:
                    aPos = aRayDirs[iRowIdx + 1, iColIdx]
                    if np.linalg.norm(aPos) < 0.9:
                        break
                    # endif
                    aY = aPos - aOrig
                # endif

                aTest = aTestDirs[iTestIdx]

                fXlen = np.linalg.norm(aX)
                fYlen = np.linalg.norm(aY)

                aDelta = aTest - aOrig

                # print(f"aDelta, aX, fXlen: {aDelta}, {aX}, {fXlen}")
                # print(f"aDelta, aY, fYlen: {aDelta}, {aY}, {fYlen}")
                if fXlen == 0:
                    fDeltaPixX = 0
                else:
                    fDeltaPixX = np.dot(aDelta, aX) / (fXlen * fXlen)
                if fYlen == 0:
                    fDeltaPixY = 0
                else:
                    fDeltaPixY = np.dot(aDelta, aY) / (fYlen * fYlen)
                # #####################################################

                lPosRC = [float(iRowIdx + fDeltaPixY), float(iColIdx + fDeltaPixX)]
                lPosRC = list(self.LutToImgPixel(lPosRC))

                bValid: bool = (
                    lPosRC[0] * self._iLutSuperSampling + self._iLutBorderPixel
                    >= -0.5 * (1 / self._iLutSuperSampling)
                    and lPosRC[0] * self._iLutSuperSampling + self._iLutBorderPixel
                    <= iRowCnt
                    and lPosRC[1] * self._iLutSuperSampling + self._iLutBorderPixel
                    >= -0.5 * (1 / self._iLutSuperSampling)
                    and lPosRC[1] * self._iLutSuperSampling + self._iLutBorderPixel
                    <= iColCnt
                )

                if bValid:
                    lPosRCRay = self._imgLut[
                        max(
                            0,
                            int(
                                np.floor(
                                    lPosRC[0] * self._iLutSuperSampling
                                    + self._iLutBorderPixel
                                )
                            ),
                        ),
                        max(
                            0,
                            int(
                                np.floor(
                                    lPosRC[1] * self._iLutSuperSampling
                                    + self._iLutBorderPixel
                                )
                            ),
                        ),
                    ]
                    if lPosRCRay[0] == 0 and lPosRCRay[1] == 0 and lPosRCRay[2] == 0:
                        bValid = False

                break
            # endwhile dummy

            lPixPosRC.append(lPosRC)
            lPixValid.append(bValid)
        # endfor

        return (lPixPosRC, lPixValid)

    # enddef

    # ##########################################################################################################
    def _AddVizRay(
        self,
        *,
        _lVizRays: list,
        _aPrevRay: np.ndarray,
        _aNewRay: np.ndarray,
        _fMaxAngle_deg: float,
        _bForce: bool = False,
    ) -> np.ndarray:
        assertion.IsTrue(len(_aNewRay.shape) == 1, "Given ray array has invalid shape")

        if _bForce is True:
            _lVizRays.append(_aNewRay)
            return _aNewRay
        else:
            fDot = round(np.dot(_aPrevRay, _aNewRay), 5)
            fAngle_deg = math.degrees(math.acos(fDot))
            if fAngle_deg > _fMaxAngle_deg:
                _lVizRays.append(_aNewRay)
                return _aNewRay
            else:
                return _aPrevRay
            # endif
        # endif

    # enddef

    # ##########################################################################################################
    def _AddVizRayList(
        self,
        *,
        _lVizRays: list,
        _aPrevRay: np.ndarray,
        _aNewRayList: np.ndarray,
        _fMaxAngle_deg: float,
        _bForceLast: bool = False,
    ) -> np.ndarray:
        assertion.IsTrue(len(_aNewRayList.shape) == 2, "Given ray list has invalid shape")

        aPrevRay = _aPrevRay
        for aRay in _aNewRayList:
            aPrevRay = self._AddVizRay(
                _lVizRays=_lVizRays, _aPrevRay=aPrevRay, _aNewRay=aRay, _fMaxAngle_deg=_fMaxAngle_deg
            )
        # endfor

        if _bForceLast is True:
            aPrevRay = self._AddVizRay(
                _lVizRays=_lVizRays,
                _aPrevRay=aPrevRay,
                _aNewRay=_aNewRayList[-1],
                _fMaxAngle_deg=_fMaxAngle_deg,
                _bForce=True,
            )
        # endif

        return aPrevRay

    # enddef

    # ##########################################################################################################
    def GetFrustumMesh(
        self, *, _fRayLen: float, _fMaxEdgeAngle_deg: float = 1.0, _fSurfAngleStep_deg: float = 10.0
    ) -> CMeshData:
        lVex: list[tuple[float, float, float]] = [(0.0, 0.0, 0.0), (0.0, 0.0, -_fRayLen)]

        aRayDir = self._imgLut[:, :, 0:3]
        aRayLen = np.linalg.norm(aRayDir, axis=2)
        iRayRows, iRayCols = aRayLen.shape

        # Walk around edge of LUT
        # Get indices of first row that has valid ray directions
        iTopRowIdx: int = 0
        aIdx: np.ndarray = np.array([])
        for iRowIdx in range(iRayRows):
            aIdx = np.argwhere(aRayLen[iRowIdx] > 0.5)
            if aIdx.shape[0] > 0:
                iTopRowIdx = iRowIdx
                break
            # endif
        # endwhile

        if aIdx.shape[0] == 0:
            raise RuntimeError("LUT has no valid ray directions")
        # endif

        fMaxAngle_deg: float = _fMaxEdgeAngle_deg
        aPrevRay: np.ndarray = aRayDir[iTopRowIdx][aIdx[0].item()]
        lVizRays: list = [aPrevRay]

        aDirs = aRayDir[iTopRowIdx][aIdx][:, 0]
        aPrevRay = self._AddVizRayList(
            _lVizRays=lVizRays, _aPrevRay=aPrevRay, _aNewRayList=aDirs, _fMaxAngle_deg=fMaxAngle_deg, _bForceLast=True
        )
        # lVex.extend([tuple(x.tolist()) for x in aDirs])

        # Find last valid LUT row
        iBotRowIdx: int = iRayRows - 1
        for iRowIdx in range(iTopRowIdx + 1, iRayRows):
            aIdx = np.argwhere(aRayLen[iRowIdx] > 0.5)
            if aIdx.shape[0] == 0:
                iBotRowIdx = iRowIdx - 1
                break
            # endif
        # endfor

        if iTopRowIdx == iBotRowIdx:
            raise RuntimeError("LUT has only a single valid row of ray directions")
        # endif

        # list of first columns starting from second valid row
        lFirstCols: list = []

        # loop over the next rows apart from the last valid row
        for iRowIdx in range(iTopRowIdx + 1, iBotRowIdx):
            aIdx = np.argwhere(aRayLen[iRowIdx] > 0.5)
            lFirstCols.append(aIdx[0].item())
            iColIdx: int = int(aIdx[-1].item())
            aPrevRay = self._AddVizRay(
                _lVizRays=lVizRays,
                _aPrevRay=aPrevRay,
                _aNewRay=aRayDir[iRowIdx, iColIdx, :],
                _fMaxAngle_deg=fMaxAngle_deg,
            )
            # lVex.append(tuple((aRayDir[iRowIdx, iColIdx, :] * _fRayLen).tolist()))
        # endfor

        # Process bottom row
        aIdx = np.argwhere(aRayLen[iBotRowIdx] > 0.5)
        aPrevRay = aRayDir[iBotRowIdx][aIdx[-1].item()]
        lVizRays.append(aPrevRay)

        aDirs = aRayDir[iBotRowIdx][aIdx[::-1]][:, 0]
        aPrevRay = self._AddVizRayList(
            _lVizRays=lVizRays, _aPrevRay=aPrevRay, _aNewRayList=aDirs, _fMaxAngle_deg=fMaxAngle_deg, _bForceLast=True
        )
        # lVex.extend([tuple(x.tolist()) for x in aDirs])

        # Now go back up the first row
        iRowIdx = iBotRowIdx - 1
        for iColIdx in lFirstCols[::-1]:
            aPrevRay = self._AddVizRay(
                _lVizRays=lVizRays,
                _aPrevRay=aPrevRay,
                _aNewRay=aRayDir[iRowIdx, iColIdx, :],
                _fMaxAngle_deg=fMaxAngle_deg,
            )
            # lVex.append(tuple((aRayDir[iRowIdx, iColIdx, :] * _fRayLen).tolist()))
            iRowIdx -= 1
        # endfor

        iEdgeRayCnt = len(lVizRays)
        lVex.extend([tuple((x * _fRayLen).tolist()) for x in lVizRays])

        ###############################################################
        # Eval vertices for front surface by rotating all rays to the
        # optical axis in a number of steps.
        fAngleStep_deg: float = _fSurfAngleStep_deg
        fAngleStep: float = math.radians(fAngleStep_deg)

        aVizRays = np.array(lVizRays)
        aX = np.array([[0.0, 0.0, -1.0]])

        aZ: np.ndarray = np.cross(aX, aVizRays)
        aZlen = np.linalg.norm(aZ, axis=1)
        aZ = np.divide(aZ, aZlen[:, np.newaxis])

        aY: np.ndarray = np.cross(aZ, aX)
        # aYlen = np.linalg.norm(aY, axis=1)
        # aY = np.divide(aY, aYlen[:, np.newaxis])

        aAngle = np.arccos(np.dot(aVizRays, aX.T))
        fAngleMin = np.min(aAngle)

        iAngleStepCnt: int = int(math.ceil(fAngleMin / fAngleStep))
        aAngleStepEff: np.ndarray = aAngle / iAngleStepCnt

        for iAngleStep in range(1, iAngleStepCnt):
            aNewAngle = aAngle - iAngleStep * aAngleStepEff
            aSin = np.sin(aNewAngle)
            aCos = np.cos(aNewAngle)

            aNewRay = aCos * aX + aSin * aY
            lVex.extend([tuple((x * _fRayLen).tolist()) for x in aNewRay])
        # endfor

        ###############################################################
        lFaces = []
        # iVexCnt = len(lVex)
        iFirstIdx = 2

        # ################################################
        # Create the central faces
        iStartIdx = iFirstIdx + (iAngleStepCnt - 1) * iEdgeRayCnt
        iCnt = iEdgeRayCnt - 1
        for iVexIdx in range(iStartIdx, iStartIdx + iCnt):
            lFaces.append([1, iVexIdx, iVexIdx + 1])
        # endfor

        # Connect the last to the first
        lFaces.append([1, iStartIdx + iCnt, iStartIdx])

        # ################################################
        # Create the outer faces
        iStartIdx = iFirstIdx
        iCnt = iEdgeRayCnt - 1
        for iVexIdx in range(iStartIdx, iStartIdx + iCnt):
            lFaces.append([0, iVexIdx, iVexIdx + 1])
        # endfor

        # Connect the last to the first
        lFaces.append([0, iStartIdx + iCnt, iStartIdx])

        # ################################################
        # Create a face ring
        for iAngleStep in range(iAngleStepCnt - 1):
            iStartIdx = iFirstIdx + iAngleStep * iEdgeRayCnt
            iCnt = iEdgeRayCnt - 1
            for iVexIdx in range(iStartIdx, iStartIdx + iCnt):
                lFaces.append([iVexIdx, iVexIdx + 1, iVexIdx + iEdgeRayCnt + 1, iVexIdx + iEdgeRayCnt])
            # endfor
            lFaces.append(
                [iStartIdx + iEdgeRayCnt - 1, iStartIdx, iStartIdx + iEdgeRayCnt, iStartIdx + 2 * iEdgeRayCnt - 1]
            )
        # endfor

        return CMeshData(lVex=lVex, lEdges=[], lFaces=lFaces)

    # enddef


# endclass
