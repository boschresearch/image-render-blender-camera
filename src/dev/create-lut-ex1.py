#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cam-lut-01.py
# Created Date: Monday, January 9th 2023, 9:39:31 am
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
"""Example to demonstrate how to create a camera LUT."""
import os
import json
from pathlib import Path

# need to enable OpenExr explicitly
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2
import numpy as np

def CreatePinholeLut(
        pathOutput: Path, 
        sName: str, 
        iSizeX_pix: int, 
        iSizeY_pix: int, 
        fCenterX_pix: float, 
        fCenterY_pix: float, 
        fFocalLength_pix: float,
        iLutBorder_pix: int = 1,
        iLutSuperSampling: int = 1,
    ) -> None:
    """Create a LUT for a pinhole camera model."""
    pathOutput.mkdir(parents=True, exist_ok=True)

    # IMPORANT:
    # The size of the image sensor in pixel units is given by iSizeX_pix and iSizeY_pix.
    # The integer pixel indices reference the CENTERS of the pixels.
    # For calculation the projection rays, we are using position coordinates on the sensor plane
    # in pixel units. The pixel center coordinates are given by the integer pixel indices plus 0.5.
    # The horizontal (X) position 0 refers to the left edge of the left most pixel.
    # The horizontal (X) position iSizeX_pix refers to the right edge of the right most pixel.
    # The horizontal (X) position of the pixel with index 0 is 0.5.
    # The vertical (Y) position 0 refers to the bottom edge of the bottom most pixel.
    # The vertical (Y) position iSizeY_pix refers to the top edge of the top most pixel.
    # The vertical (Y) position of the pixel with index 0 is 0.5.

    iEffSizeX_pix: int = iSizeX_pix * iLutSuperSampling + 2 * iLutBorder_pix
    iEffSizeY_pix: int = iSizeY_pix * iLutSuperSampling + 2 * iLutBorder_pix
    fEffCenterX_pix: float = fCenterX_pix * iLutSuperSampling + iLutBorder_pix
    fEffCenterY_pix: float = fCenterY_pix * iLutSuperSampling + iLutBorder_pix
    fEffFocalLength_pix: float = fFocalLength_pix * iLutSuperSampling

    # Create an empty LUT with numpy
    # The fourth color channel is the attenuation of the light intensity.
    aLut: np.ndarray = np.zeros((iEffSizeY_pix, iEffSizeX_pix, 4), dtype=np.float32)
    aLut[:, :, 3] = 1.0  # Set the attenuation to 1.0 for all pixels

    for iY_pix in range(iEffSizeY_pix):
        for iX_pix in range(iEffSizeX_pix):
            # Calculate the position of the pixel center in pixel units
            fPosX_pix: float = iX_pix + 0.5
            fPosY_pix: float = iY_pix + 0.5

            # Calculate the projection direction vector in Blender coordinates.
            # In Blender, the origin is in the specified image center,
            # x-axis points to the right, y-axis points up and 
            # the NEGATIVE z-axis points into the direction the camera looks at.
            fX: float = fPosX_pix - fEffCenterX_pix
            fY: float = fEffCenterY_pix - fPosY_pix
            fZ: float = -fEffFocalLength_pix
            fLen: float = np.sqrt(fX * fX + fY * fY + fZ * fZ)

            # Store the normalized coordinates in the LUT
            aLut[iY_pix, iX_pix, 0] = fX / fLen
            aLut[iY_pix, iX_pix, 1] = fY / fLen
            aLut[iY_pix, iX_pix, 2] = fZ / fLen

    # Save LUT to file
    sLutFilename = f"{sName}_lut.exr"
    pathLut = pathOutput / sLutFilename
    print(f"LUT file: {pathLut.as_posix()}")

    # opencv stores images a BGR and NOT RGB,
    # so we need to exchange the R and B channels
    aLut_swapped = aLut[:, :, [2, 1, 0, 3]]

    cv2.imwrite(pathLut.as_posix(), aLut_swapped)

    # Create & save LUT Config file
    dicConfig: dict = {
        "sDTI": "/anycam/db/project/lut/std:1.1",
        "sId": "$filebasename",
        "sLutFile": sLutFilename,   
        "iLutBorderPixel": iLutBorder_pix,
        "iLutSuperSampling": iLutSuperSampling,
        "fLutCenterRow": fEffCenterY_pix,
        "fLutCenterCol": fEffCenterX_pix,
        "iSensorRows": iSizeY_pix,
        "iSensorCols": iSizeX_pix,
    }

    sConfigFilename = f"{sName}_lut.json"
    pathConfig = pathOutput / sConfigFilename
    print(f"LUT config file: {pathConfig.as_posix()}")

    with open(pathConfig.as_posix(), "w") as f:
        json.dump(dicConfig, f, indent=4)
        

if __name__ == "__main__":
    # Example parameters for the LUT
    sName: str = "pinhole"
    iSizeX_pix: int = 1000
    iSizeY_pix: int = 1000
    fCenterX_pix: float = iSizeX_pix / 2.0
    fCenterY_pix: float = iSizeY_pix / 2.0
    fFocalLength_pix: float = 400.0
    iLutBorder_pix: int = 1
    iLutSuperSampling: int = 1

    # Create the LUT
    pathOutput: Path = Path(__file__).parent / "lut"
    CreatePinholeLut(
        pathOutput, 
        sName, 
        iSizeX_pix, 
        iSizeY_pix, 
        fCenterX_pix, 
        fCenterY_pix, 
        fFocalLength_pix,
        iLutBorder_pix=iLutBorder_pix,
        iLutSuperSampling=iLutSuperSampling,
    )
