#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /camera_pano.py
# Created Date: Thursday, October 22nd 2020, 2:51:36 pm
# Author: Christian Perwass
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


import bpy

# import bmesh
import math

# import mathutils
import pyjson5 as json
from pathlib import Path

# from . import util
from .. import ops
from ..mesh import solids
from anybase import config, convert
from anybase import path as anypath

import anyblend
from anyblend.mesh.types import CMeshData

from anybase.cls_anyexcept import CAnyExcept
from anybase.cls_any_error import CAnyError_Message

from .cls_cameraview_pano_equidist import CCameraViewPanoEquidist
from .cls_cameraview_pano_equirect import CCameraViewPanoEquirect
from .cls_cameraview_pano_poly import CCameraViewPanoPoly


#####################################################################
# Create the camera name
def CreateName(_sName):
    return "Cam.Pano.{0}".format(_sName)


# enddef


#####################################################################
# Create Light Field Trace Cameras
def Create(
    _sName,
    _dicCamera,
    bOverwrite=False,
    fScale=1.0,
    bCreateFrustum=False,
    dicAnyCamEx=None,
):
    # Calculate Blender Units per Millimeter
    fBUperMM = fScale * 1e-3 / bpy.context.scene.unit_settings.scale_length

    #####################################################
    # Get camera data
    dicSensor = _dicCamera.get("dicSensor")
    dicPano = _dicCamera.get("dicPano")
    iEnsureSquarePixel = _dicCamera.get("iEnsureSquarePixel", 0)

    #####################################################
    # Create camera empty, that acts as origin for whole camera system
    sCamName = CreateName(_sName)

    clnMain = bpy.data.collections.get("AnyCam")
    if clnMain is None:
        clnMain = bpy.data.collections.new("AnyCam")
        bpy.context.scene.collection.children.link(clnMain)
    # endif

    objCamOrig = bpy.data.objects.get(sCamName)
    if objCamOrig is not None:
        if bOverwrite is True:
            ops.DeleteObjectHierarchy(objCamOrig)
            objCamOrig = None
        else:
            return {
                "bResult": False,
                "objCam": objCamOrig,
                "sMsg": "Camera with selected name already exists.",
            }
        # endif
    # endif

    #####################################################

    # objCamOrig = bpy.data.objects.new(sCamName, None)
    # objCamOrig.location = (0, 0, 0)
    # objCamOrig.empty_display_size = 1
    # objCamOrig.empty_display_type = "PLAIN_AXES"
    # cnMain.objects.link(objCamOrig)

    #####################################################
    # Create render pano camera

    camX = bpy.data.cameras.get(sCamName)
    if camX is not None:
        bpy.data.cameras.remove(camX)
        camX = None
    # endif

    camX: bpy.types.Camera = bpy.data.cameras.new(sCamName)
    objCam: bpy.types.Object = bpy.data.objects.new(name=sCamName, object_data=camX)

    vlMain = bpy.context.view_layer
    clnMain.objects.link(objCam)
    vlMain.objects.active = objCam
    objCam.select_set(True)

    dicFovRange = dicPano.get("mFovRange")
    if dicFovRange is not None:
        lFovH = dicFovRange.get("lHorizontal")
        if lFovH is None:
            raise CAnyExcept("No horizontal field-of-view given")
        # endif
        lFovV = dicFovRange.get("lVertical")
        if lFovV is None:
            raise CAnyExcept("No vertical field-of-view given")
        # endif
        lFovRange = [lFovH, lFovV]
    else:
        lFovRange = None
    # endif

    # Render Crop: left, right, bottom, top
    lCrop = None
    tShift = (0.0, 0.0)
    bEnsureSquarePixel: bool = iEnsureSquarePixel != 0

    dicPanoType = config.SplitDti(dicPano.get("sDTI"))
    sPanoType = dicPanoType.get("lType")[4]
    if sPanoType == "equidist":
        # an equidistant pano camera can only have one FoV in Blender.
        # We also need to make the image square and use the render crop
        # to adjust to the given sensor resolution.

        xView = CCameraViewPanoEquidist()
        xView.Init(
            lPixCnt=[dicSensor.get("iPixCntX"), dicSensor.get("iPixCntY")],
            fPixSize_um=dicSensor.get("fPixSize"),
            fFovMax_deg=dicPano.get("fFovMax_deg"),
            lFov_deg=dicPano.get("lFov_deg"),
            lFovRange_deg=lFovRange,
            bEnsureSquarePixel=bEnsureSquarePixel,
        )

        if hasattr(camX, "cycles"):
            camX.cycles.panorama_type = "FISHEYE_EQUIDISTANT"
            camX.cycles.fisheye_fov = math.radians(xView.fFovMax_deg)
        else:
            camX.panorama_type = "FISHEYE_EQUIDISTANT"
            camX.fisheye_fov = math.radians(xView.fFovMax_deg)
        # endif

        # this value has no effect on the rendering, only on the way
        # Blender displays the camera
        camX.lens = xView.fSenSizeMax_mm / 2.0

        lCrop = xView.EvalCrop()

        iRenderResX = xView.iPixCntMaxX
        iRenderResY = xView.iPixCntMaxY
        fAspectX = xView.fAspectX
        fAspectY = xView.fAspectY

    elif sPanoType == "equirect":
        # an equidistant pano camera can only have one FoV in Blender.
        # We also need to make the image square and use the render crop
        # to adjust to the given sensor resolution.

        xView = CCameraViewPanoEquirect()
        xView.Init(
            lPixCnt=[dicSensor.get("iPixCntX"), dicSensor.get("iPixCntY")],
            fPixSize_um=dicSensor.get("fPixSize"),
            fFovMax_deg=dicPano.get("fFovMax_deg"),
            lFov_deg=dicPano.get("lFov_deg"),
            lFovRange_deg=lFovRange,
            bEnsureSquarePixel=bEnsureSquarePixel,
        )

        if hasattr(camX, "cycles"):
            camX.cycles.panorama_type = "EQUIRECTANGULAR"
            camX.cycles.longitude_min = math.radians(xView.lFovRange_deg[0][0])
            camX.cycles.longitude_max = math.radians(xView.lFovRange_deg[0][1])
            camX.cycles.latitude_min = math.radians(xView.lFovRange_deg[1][0])
            camX.cycles.latitude_max = math.radians(xView.lFovRange_deg[1][1])
        else:
            camX.panorama_type = "EQUIRECTANGULAR"
            camX.longitude_min = math.radians(xView.lFovRange_deg[0][0])
            camX.longitude_max = math.radians(xView.lFovRange_deg[0][1])
            camX.latitude_min = math.radians(xView.lFovRange_deg[1][0])
            camX.latitude_max = math.radians(xView.lFovRange_deg[1][1])
        # endif

        # this value has no effect on the rendering, only on the way
        # Blender displays the camera
        camX.lens = xView.fSenSizeMax_mm / 2.0

        lCrop = None
        iRenderResX = None
        iRenderResY = None
        fAspectX = xView.fAspectX
        fAspectY = xView.fAspectY

    elif sPanoType == "poly":
        # A fisheye camera with polynomial distortion
        xView = CCameraViewPanoPoly()

        sLutConfigFile = convert.DictElementToString(dicPano, "sLutConfigFile", sDefault=None, bDoRaise=False)

        if sLutConfigFile is None:
            xView.Init(
                lPixCnt=[
                    convert.DictElementToInt(dicPano, "iPixCntX"), 
                    convert.DictElementToInt(dicPano, "iPixCntY")
                ],
                fPixSize_um=convert.DictElementToFloat(dicSensor, "fPixSize"),
                fFovMax_deg=convert.DictElementToFloat(dicPano, "fFovMax_deg", fDefault=None, bDoRaise=False),
                lPolyCoef_rad_mm=convert.DictElementToFloatList(dicPano, "lPolyCoef_rad_mm"),
                lCenterOffsetXY_mm=convert.DictElementToFloatList(dicPano, "lCenterOffsetXY_mm"),
            )

        else:
            pathLutConfigFile = Path(sLutConfigFile)
            if not pathLutConfigFile.is_absolute():
                dicPrjVars: dict = dicPano.get("__locals__")
                if dicPrjVars is None:
                    raise RuntimeError("Project configuration does not contain automatically added path information")
                # endif

                sPrjCfgPath: str = dicPrjVars.get("path")
                if sPrjCfgPath is None:
                    raise RuntimeError("Project configuration does not contain automatically added path information")
                # endif

                pathLutConfigFile = anypath.MakeNormPath((sPrjCfgPath, pathLutConfigFile))
            # endif

            fMaxPolyFitResidual: float | None = convert.DictElementToFloat(dicPano, "fMaxPolyFitResidual", fDefault=0.02, bDoRaise=False)

            try:
                dicLut = config.Load(pathLutConfigFile, sDTI="/anycam/db/project/lut/std:1.0", bAddPathVars=True)
            except Exception as xEx:
                raise CAnyError_Message(
                    sMsg=f"Error loading LUT configuration file: {(pathLutConfigFile.as_posix())}", xChildEx=xEx
                )
            # endtry

            pathLutFile = Path(dicLut.get("sLutFile"))
            if not pathLutFile.is_absolute():
                pathLutFile = anypath.MakeNormPath((pathLutConfigFile.parent, pathLutFile))
            # endif

            if not pathLutFile.exists():
                raise RuntimeError(f"LUT file not found at: {(pathLutFile.as_posix())}")
            # endif

            iLutBorderPixel: int = convert.DictElementToInt(dicLut, "iLutBorderPixel", iDefault=0)
            iLutSuperSampling: int = convert.DictElementToInt(dicLut, "iLutSuperSampling", iDefault=1)
            fLutCenterRow: float = convert.DictElementToFloat(dicLut, "fLutCenterRow", fDefault=None, bDoRaise=False)
            fLutCenterCol: float = convert.DictElementToFloat(dicLut, "fLutCenterCol", fDefault=None, bDoRaise=False)

            xView.Init(
                lPixCnt=[dicSensor.get("iPixCntX"), dicSensor.get("iPixCntY")],
                fPixSize_um=dicSensor.get("fPixSize"),
                fFovMax_deg=dicPano.get("fFovMax_deg"),
                iLutBorderPixel=iLutBorderPixel,
                iLutSuperSampling=iLutSuperSampling,
                lLutCenterRC=[fLutCenterRow, fLutCenterCol],
                xFilePath=pathLutFile,
            )

            if fMaxPolyFitResidual is not None and xView.lPolyFitQuality[0][0] > fMaxPolyFitResidual:
                raise CAnyError_Message(sMsg=(
                    f"The polynomial fit of the LUT has a residual of {xView.lPolyFitQuality[0][0]:6.4f}, "
                    f"which is above the threshold {fMaxPolyFitResidual:6.4f} for LUT: \n"
                    f"     {pathLutFile.as_posix()}\n"
                    "If you want to accept a higher residual threshold set the value of "
                    "'fMaxPolyFitResidual' in the projection configuration to a higher value.\n"
                    "IMPORTANT: A high residual value may lead to incorrect results in the rendering.\n"
                    "           Please check rendering quality of the camera."
                ))
        # endif

        tShift = xView.GetPrinciplePointShift()
        # this value has no effect on the rendering, only on the way
        # Blender displays the camera
        camX.lens = xView.fSenSizeMax_mm / 2.0

        lPolyCoef_rad_mm = xView.lPolyCoef_rad_mm

        if hasattr(camX, "cycles"):
            camX.cycles.panorama_type = "FISHEYE_LENS_POLYNOMIAL"
            camX.cycles.fisheye_fov = math.radians(xView.fFovMax_deg)
            # For some reason need to negate the coefficients for Blender.
            # Otherwise the image is upside-down.
            # HOWEVER, with the negated components the optical flow ground truth
            # does not work. So, we do NOT negate the components here
            # but rotate the camera by 180° about the optical axis.
            # camX.cycles.fisheye_polynomial_k0 = lPolyCoef_rad_mm[0]
            # camX.cycles.fisheye_polynomial_k1 = lPolyCoef_rad_mm[1]
            # camX.cycles.fisheye_polynomial_k2 = lPolyCoef_rad_mm[2]
            # camX.cycles.fisheye_polynomial_k3 = lPolyCoef_rad_mm[3]
            # camX.cycles.fisheye_polynomial_k4 = lPolyCoef_rad_mm[4]

            camX.cycles.fisheye_polynomial_k0 = -lPolyCoef_rad_mm[0]
            camX.cycles.fisheye_polynomial_k1 = -lPolyCoef_rad_mm[1]
            camX.cycles.fisheye_polynomial_k2 = -lPolyCoef_rad_mm[2]
            camX.cycles.fisheye_polynomial_k3 = -lPolyCoef_rad_mm[3]
            camX.cycles.fisheye_polynomial_k4 = -lPolyCoef_rad_mm[4]

        else:
            camX.panorama_type = "FISHEYE_LENS_POLYNOMIAL"
            camX.fisheye_fov = math.radians(xView.fFovMax_deg)

            camX.fisheye_polynomial_k0 = -lPolyCoef_rad_mm[0]
            camX.fisheye_polynomial_k1 = -lPolyCoef_rad_mm[1]
            camX.fisheye_polynomial_k2 = -lPolyCoef_rad_mm[2]
            camX.fisheye_polynomial_k3 = -lPolyCoef_rad_mm[3]
            camX.fisheye_polynomial_k4 = -lPolyCoef_rad_mm[4]

        # endif

        # Turn camera upside-down
        # objCam.rotation_euler = (0.0, 0.0, math.radians(180.0))

        lCrop = None
        iRenderResX = None
        iRenderResY = None
        fAspectX = xView.fAspectX
        fAspectY = xView.fAspectY

    else:
        raise CAnyExcept("Unsupported panoramic camera type '{0}'.".format(sPanoType))
    # endif

    camX.type = "PANO"
    camX.sensor_width = xView.fSenSizeX_mm
    camX.sensor_height = xView.fSenSizeY_mm
    if xView.fSenSizeX_mm >= xView.fSenSizeY_mm:
        camX.sensor_fit = "HORIZONTAL"
    else:
        camX.sensor_fit = "VERTICAL"
    # endif
    camX.shift_x = tShift[0]
    camX.shift_y = tShift[1]

    camX.clip_start = fBUperMM / 2.0
    camX.clip_end = fBUperMM * 1e7
    camX.display_size = max(0.5, fBUperMM * xView.fSenSizeMax_mm / 2.0)

    #############################################################
    # Create Frustum Object and Mesh
    if bCreateFrustum:
        if sPanoType == "equidist" or sPanoType == "equirect":
            objFS = solids.CreateFrustumPanoFovRange(
                sName="Frustum.Pano.S." + _sName,
                lFovRange_deg=xView.lFovRange_deg,
                fFovMax_deg=xView.fFovMax_deg,
                iResolution=20,
                fRayLen=1.0,
            )
            clnMain.objects.link(objFS)

            objFL = solids.CreateFrustumPanoFovRange(
                sName="Frustum.Pano.L." + _sName,
                lFovRange_deg=xView.lFovRange_deg,
                fFovMax_deg=xView.fFovMax_deg,
                iResolution=20,
                fRayLen=1000.0,
            )
            clnMain.objects.link(objFL)

            anyblend.viewlayer.Update()
            # Make Frustum child of camera object
            anyblend.object.ParentObjectList(objCam, [objFL, objFS], bKeepTransform=False)
            anyblend.object.Hide(objFS, bHide=True, bHideInAllViewports=True, bHideRender=True)
            anyblend.object.Hide(objFL, bHide=True, bHideInAllViewports=True, bHideRender=True)

        elif sPanoType == "poly":
            xMeshFrustum: CMeshData = xView.GetFrustumMesh(
                _fRayLen=1.0, _fMaxEdgeAngle_deg=1.0, _fSurfAngleStep_deg=10.0
            )

            objFS: bpy.types.Object = anyblend.object.CreateObjectFromMeshData(
                f"Frustum.Pano.S.{_sName}", xMeshFrustum, _xCollection=clnMain
            )

            # modRemesh = anyblend.ops_object.AddModifier_Remesh(objFS)
            # modRemesh.mode = "SHARP"
            # modRemesh.octree_depth = 5
            # modRemesh.scale = 0.9
            # modRemesh.sharpness = 1.0
            # modRemesh.use_remove_disconnected = True
            # modRemesh.threshold = 1.0
            # modRemesh.use_smooth_shade = True

            # anyblend.ops_object.ApplyModifier(objFS, modRemesh)

            objFL = anyblend.ops_object.Duplicate(objFS)
            objFL.name = f"Frustum.Pano.L.{_sName}"
            objFL.scale = (1e3, 1e3, 1e3)
            anyblend.ops_object.ApplyTransforms(objFL)

            anyblend.viewlayer.Update()
            # Make Frustum child of camera object
            anyblend.object.ParentObjectList(objCam, [objFL, objFS], bKeepTransform=False)
            anyblend.object.Hide(objFS, bHide=True, bHideInAllViewports=True, bHideRender=True)
            anyblend.object.Hide(objFL, bHide=True, bHideInAllViewports=True, bHideRender=True)

        # endif
    # endif (CreateFrustum)

    #############################################################
    # Store AnyCam Data
    if dicAnyCamEx is None:
        dicAnyCamEx = {}
    # endif

    dicAnyCam = {
        "sDTI": "/anycam/camera/pano/{0}:1.2".format(sPanoType),
        "iSenResX": xView.iPixCntX,
        "iSenResY": xView.iPixCntY,
        "fAspectX": fAspectX,
        "fAspectY": fAspectY,
        "fPixSize_um": dicSensor.get("fPixSize"),
        "bEnsureSquarePixel": iEnsureSquarePixel != 0,
        "mEx": dicAnyCamEx,
    }

    if sPanoType == "poly":
        dicAnyCam.update(
            {
                "lPolyCoef_rad_mm": xView.lPolyCoef_rad_mm,
                "lPolyFitQuality": xView.lPolyFitQuality,
                "lCenterOffsetXY_mm": xView.lCenterOffsetXY_mm,
                "fFovMax_deg": xView.fFovMax_deg,
                "lFov_deg": xView.lFov_deg,
                "lFovRange_deg": xView.lFovRange_deg,
            }
        )
    else:
        dicAnyCam.update(
            {
                "fFovMax_deg": dicPano.get("fFovMax_deg"),
                "lFov_deg": dicPano.get("lFov_deg"),
                "lFovRange_deg": lFovRange,
            }
        )
    # enddef

    if iRenderResX is not None and iRenderResY is not None:
        dicAnyCam["iRenderResX"] = iRenderResX
        dicAnyCam["iRenderResY"] = iRenderResY
    # endif

    if lCrop is not None:
        dicAnyCam["lCrop"] = lCrop
    # endif

    objCam["AnyCam"] = json.dumps(dicAnyCam)

    #############################################################

    return {"bResult": True, "objCam": objCam, "objAnyCam": objCam}


# enddef


# ###################################################################################################
def _CreatePanoPolyView(*, _dicSensor: dict, _dicProject: dict):
    xView = CCameraViewPanoPoly()

    if config.IsConfigType(_dicProject, "/anycam/db/project/pano/poly:1.0"):
        xView.Init(
            lPixCnt=[_dicSensor.get("iPixCntX"), _dicSensor.get("iPixCntY")],
            fPixSize_um=_dicSensor.get("fPixSize"),
            fFovMax_deg=_dicProject.get("fFovMax_deg"),
            lPolyCoef_rad_mm=_dicProject.get("lPolyCoef_rad_mm"),
            lCenterOffsetXY_mm=_dicProject.get("lCenterOffsetXY_mm"),
        )

    elif config.IsConfigType(_dicProject, "/anycam/db/project/lut/std:1.0"):
        xView.Init(
            lPixCnt=[_dicSensor.get("iPixCntX"), _dicSensor.get("iPixCntY")],
            fPixSize_um=_dicSensor.get("fPixSize"),
        )
