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
"""
Code to create a lookup table of ray directions for every pixel on the
sensor. This version contains the opencv camera model with up to three radial
distortion parameters. In future, it could also be extended to other camera
models.

To create the lookup table of a given camera, call the function
create_lookup(_tSensorSizeXY, _tFocLenXY, _tImgCtrXY, _tDistRad, _bBlenderFormat=True)

For questions, refer to
Annika Hagemann (CR/AEC3) annika.hagemann@de.bosch.com
"""

import numpy as np
from numpy.polynomial.polynomial import Polynomial as Poly
import math


######################################################################################################
def opencv_radial(_aPoints, _tFocLenXY, _tImgCtrXY, _tDistRad):
    """Project rays back to image plane using a set of intrinsics parameters.
    This is only used for verification purposes.

    Args:
        _aPoints (numpy.ndarray): projection rays for each image pixel. Expected shape is (2, WxH)
        _tFocLenXY (array_like): Focal length (fx, fy). Expected shape (2,).
        _tImgCtrXY (array_like): Principal point (ppx, ppy). Expected shape (2,).
        _tDistRad (array_like):  Radial distortion parameters (k1, k2, k3). Expected shape (n,) where n in [0, 3].
        *args: any further arguments like additional distortion coefficients - ignored
    Returns:
        numpy.ndarray: position of reprojected rays. Shape (2,HxW)
    """

    fFx, fFy = _tFocLenXY
    fPpx, fPpy = _tImgCtrXY

    fK1 = 0
    fK2 = 0
    fK3 = 0
    iDistCnt = len(_tDistRad)
    if iDistCnt >= 1:
        fK1 = _tDistRad[0]
    # endif

    if iDistCnt >= 2:
        fK2 = _tDistRad[1]
    # endif

    if iDistCnt >= 3:
        fK3 = _tDistRad[2]
    # endif

    aNpoints = _aPoints.shape[1]
    aPoint_proj = np.zeros((2, aNpoints))
    aPoints_normalized = _aPoints[0:2, :] / _aPoints[2, :]
    n = np.sum(aPoints_normalized**2, axis=0)
    r = 1 + fK1 * n + fK2 * n**2 + fK3 * n**3
    aPoint_proj[0, :] = aPoints_normalized[0, :] * fFx * r + fPpx
    aPoint_proj[1, :] = aPoints_normalized[1, :] * fFy * r + fPpy

    return aPoint_proj


# enddef


######################################################################################################
def inverse_opencv_radial(_aUv, _tFocLenXY, _tImgCtrXY, _tDistRad):
    """Generate projection rays from a point grid and a set of camera intrinsics.

    Args:
        _aUv (numpy.ndarray): Grid of pixel positions. Expected shape is (2, HxW)
        _tFocLenXY (array_like): Focal length (fx, fy). Expected shape (2,).
        _tImgCtrXY (array_like): Principal point (ppx, ppy). Expected shape (2,).
        _tDistRad (array_like):  Radial distortion parameters (k1, k2, k3). Expected shape (n,) where n in [0, 3].

    Returns:
        numpy.ndarray: projection rays for each image pixel. Shape is (3, WxH).
    """

    fFx, fFy = _tFocLenXY
    fPpx, fPpy = _tImgCtrXY

    fK1 = 0
    fK2 = 0
    fK3 = 0
    iDistCnt = len(_tDistRad)
    if iDistCnt >= 1:
        fK1 = _tDistRad[0]
    # endif

    if iDistCnt >= 2:
        fK2 = _tDistRad[1]
    # endif

    if iDistCnt >= 3:
        fK3 = _tDistRad[2]
    # endif

    aNpoints = _aUv.shape[1]
    aRays = np.zeros((3, aNpoints))

    aRays[0, :] = (_aUv[0, :] - fPpx) / fFx  # K_target-Ã‚Â¹
    aRays[1, :] = (_aUv[1, :] - fPpy) / fFy  # K_target-Ã‚Â¹

    if fK1 != 0.0 or fK2 != 0.0 or fK3 != 0.0:
        # print("Undistort: {}, {}".format(_fK1, _fK2, _fK3))
        aRays = undistort(aRays, fK1, fK2, fK3)
    else:
        aRays[2, :] = 1.0
    # endif

    return aRays


# enddef


