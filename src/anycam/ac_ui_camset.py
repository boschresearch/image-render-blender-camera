#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ac_ui_camset.py
# Created Date: Friday, April 30th 2021, 8:05:59 am
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

import bpy
from . import ac_func_camset

##############################################################################
# The camera set element list


class AC_UL_CameraLocationList(bpy.types.UIList):
    def draw_item(
        self,
        context,
        layout,
        data,
        item,
        icon,
        active_data,
        active_propname,
        index,
        flt_flag,
    ):
        lId = item.sId.split(";")

        yRow = layout

        ySplit = yRow.split(factor=0.2)
        yCol1 = ySplit.column()
        yCol2 = ySplit.column()

        ySplit1 = yCol1.split()
        yCol1_1 = ySplit1.column()
        yCol1_2 = ySplit1.column()
        yCol1_3 = ySplit1.column()

        # ySplit2 = yCol2.split(factor=0.5)
        # yCol2_1 = ySplit2.column()
        # yCol2_2 = ySplit2.column()

        yCol1_1.prop(item, "colCamera", text="")

        sIcon = "HIDE_OFF" if item.bShowCameraFrustum else "HIDE_ON"
        yCol1_2.prop(
            item,
            "bShowCameraFrustum",
            text="",
            icon_only=True,
            icon=sIcon,
            emboss=False,
        )

        sIcon = "RADIOBUT_ON" if item.bShowIntersection else "RADIOBUT_OFF"
        yCol1_3.prop(
            item, "bShowIntersection", text="", icon_only=True, icon=sIcon, emboss=False
        )

        if data.bCompactView:
            ySplit2 = yCol2.split()
            yCol2_1 = ySplit2.column()
            yCol2_2 = ySplit2.column()
            yCol2_1.label(text=lId[1])
            yCol2_2.label(text=lId[0])
        else:
            yCol2.label(text=lId[1])
            yCol2.label(text=lId[0])
            yCol2.label(text=item.sCathPath)
            yCol2.prop(item, "fFrustDeltaViewScale", text="Delta Scale")
        # endif

    # enddef


# endclass

##############################################################################
# The camera set panel


