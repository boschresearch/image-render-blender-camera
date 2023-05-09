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
# The camera set list


class AC_UL_CameraSetList(bpy.types.UIList):
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
        yRow = layout
        ySplit = yRow.split(factor=0.1)
        yCol1 = ySplit.column()
        yCol2 = ySplit.column()

        sIcon = "HIDE_OFF" if item.bShow else "HIDE_ON"
        yCol1.prop(item, "bShow", text="", icon_only=True, icon=sIcon, emboss=False)

        yCol2.label(text=item.sId)

    # enddef


# endclass

##############################################################################
# The camera set panel


class AC_PT_CameraSetCollection(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_label = "Camera Set Collection"
    bl_idname = "AC_PT_CameraSetCollection"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AnyCam"

    def draw(self, context):

        xAcCamSetList = context.scene.AcPropsCamSets

        layout = self.layout

        yRow = layout.row()
        yBox = yRow.box()
        yBox.label(text="Camera Sets")

        yRow = yBox.row()
        ySplit = yRow.split(factor=0.9)
        yCol1 = ySplit.column().row()
        yCol2 = ySplit.column().row()
        yCol1.alert = not xAcCamSetList.bImportFileExists
        yCol1.prop(xAcCamSetList, "sFilePathImport", text="Import file")
        if xAcCamSetList.bImportFileExists:
            yCol2.operator("ac.camset_import", text="", icon="IMPORT", emboss=True)
        else:
            yCol2.label(text="", icon="IMPORT")
        # endif

        yRow = yBox.row()
        ySplit = yRow.split(factor=0.9)
        yCol1 = ySplit.column()
        yCol2 = ySplit.column()
        yCol1.alignment = "RIGHT"

        yCol1.template_list(
            "AC_UL_CameraSetList",
            "",
            xAcCamSetList,
            "clCamSets",
            xAcCamSetList,
            "iSelIdx",
            item_dyntip_propname="sToolTip",
            type="DEFAULT",
        )

        yRow = yCol2.row()
        yRow.operator("ac.camset_create", text="", icon="ADD", emboss=True)

        yRow = yCol2.row()
        if xAcCamSetList.bValidSelection:
            yRow.operator(
                "ac.camset_remove_selected", text="", icon="REMOVE", emboss=True
            )
        else:
            yRow.label(text="", icon="REMOVE")
        # endif

        yRow = yCol2.row()
        if xAcCamSetList.bValidSelection:
            yRow.operator("ac.camset_copy", text="", icon="COPY_ID", emboss=True)
        else:
            yRow.label(text="", icon="COPY_ID")
        # endif

        if xAcCamSetList.bValidSelection:
            xAcCamSet = xAcCamSetList.Selected

            ################################################################
            # Visualization options for camera set
            yRow = yBox.row()
            yRow.prop(xAcCamSet, "sId", text="Name")

            yRow = yBox.row()
            ySplit = yRow.split(factor=0.9)
            yCol1 = ySplit.column()
            yCol2 = ySplit.column()
            bCannotExport = (
                xAcCamSet.bExportFileExists and not xAcCamSet.bExportOverwrite
            )
            yCol1.alert = bCannotExport
            yCol1.prop(xAcCamSet, "sPathExport", text="Export Path")

            if bCannotExport:
                yCol2.label(text="", icon="EXPORT")
            else:
                yCol2.operator("ac.camset_export", text="", icon="EXPORT", emboss=True)
            # endif

            yRow = yBox.row()
            yRow.prop(xAcCamSet, "bExportOverwrite")
        # endif

    # enddef


# endclass

##############################################################################
# Register


def register():
    bpy.utils.register_class(AC_PT_CameraSetCollection)
    bpy.utils.register_class(AC_UL_CameraSetList)


# enddef

##############################################################################
# Unregister


def unregister():
    bpy.utils.unregister_class(AC_PT_CameraSetCollection)
    bpy.utils.unregister_class(AC_UL_CameraSetList)


# enddef
