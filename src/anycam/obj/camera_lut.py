#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /camera_pinhole.py
# Created Date: Friday, January 6th 2023, 11:55:12 am
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

import anyblend.ops_image
import bpy
import bmesh

# import math
# import mathutils
import os
import json
import numpy as np
from pathlib import Path
from typing import Any, Union

from .. import ops

# from .. import node
from ..material import ray_lut_fisheye

# from .. import model

# from ..mesh import solids
from ..model.cls_camera_lut import CCameraLut

import anyblend
from anybase.cls_any_error import CAnyError_Message
from anybase import convert
from anybase import path as anypath


#####################################################################
# Create the camera name
def CreateName(_sName):
    return "Cam.Lut.{0}".format(_sName)


# enddef


#####################################################################
# Create Light Field Trace Cameras
def Create(
    _sName: str,
    _dicCamera: dict,
    bOverwrite: bool = False,
    bForce: bool = False,
    fScale: float = 1.0,
    bCreateFrustum: bool = False,
    dicAnyCamEx: dict = None,
) -> dict[str, Any]:

    #####################################################
    # Get camera data
    dicProject = _dicCamera.get("dicProject")

    pathLutFile = Path(convert.DictElementToString(dicProject, "sLutFile"))
    if not pathLutFile.is_absolute():
        dicPrjVars: dict = dicProject.get("__locals__")
        if dicPrjVars is None:
            raise RuntimeError("Project configuration does not contain automatically added path information")
        # endif

        sPrjCfgPath: str = dicPrjVars.get("path")
        if sPrjCfgPath is None:
            raise RuntimeError("Project configuration does not contain automatically added path information")
        # endif

        pathLutFile = anypath.MakeNormPath((sPrjCfgPath, pathLutFile))
    # endif

    if not pathLutFile.exists():
        raise RuntimeError(f"LUT file not found at: {(pathLutFile.as_posix())}")
    # endif

    iLutBorderPixel: int = convert.DictElementToInt(dicProject, "iLutBorderPixel", iDefault=0)
    iLutSuperSampling: int = convert.DictElementToInt(dicProject, "iLutSuperSampling", iDefault=1)
    fLutCenterRow: float = convert.DictElementToFloat(dicProject, "fLutCenterRow", fDefault=None, bDoRaise=False)
    fLutCenterCol: float = convert.DictElementToFloat(dicProject, "fLutCenterCol", fDefault=None, bDoRaise=False)

    #####################################################
    # Create LUT Camera model
    xCamLut = CCameraLut()
    xCamLut.FromFile(
        _xFilePath=pathLutFile,
        _iLutBorderPixel=iLutBorderPixel,
        _iLutSuperSampling=iLutSuperSampling,
        _fLutCenterRow=fLutCenterRow,
        _fLutCenterCol=fLutCenterCol,
    )

    # print(xCamLut._tRenderLutAngleRangeX_deg)
    # print(xCamLut._tRenderLutAngleRangeY_deg)
    return CreateCameraLut(
        _sName, 
        xCamLut, 
        bOverwrite=bOverwrite, 
        bForce=bForce, 
        fScale=fScale, 
        bCreateFrustum=bCreateFrustum, 
        dicAnyCamEx=dicAnyCamEx
    )