######################################################################################################
def maximum_distortion_radius(_fK1, _fK2, _fK3):
    """the maximum radius of polynomial lens distortion is the smallest
    positive root of the derivative of the distorted radius. See also
    https://openaccess.thecvf.com/content/WACV2022/papers/Leotta_On_the_Maximum_Radius_of_Polynomial_Lens_Distortion_WACV_2022_paper.pdf

    Args:
        _fK1 (float): first order radial distortion coefficient.
        _fK2 (float): second order radial distortion coefficient
        _fK3 (float): third order radial distortion coefficient
    Returns:
        float: maximum radius before distortion
        float: maximum radius after distortion
    """

    # distortion polynomial
    polyR = Poly((0, 1.0, 0, _fK1, 0, _fK2, 0, _fK3))
    polyDR = polyR.deriv()

    # get maximum radius (monotonous regime)
    aRoots = polyDR.roots()
    aRoots_real = aRoots[aRoots.imag == 0.0].real
    aRoots_pos = aRoots_real[aRoots_real > 0.0]

    if aRoots_pos.size == 0:
        fRmax_undistorted = np.inf
        fRmax_distorted = np.inf
    else:
        fR_zero = np.min(aRoots_pos)
        fRmax_undistorted = math.floor(fR_zero * 1e2) * 1e-2
        fRmax_distorted = polyR(fRmax_undistorted)
        fRmax_distorted = math.floor(fRmax_distorted * 1e2) * 1e-2

    return fRmax_undistorted, fRmax_distorted


# enddef


######################################################################################################
def approx_undistortion(_aR_distorted, _fK1, _fK2, _fK3):
    """get initial values for undistorted radii by approximating the inverse
    distortion with a fitted polynomial in the valid (monotonous) regime

    Args:
        _aR_distorted(numpy.ndarray): radius of viewing ray for each image pixel. Expected shape is (1,WxH)
        _fK1 (float): first order radial distortion coefficient.
        _fK2 (float): second order radial distortion coefficient
        _fK3 (float): third order radial distortion coefficient
    Returns:
        float: maximum radius before distortion
        float: maximum radius after distortion
    """
    polyR = Poly((0, 1.0, 0, _fK1, 0, _fK2, 0, _fK3))

    # get maximum radius (monotonous regime)
    fRmax_undistorted, _ = maximum_distortion_radius(_fK1, _fK2, _fK3)

    # in case the maximum radius is inf, set heuristic different max value
    fX_max = min(fRmax_undistorted, np.max(_aR_distorted) * 3)

    # define set of undistorted values in monotonous regime
    iStepCnt = 100
    aX = np.arange(0, fX_max, fX_max / iStepCnt)

    # get corresponding distorted values (this direction is known)
    aY = polyR(aX)

    # Fit inverse polynomial
    aFit = np.polyfit(aY, aX, deg=11)
    polyFit = Poly(aFit[::-1])

    return polyFit(_aR_distorted)


# enddef


######################################################################################################
def undistort(_aRays, _fK1, _fK2, _fK3):
    """Find the distance x, that, after applying the distortion, will result in
    the distance r_image.
    Uses Newton Algorithm to compute this.
    Invalid pixels (beyond maximum radius) will be assigned the viewing ray [0, 0, 0].

    Args:
        aRays (numpy.ndarray): undistorted projection rays for each image pixel. Expected shape is (3, WxH).
        _fK1 (float): first order radial distortion coefficient.
        _fK2 (float): second order radial distortion coefficient
        _fK3 (float): third order radial distortion coefficient
    Returns:
        numpy.ndarray: projection rays for each image pixel. Shape is (3, WxH).
    """

    def cost_distortion(_aR, _fK1, _fK2, _fK3, _aR_image):
        """Function of which we want to find the root"""
        aR2 = _aR * _aR
        aR4 = aR2 * aR2
        aR6 = aR4 * aR2
        return _aR * (1 + _fK1 * aR2 + _fK2 * aR4 + _fK3 * aR6) - _aR_image

    # enddef

    def ddr_distortion(_aR, _fK1, _fK2, _fK3, _aR_image=None):
        """Computes derivative of distortion term"""
        aR2 = _aR * _aR
        aR4 = aR2 * aR2
        aR6 = aR4 * aR2
        return 1 + 3 * _fK1 * aR2 + 5 * _fK2 * aR4 + 7 * _fK3 * aR6

    # enddef

    fEpsilon = 1e-10
    aR_image = np.sqrt(np.sum(_aRays * _aRays, axis=0))
    aRays_undistorted = np.zeros((3, _aRays.shape[1]))

    # mask pixels for which maximum distortion radius is exceeded
    _, fRmax_distorted = maximum_distortion_radius(_fK1, _fK2, _fK3)
    aMask = aR_image < fRmax_distorted

    # get initial values for undistorted radii
    aRk = approx_undistortion(aR_image, _fK1, _fK2, _fK3)
    aDf_dr = np.ones(aRk.shape, float)

    # use newton step for optimization
    iI_invert = 0
    while aMask.any():
        aDf_dr[aMask] = ddr_distortion(aRk[aMask], _fK1, _fK2, _fK3, aR_image[aMask])
        aRk[aMask] = aRk[aMask] - (
            cost_distortion(aRk[aMask], _fK1, _fK2, _fK3, aR_image[aMask])
            / aDf_dr[aMask]
        )
        aMask = (
            np.abs(cost_distortion(aRk, _fK1, _fK2, _fK3, aR_image)) > fEpsilon
        ) & (aR_image < fRmax_distorted)

        if iI_invert >= 1000:
            return None
        # endif
        iI_invert += 1
    # endwhile

    # set radii to zero that ended up slightly below zero because of limited
    # optimization accuracy
    aRk[(aRk < 0) & (aRk > -fEpsilon)] = 0

    aRk2 = aRk * aRk
    aRk4 = aRk2 * aRk2
    aRk6 = aRk4 * aRk2

    aRays_undistorted[0, :] = _aRays[0, :] / (
        1 + _fK1 * aRk2 + _fK2 * aRk4 + _fK3 * aRk6
    )
    aRays_undistorted[1, :] = _aRays[1, :] / (
        1 + _fK1 * aRk2 + _fK2 * aRk4 + _fK3 * aRk6
    )
    aRays_undistorted[2, :] = 1

    # set viewing rays of invalid pixels to zero
    aMask_invalid = aR_image >= fRmax_distorted
    aRays_undistorted[:, aMask_invalid] = 0

    #  sanity check to make sure that all valid undistorted radii are positive
    if not np.all(aRk[~aMask_invalid] >= 0):
        raise RuntimeError(
            "Error in calculating undistortion: some radii are negative."
        )
    # endif

    return aRays_undistorted


