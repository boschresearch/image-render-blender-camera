#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \obj\camera.py
# Created Date: Thursday, June 10th 2021, 7:50:16 am
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
import numpy as np
from typing import Union
from pathlib import Path

from anybase import config, convert
from anybase.cls_any_error import CAnyError_Message

from .cls_cameraview_lut import CCameraViewLut
from .cls_cameraview_pinhole import CCameraViewPinhole
from .cls_cameraview_pano_equidist import CCameraViewPanoEquidist
from .cls_cameraview_pano_equirect import CCameraViewPanoEquirect
from .cls_cameraview_pano_poly import CCameraViewPanoPoly


##################################################################################
# Create a camera view class instance from AnyCam data (>= v1.2)
def CreateCameraView(_dicAnyCam: dict, *, _xCamDataPath: Union[str, Path, tuple, None] = None, bDoThrow: bool = True):

    if _dicAnyCam is None:
        if bDoThrow:
            raise Exception("No AnyCam data given")
        else:
            return None
        # endif
    # endif

    dicRes = config.CheckConfigType(_dicAnyCam, "/anycam/camera/*:1.2")
    if not dicRes.get("bOK"):
        if bDoThrow:
            raise Exception("Invalid AnyCam data: {0}".format(dicRes.get("sMsg")))
        else:
            return None
        # endif
    # endif

    lCamType = dicRes.get("lCfgType")[2:]

    xView = None
    if lCamType[0] == "pin":
        xView = CCameraViewPinhole()
        xView.Init(
            lPixCnt=[_dicAnyCam.get("iSenResX"), _dicAnyCam.get("iSenResY")],
            fPixSize_um=_dicAnyCam.get("fPixSize_um"),
            fFovMax_deg=_dicAnyCam.get("fFovMax_deg"),
            lFov_deg=_dicAnyCam.get("lFov_deg"),
            lFovRange_deg=_dicAnyCam.get("lFovRange_deg"),
            bEnsureSquarePixel=_dicAnyCam.get("bEnsureSquarePixel"),
            lAxes=_dicAnyCam.get("lAxes"),
            lOrig_m=_dicAnyCam.get("lOrigin"),
        )

    elif lCamType[0] == "pano" and lCamType[1] == "equidist":
        xView = CCameraViewPanoEquidist()
        xView.Init(
            lPixCnt=[_dicAnyCam.get("iSenResX"), _dicAnyCam.get("iSenResY")],
            fPixSize_um=_dicAnyCam.get("fPixSize_um"),
            fFovMax_deg=_dicAnyCam.get("fFovMax_deg"),
            lFov_deg=_dicAnyCam.get("lFov_deg"),
            lFovRange_deg=_dicAnyCam.get("lFovRange_deg"),
            bEnsureSquarePixel=_dicAnyCam.get("bEnsureSquarePixel"),
            lAxes=_dicAnyCam.get("lAxes"),
            lOrig_m=_dicAnyCam.get("lOrigin"),
        )

    elif lCamType[0] == "pano" and lCamType[1] == "equirect":
        xView = CCameraViewPanoEquirect()
        xView.Init(
            lPixCnt=[_dicAnyCam.get("iSenResX"), _dicAnyCam.get("iSenResY")],
            fPixSize_um=_dicAnyCam.get("fPixSize_um"),
            fFovMax_deg=_dicAnyCam.get("fFovMax_deg"),
            lFov_deg=_dicAnyCam.get("lFov_deg"),
            lFovRange_deg=_dicAnyCam.get("lFovRange_deg"),
            bEnsureSquarePixel=_dicAnyCam.get("bEnsureSquarePixel"),
            lAxes=_dicAnyCam.get("lAxes"),
            lOrig_m=_dicAnyCam.get("lOrigin"),
        )

    elif lCamType[0] == "pano" and lCamType[1] == "poly":
        xView = CCameraViewPanoPoly()
        xView.Init(
            lPixCnt=[_dicAnyCam.get("iSenResX"), _dicAnyCam.get("iSenResY")],
            fPixSize_um=_dicAnyCam.get("fPixSize_um"),
            fFovMax_deg=_dicAnyCam.get("fFovMax_deg"),
            lPolyCoef_rad_mm=_dicAnyCam.get("lPolyCoef_rad_mm"),
            lCenterOffsetXY_mm=_dicAnyCam.get("lCenterOffsetXY_mm"),
            lAxes=_dicAnyCam.get("lAxes"),
            lOrig_m=_dicAnyCam.get("lOrigin"),
        )

    elif lCamType[0] == "lut" and lCamType[1] == "std":
        dicACEx: dict = _dicAnyCam.get("mEx")
        if not isinstance(dicACEx, dict):
            raise RuntimeError("AnyCam data for LUT camera does not have a 'mEx' element")
        # endif
        dicLutData: dict = dicACEx.get("mLutData")
        if not isinstance(dicLutData, dict):
            raise RuntimeError("AnyCamEx data LUT camera does not have a 'mLutData' element")
        # endif
        try:
            sImageName: str = convert.DictElementToString(dicLutData, "sImageName")
            sFilePath: str = convert.DictElementToString(dicLutData, "sFilePath", sDefault=None, bDoRaise=False)
            iLutBorderPixel: int = convert.DictElementToInt(dicLutData, "iLutBorderPixel")
            iLutSuperSampling: int = convert.DictElementToInt(dicLutData, "iLutSuperSampling")
            lLutCenterRC: list = convert.DictElementToFloatList(dicLutData, "lLutCenterRC", iLen=2)
        except Exception as xEx:
            raise CAnyError_Message(sMsg="AnyCamEx LUT data block is missing an element", xChildEx=xEx)
        # endtry

        xFilePath = None
        if sFilePath is not None:
            if _xCamDataPath is not None:
                pathFile = Path(sFilePath)
                if not pathFile.is_absolute():
                    xFilePath = (_xCamDataPath, sFilePath)
                else:
                    xFilePath = sFilePath
                # endif
            else:
                xFilePath = sFilePath
            # endif
        # endif

        # if there is an image name and we are in a Blender context, then load the LUT image from Blender
        imgLut: np.ndarray = None
        if sImageName is not None:
            try:
                # Try to import '_bpy' which only works in an actual Blender context.
                import _bpy

                bHasBpy = True
            except Exception:
                bHasBpy = False
            # endtry

            if bHasBpy is True:
                from .camera_lut import GetBlenderLutImage

                imgLut = GetBlenderLutImage(sImageName)
            # endif
        # endif

        xView = CCameraViewLut()
        xView.Init(
            aImage=imgLut,
            xFilePath=xFilePath,
            iLutBorderPixel=iLutBorderPixel,
            iLutSuperSampling=iLutSuperSampling,
            lLutCenterRC=lLutCenterRC,
            lAxes=_dicAnyCam.get("lAxes"),
            lOrig_m=_dicAnyCam.get("lOrigin"),
        )

    else:
        if bDoThrow:
            raise Exception("Unsupported camera type: {0}".format("/".join(lCamType)))
        # endif
    # endif

    return xView


# enddef