# ##################################################################################
def CreateCameraLut(_sName: str, 
                    xCamLut: CCameraLut,     
                    bOverwrite: bool = False,
                    bForce: bool = False,
                    fScale: float = 1.0,
                    bCreateFrustum: bool = False,
                    dicAnyCamEx: dict = None,
) -> dict[str, Any]:
    # Create camera empty, that acts as origin for whole camera system

    # Calculate Blender Units per Millimeter
    fBUperMM = fScale * 1e-3 / bpy.context.scene.unit_settings.scale_length

    # Create the name for the camera
    sCamName = CreateName(_sName)

    # get or create anycam collection where all cameras are placed
    clnMain = bpy.data.collections.get("AnyCam") # type: ignore
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

    objCamOrig = bpy.data.objects.new(sCamName, None)
    objCamOrig.location = (0, 0, 0)
    objCamOrig.empty_display_size = 1
    objCamOrig.empty_display_type = "PLAIN_AXES"
    clnMain.objects.link(objCamOrig)

    #####################################################
    # Create render fisheye camera
    sSenName = sCamName + ".Sen"

    camX = bpy.data.cameras.get(sSenName)
    if camX is not None:
        bpy.data.cameras.remove(camX)
        camX = None
    # endif

    camX = bpy.data.cameras.new(sSenName)
    objCam = bpy.data.objects.new(name=sSenName, object_data=camX)

    # cnMain = bpy.context.scene.collection
    vlMain = bpy.context.view_layer
    clnMain.objects.link(objCam)
    vlMain.objects.active = objCam
    objCam.select_set(True)

    # Specify camera parameters

    # fPixSize_mm = 1e-3 * fPixSize_um
    # fSenSizeX_mm = fPixSize_mm * iPixCntX
    # fSenSizeY_mm = fPixSize_mm * iPixCntY
    # fSenSizeMax_mm = max(fSenSizeX_mm, fSenSizeY_mm)
    # fFocLen_mm = fSenSizeMax_mm
    # fFocLen_mm = lFocLenXY_pix[0] * fPixSize_mm

    camX.type = "PANO"
    if hasattr(camX, "cycles"):
        camX.cycles.panorama_type = "FISHEYE_EQUIDISTANT"
        camX.cycles.fisheye_fov = xCamLut.fRenderFoV_rad
    else:
        camX.panorama_type = "FISHEYE_EQUIDISTANT"
        camX.fisheye_fov = xCamLut.fRenderFoV_rad
    # endif
    camX.shift_x = xCamLut.tCamShiftXY[0]
    camX.shift_y = xCamLut.tCamShiftXY[1]

    # Dummy values
    camX.lens = 50.0
    camX.lens_unit = "MILLIMETERS"
    camX.sensor_width = 50.0
    camX.sensor_height = 50.0
    camX.sensor_fit = "HORIZONTAL"

    camX.clip_start = fBUperMM * 0.1
    camX.clip_end = fBUperMM * 1e7
    camX.display_size = max(0.5, fBUperMM * 50.0)

    # Sensor position relative to camera origin.
    objCam.location = (0, 0, 0)
    objCam.rotation_euler = (0, 0, 0)

    ##############################################################
    # Creating LUT image object
    sImgName = sCamName + ".RayDir"
    imgA = bpy.data.images.get(sImgName)
    if imgA is not None:
        bpy.data.images.remove(imgA)
    # endif

    iLutPixCntY, iLutPixCntX = xCamLut.tLutPixCntRC

    imgA: bpy.types.Image = bpy.data.images.new(sImgName, iLutPixCntX, iLutPixCntY, alpha=True, float_buffer=True, is_data=True)
    sImgName = imgA.name
    # bpy.ops.image.new(name=sImgName, width=iImgW, height=iImgH)
    # imgA = bpy.data.images[sImgName]
    imgA.use_fake_user = True

    # print("LUT pixel count: {}".format(aRayImg.size))
    # print("image pixel count: {}".format(len(imgA.pixels)))

    # Copy the actual pixels into the Blender image
    imgA.pixels = list(xCamLut.imgLutFlipped.flatten())

    # Pack image in Blender file
    anyblend.ops_image.Pack(imgA)

    # Create a texture that uses the image to ensure that the image is not deleted by Blender
    sTexName = sCamName + ".RayDir.Tex"
    texA = bpy.data.textures.get(sTexName)
    if texA is not None:
        bpy.data.textures.remove(texA)
    # endif
    texA = bpy.data.textures.new(sTexName, type="IMAGE")
    texA.image = imgA
    texA.use_fake_user = True

    #####################################################
    # Create Parameter node groups
    # node.grp.render_pars.Create(bForce=bForce, fScale=fScale)
    # node.grp.sensor_pars.Create(dicSensor, bForce=bForce)
    #####################################################

    #####################################################
    # Create sphere surrounding camera with refractor that acts as sensor plane
    sRefractorName = sSenName + ".RF"

    objRF = bpy.data.objects.get(sRefractorName)
    if objRF is not None:
        bpy.data.objects.remove(objRF)
    # endif

    meshRF = bpy.data.meshes.get(sRefractorName)
    if meshRF is not None:
        bpy.data.meshes.remove(meshRF)
    # endif

    meshRF = bpy.data.meshes.new(sRefractorName)
    objRF = bpy.data.objects.new(name=sRefractorName, object_data=meshRF)
    clnMain.objects.link(objRF)

    # objRF.location = (-lCenter_mm[0], -lCenter_mm[1], 0)
    objRF.location = (0, 0, 0)

    # Create refractive sphere.
    # MUST flip normals for this to work with the shader.
    bmX = bmesh.new()
    bmesh.ops.create_uvsphere(bmX, u_segments=32, v_segments=16, radius=5.0 * fBUperMM)
    for faceX in bmX.faces:
        faceX.normal_flip()
    # endfor
    bmX.normal_update()
    bmX.to_mesh(meshRF)
    meshRF.update()
    bmX.free()

    try:
        # Get Refractor Material
        matRF, ngLut = ray_lut_fisheye.Create(
            _sId=sCamName,
            _sImgLut=imgA.name,
            _tLutAngleRangeX_deg=xCamLut.tRenderLutAngleRangeX_deg,
            _tLutAngleRangeY_deg=xCamLut.tRenderLutAngleRangeY_deg,
            _bForce=True,
        )
    except Exception as xEx:
        return {
            "bResult": False,
            "objCam": objCamOrig,
            "sMsg": "Exception creating LUT material:\n{}".format(str(xEx)),
        }
    # endtry

    objRF.data.materials.append(matRF)

    #############################################################
    # Create Frustum if needed
    if bCreateFrustum is True:
        xMeshFrustumS = xCamLut.GetFrustumMesh(_fRayLen=1.0, _fMaxEdgeAngle_deg=1.0, _fSurfAngleStep_deg=10.0)
        objFS: bpy.types.Object = anyblend.object.CreateObjectFromMeshData(
            f"Frustum.Lut.S.{_sName}", xMeshFrustumS, _xCollection=clnMain
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
        objFL.name = f"Frustum.Lut.L.{_sName}"
        objFL.scale = (1e3, 1e3, 1e3)
        anyblend.ops_object.ApplyTransforms(objFL)

        anyblend.viewlayer.Update()
        # Make Frustum child of camera object
        anyblend.object.ParentObjectList(objCam, [objFL, objFS], bKeepTransform=False)
        anyblend.object.Hide(objFS, bHide=True, bHideInAllViewports=True, bHideRender=True)
        anyblend.object.Hide(objFL, bHide=True, bHideInAllViewports=True, bHideRender=True)

    # endif

    #############################################################
    # Store AnyCam Data
    if dicAnyCamEx is None:
        dicAnyCamEx = {}
    # endif

    dicAnyCamEx.update(
        {
            "mDepData": {
                "images": [imgA.name],
                "textures": [texA.name],
                "materials": [matRF.name],
                "node_groups": [ngLut.name],
            },
            "mLutData": {
                "sImageName": imgA.name,
                "sFilePath": None,
                "iLutBorderPixel": xCamLut.iLutBorderPixel,
                "iLutSuperSampling": xCamLut.iLutSuperSampling,
                "lLutCenterRC": list(xCamLut.tLutCenterRC),
                "sRefractMaterial": matRF.name,
            },
            "mAnyTruth": {
                "sLabelShaderType": "/anytruth/label/shader/emission:1.0",
            },
        }
    )

    tImgPixCntRC = xCamLut.tImgPixCntRC
    iRenderPixCnt = xCamLut.iRenderPixCnt
    xCrop = xCamLut.xRenderCrop

    objCam["AnyCam"] = json.dumps(
        {
            "sDTI": "/anycam/camera/lut/std:1.2",
            "iSenResX": tImgPixCntRC[1],
            "iSenResY": tImgPixCntRC[0],
            "fAspectX": 1.0,
            "fAspectY": 1.0,
            "fPixSize_um": 1.0,
            "sOrigin": objCamOrig.name,
            "lFov_deg": list(xCamLut.tLutFovXY_deg),
            "lFovRange_deg": [list(xCamLut.tLutAngleRangeX_deg), list(xCamLut.tLutAngleRangeY_deg)],
            "iRenderResX": iRenderPixCnt,
            "iRenderResY": iRenderPixCnt,
            "lCrop": [xCrop.fLeft, xCrop.fRight, xCrop.fBottom, xCrop.fTop],
            "mEx": dicAnyCamEx,
        }
    )

    #############################################################
    # Place objects in hierarchical order
    anyblend.viewlayer.Update()
    anyblend.object.ParentObject(objCam, objRF)
    anyblend.object.ParentObject(objCamOrig, objCam)

    return {"bResult": True, "objCam": objCamOrig, "objAnyCam": objCam}

    # return {"bResult": False, "objCam": None}


# enddef


# ###############################################################################
def GetBlenderLutImage(_sImageName: str, _bDoRaise=True) -> np.ndarray:
    bpyImage = bpy.data.images.get(_sImageName)
    if bpyImage is None:
        if _bDoRaise is True:
            raise CAnyError_Message(sMsg=f"Blender LUT image '{_sImageName}' not found")
        # endif
        return None
    # endif

    if bpyImage.is_float is False:
        if _bDoRaise is True:
            raise CAnyError_Message(sMsg=f"Blender LUT image '{_sImageName}' is not of data type 'float'")
        # endif
        return None
    # endif

    imgLut = np.asarray(bpyImage.pixels, dtype=np.float32)
    imgLut = imgLut.reshape(bpyImage.size[1], bpyImage.size[0], -1)

    # need to flip Y-axis of image array, as it is stored with
    # bottom row first.
    imgLut = np.flipud(imgLut)

    return imgLut


# enddef


# ###############################################################################
# Save Blender Lut Image
def SaveBlenderLutImage(_xFilePath: Union[str, list, tuple, Path], _sImageName: str, *, _bOverwrite: bool = True):
    import os

    # need to enable OpenExr explicitly
    os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
    import cv2

    pathFile = anypath.MakeNormPath(_xFilePath).absolute()

    if pathFile.suffix != ".exr":
        raise RuntimeError("LUT images can only be saved to 32bit RGBA OpenEXR files")
    # endif

    if pathFile.exists():
        if _bOverwrite is True:
            pathFile.unlink()
        else:
            return
        # endif
    # endif

    imgLut = GetBlenderLutImage(_sImageName)
    # Flip order of color channel elements, as cv2 stores images as BGR and not RGB.
    if imgLut.shape[2] == 4:
        imgLut = imgLut[:, :, [2, 1, 0, 3]]
    else:
        imgLut = imgLut[:, :, ::-1]
    # endif

    bRet: bool = cv2.imwrite(pathFile.as_posix(), imgLut.astype(np.float32))
    if bRet is False:
        raise RuntimeError(f"Error writing camera LUT file to: {(pathFile.as_posix())}")
    # endif


# enddef


# ###############################################################################
# Store LUT data in dictionary and saving LUT file
def StoreLutCameraData(
    *, _dicCamData: dict, _xPath: Union[Path, str], _xFromPath: Path = None, _bOverwrite: bool = True
):
    try:
        dicLutData: dict = _dicCamData["mEx"]["mLutData"]
        sImageName = dicLutData["sImageName"]
    except Exception as xEx:
        raise CAnyError_Message(sMsg=f"Incomplete camera data for LUT camera", xChildEx=xEx)
    # endtry

    pathTrg = Path(_xPath)

    # sLutFilename = "Camera-LUT.exr"
    sName = sImageName.replace(".", "-")
    sLutFilename = f"LUT-{sName}.exr"

    pathLutFile = pathTrg / sLutFilename

    if _xFromPath is not None:
        dicLutData["sFilePath"] = Path(os.path.relpath(pathLutFile.as_posix(), _xFromPath.as_posix())).as_posix()
    else:
        dicLutData["sFilePath"] = sLutFilename
    # endif

    SaveBlenderLutImage(pathLutFile, sImageName, _bOverwrite=_bOverwrite)


# enddef