# enddef


######################################################################################################
def create_lookup(
    _tSensorSizeXY,
    _tFocLenXY,
    _tImgCtrXY,
    _tDistRad,
    _iLutSupersampling=1,
    _iLutBorderPixel=1,
    _bBlenderFormat=True,
):
    """Creates a projection rays mask for a pair of camera  _tIntrinsics and sensor size.

    Args:
        _tSensorSize (array_like): Image plane resolution (width, height). Expected shape (2,).
        _tFocLenXY (array_like): Focal length (fx, fy). Expected shape (2,).
        _tImgCtrXY (array_like): Principal point (ppx, ppy). Expected shape (2,).
        _tDistRad (array_like):  Radial distortion parameters (k1, k2, k3). Expected shape (n,) where n in [0, 3].
        _iLutSupersampling (int): Supersampling parameter, positive integer, defaults to 1 (no supersampling)
        _iLutBorderPixel (int): Number of border pixels (or number of border "subpixels" in case fo supersampling), defaults to 1 (minimum allowed)
        _bBlenderFormat (bool, optional): Whether to transform rays to blender CS. Defaults to True.

    Returns:
        numpy.ndarray: projection rays for each image pixel. Shape is (H, W, 3).
        If _bBlenderFormat is set to False, the shape is (3, WxH).
    """
    # The supersampling parameter must be a strictly posivite integer.
    if not _iLutSupersampling > 0 and isinstance(_iLutSupersampling, int):
        raise ValueError(
            f"_iLutSupersampling should be a strictly positive integer but {_iLutSupersampling} was given."
        )

    # The number of border pixels must be a strictly posivite integer.
    if not _iLutBorderPixel > 0 and isinstance(_iLutBorderPixel, int):
        raise ValueError(
            f"_iLutBorderPixel should be a strictly positive integer but {_iLutBorderPixel} was given."
        )

    # Only flip z-axis for Blender, as y-axis is flipped implicitly,
    # when using numpy array as Blender generated image.
    aRot_x_180 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]])

    # The y axis is pointing downwards. Adjust the vertical centre accordingly.
    _tImgCtrXY_opencv = [_tImgCtrXY[0], _tSensorSizeXY[1] - _tImgCtrXY[1]]

    # Determine the size of the LUT based on the imager size, the supersampling, and the two border pixels
    iLutSizeV = _iLutSupersampling * _tSensorSizeXY[1] + 2 * _iLutBorderPixel
    iLutSizeH = _iLutSupersampling * _tSensorSizeXY[0] + 2 * _iLutBorderPixel
    fStep = 1 / _iLutSupersampling

    # get image coordinates of each pixel. Use pixel center point for ray
    # formation.
    # vertical image direction:
    aV = np.arange(0, _tSensorSizeXY[1], fStep) + 0.5 * fStep
    aV = np.hstack(
        (
            np.arange(aV[0] - _iLutBorderPixel, aV[0], 1),
            aV,
            np.arange(aV[-1], aV[-1] + _iLutBorderPixel, 1),
        )
    )

    # horizontal image direction
    aU = np.arange(0, _tSensorSizeXY[0], fStep) + 0.5 * fStep
    aU = np.hstack(
        (
            np.arange(aU[0] - _iLutBorderPixel, aU[0], 1),
            aU,
            np.arange(aU[-1], aU[-1] + _iLutBorderPixel, 1),
        )
    )

    aU_grid, aV_grid = np.meshgrid(aU, aV)
    aUv = np.array([np.ravel(aU_grid), np.ravel(aV_grid)])

    # get viewing rays of each pixel
    aRays = inverse_opencv_radial(aUv, _tFocLenXY, _tImgCtrXY_opencv, _tDistRad)

    # Legacy return for verification purposes
    if not _bBlenderFormat:
        return aRays

    if aRays is None:
        return None
    # endif

    # Transform rays to blender's camera CS. Shape [H, W, 3].
    aRays_reshaped = np.moveaxis(np.reshape(aRays, (3, iLutSizeV, iLutSizeH)), 0, 2)

    aRays_blender_cs = np.squeeze(aRot_x_180 @ np.expand_dims(aRays_reshaped, -1))

    aNorm = np.linalg.norm(aRays_blender_cs, axis=2)
    aNorm[aNorm == 0] = 1
    aRays_normalized = aRays_blender_cs / np.expand_dims(aNorm, -1)

    iImgCtrX = int(_tImgCtrXY_opencv[0])
    iImgCtrY = int(_tImgCtrXY_opencv[1])

    aRayLeft = aRays_normalized[iImgCtrY, 0, :]
    aRayRight = aRays_normalized[iImgCtrY, _tSensorSizeXY[0] - 1, :]
    aRayTop = aRays_normalized[_tSensorSizeXY[1] - 1, iImgCtrX, :]
    aRayBot = aRays_normalized[0, iImgCtrX, :]

    fDegPerRad = 180.0 / np.pi
    fAngleLeft = np.arctan2(aRayLeft[0], -aRayLeft[2]) * fDegPerRad
    fAngleRight = np.arctan2(aRayRight[0], -aRayRight[2]) * fDegPerRad
    fAngleTop = np.arctan2(aRayTop[1], -aRayTop[2]) * fDegPerRad
    fAngleBot = np.arctan2(aRayBot[1], -aRayBot[2]) * fDegPerRad

    dicRes = {
        "aRays": aRays_normalized,
        "lFov_deg": [fAngleRight - fAngleLeft, fAngleTop - fAngleBot],
        "lFovRange_deg": [[fAngleLeft, fAngleRight], [fAngleBot, fAngleTop]],
    }

    return dicRes