class AC_PT_CameraSet(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_label = "Camera Set"
    bl_idname = "AC_PT_CameraSet"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AnyCam"

    def draw(self, context):

        xAcProps = context.window_manager.AcProps
        xAcCamSetList = context.scene.AcPropsCamSets

        layout = self.layout

        if not xAcCamSetList.bValidSelection:
            yRow = layout.row()
            yRow.label(text="No camera set selected")

        else:
            xAcCamSet = xAcCamSetList.Selected

            ################################################################
            # Create Camera / Location Pair
            yRow = layout.row()
            yBox = yRow.box()
            yBox.label(text="Camera/Location Pairs")

            yRow = yBox.row()
            # ySplit = yRow.split(factor=0.9)
            # ySupCol1 = ySplit.column().box()
            # ySupCol2 = ySplit.column()
            ySupCol1 = yRow.box()

            ySplit = ySupCol1.split(factor=0.25)
            yCol1 = ySplit.column()
            yCol2 = ySplit.column()

            bCanCreateCamera = True
            bHasLocId = True
            bHasCamId = True
            objAct = context.active_object
            if objAct is None or objAct.type != "EMPTY":
                sLocId = "[Select an Empty]"
                bCanCreateCamera = False
                bHasLocId = False
            else:
                sLocId = objAct.name
            # endif

            if xAcProps.bValidCamSel == False:
                sCamId = "[Select a Camera]"
                bCanCreateCamera = False
                bHasCamId = False
            else:
                sCamId = xAcProps.SelectedCamera.sLabel
            # endif

            bHasCamera = False
            if bCanCreateCamera:
                dicSel = ac_func_camset.GetSelectedCameraLocation(self, context)
                sCamSetElId = xAcCamSet.CreateId(
                    objCamera=dicSel.get("objCam"), objLocation=dicSel.get("objLoc")
                )
                bHasCamera = xAcCamSet.HasId(sCamSetElId)
                bCanCreateCamera = not bHasCamera
            # endif

            yRow = yCol1.row()
            yRow.label(text="Location:")
            yRow.alignment = "RIGHT"

            yRow = yCol2.row()
            yRow.alert = not bHasLocId
            yRow.label(text=sLocId)

            yRow = yCol1.row()
            yRow.label(text="Camera:")
            yRow.alignment = "RIGHT"

            yRow = yCol2.row()
            yRow.alert = not bHasCamId
            yRow.label(text=sCamId)

            ################################################################
            # camera set element properties
            # if xAcCamSet.bValidSelection:
            # 	xAcCamLoc = xAcCamSet.Selected
            # # endif

            ################################################################
            # List Cameras / Location pairs
            yRow = yBox.row()
            ySplit = yRow.split(factor=0.2)
            yCol1 = ySplit.column()
            yCol2 = ySplit.column()

            ySplit1 = yCol1.split()
            yCol1_1 = ySplit1.column()
            yCol1_2 = ySplit1.column()
            yCol1_3 = ySplit1.column()

            ySplit2 = yCol2.split()
            yCol2_1 = ySplit2.column()
            yCol2_2 = ySplit2.column()
            yCol2_3 = ySplit2.column()

            sIcon = "ALIGN_JUSTIFY" if xAcCamSet.bCompactView else "LINENUMBERS_OFF"
            yCol1_1.prop(
                xAcCamSet,
                "bCompactView",
                text="",
                icon=sIcon,
                icon_only=True,
                emboss=False,
            )

            sIcon = "HIDE_OFF" if xAcCamSet.bShowFrustum else "HIDE_ON"
            yCol1_2.prop(
                xAcCamSet,
                "bShowFrustum",
                text="",
                icon=sIcon,
                icon_only=True,
                emboss=False,
            )

            sIcon = "RADIOBUT_ON" if xAcCamSet.bShowIntersection else "RADIOBUT_OFF"
            yCol1_3.prop(
                xAcCamSet,
                "bShowIntersection",
                text="",
                icon=sIcon,
                icon_only=True,
                emboss=False,
            )

            if bCanCreateCamera:
                yCol2_2.operator("ac.create_camset_element", text="Add", emboss=True)
            else:
                yCol2_2.label(text="Add")
            # endif

            if xAcCamSet.bValidSelection:
                yCol2_3.operator("ac.remove_camset_element", text="Remove", emboss=True)
            else:
                yCol2_3.label(text="Remove")
            # endif

            #################################################
            # CamLoc List
            yRow = yBox.row()
            yRow.template_list(
                "AC_UL_CameraLocationList",
                "",
                xAcCamSet,
                "clCameras",
                xAcCamSet,
                "iSelIdx",
                item_dyntip_propname="sToolTip",
                type="DEFAULT",
            )

            if xAcCamSet.bValidSelection:
                xAcCamLoc = xAcCamSet.Selected

                # Additional properties per CamLoc
                yRow = yBox.row()
                yRow.prop(xAcCamLoc, "sCathPath", text="Path")

                yRow = yBox.row()
                yRow.operator(
                    "ac.camset_auto_gen_cathpath",
                    text="Auto generate paths",
                    emboss=True,
                )

                yRow = yBox.row()
                yRow.prop(xAcCamSet, "fFrustumViewScale")

                yRow = yBox.row()
                yRow.prop(
                    xAcCamSet, "objIntersect", text="Intersect", icon="OUTLINER_OB_MESH"
                )

                yRow = yBox.row()
                yRow.prop(xAcCamSet, "fFrustumIntersectScale")
            # endif
        # endif

    # enddef


# endclass

##############################################################################
# Register


def register():
    bpy.utils.register_class(AC_PT_CameraSet)
    bpy.utils.register_class(AC_UL_CameraLocationList)


# enddef

##############################################################################
# Unregister


def unregister():
    bpy.utils.unregister_class(AC_PT_CameraSet)
    bpy.utils.unregister_class(AC_UL_CameraLocationList)


# enddef