# enddef


######################################################################################################
def verify_inverse_model():
    """Testing method to verify that the projection rays are computed correctly."""
    import timeit

    start = timeit.default_timer()

    tSensor_Size = (1936, 1216)  # (width, height)
    tFocLenXY = (1500.0, 1500.0)
    tImgCtrXY = (988.0, 620.0)
    tDistRad = (-0.7, -0.2, -0.2)
    iSupersampling = 1
    fStep = 1 / iSupersampling
    iLutBorderPixel = 1

    aRays = create_lookup(
        tSensor_Size, tFocLenXY, tImgCtrXY, tDistRad, _bBlenderFormat=False
    )

    aMask_invalid = aRays[2, :] == 0
    aUv_backprojected = opencv_radial(
        aRays[:, ~aMask_invalid],
        tFocLenXY,
        (tImgCtrXY[0], tSensor_Size[1] - tImgCtrXY[1]),
        tDistRad,
    )

    step = 1
    # get image coordinates of each pixel. Use pixel center point for ray
    # formation.
    # vertical image direction:
    aV = np.arange(0, tSensor_Size[1], fStep) + 0.5 * fStep
    aV = np.hstack(
        (
            np.arange(aV[0] - iLutBorderPixel, aV[0], 1),
            aV,
            np.arange(aV[-1], aV[-1] + iLutBorderPixel, 1),
        )
    )

    # horizontal image direction
    aU = np.arange(0, tSensor_Size[0], fStep) + 0.5 * fStep
    aU = np.hstack(
        (
            np.arange(aU[0] - iLutBorderPixel, aU[0], 1),
            aU,
            np.arange(aU[-1], aU[-1] + iLutBorderPixel, 1),
        )
    )
    aU_grid, aV_grid = np.meshgrid(aU, aV)
    aUv_original = np.array([np.ravel(aU_grid), np.ravel(aV_grid)])

    print(
        "Maximum deviation in image points: ",
        np.max(aUv_backprojected - aUv_original[:, ~aMask_invalid]),
    )

    stop = timeit.default_timer()
    print("Time: ", stop - start)


# enddef


######################################################################################################
######################################################################################################
if __name__ == "__main__":
    verify_inverse_model()
# endif
