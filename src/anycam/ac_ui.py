#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /ac_ui.py
# Created Date: Thursday, October 22nd 2020, 2:51:42 pm
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

from . import ac_global
from . import ac_func

# from . import ops

##############################################################################
# Panels

###################################
# The Camera List


class AC_UL_CamDbList(bpy.types.UIList):
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

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            yRow.label(text=item.sLabel)
            yRow.label(text=item.sType)

        elif self.layout_type in {"GRID"}:
            yRow.label(text=item.sLabel)
            yRow.label(text=item.sType)

        # endif

    # enddef


# endclass

###################################
class AC_UL_CamObjList(bpy.types.UIList):
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

        if item.bHasRenderPars:
            sRPIcon = "SCENE"
        else:
            sRPIcon = "BLANK1"
        # endif

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            yRow = yRow.split(factor=0.1)
            yRow.label(text="", icon=sRPIcon)
            yRow = yRow.split(factor=0.3)
            yRow.label(text=item.sName)
            yRow = yRow.split(factor=0.35)

            sType = item.sSubType if len(item.sSubType) > 0 else item.sType
            yRow.label(text=sType)

            yRow.label(text=item.sDesign)
            # yRow.label(text="{0}x{1}".format(item.iResX, item.iResY))

        elif self.layout_type in {"GRID"}:
            # yRow.label(text=item.sLabel, icon=sRPIcon)
            yRow = yRow.split(factor=0.1)
            yRow.label(text="", icon=sRPIcon)
            yRow = yRow.split(factor=0.4)
            yRow.label(text=item.sName)
            yRow = yRow.split(factor=0.25)

            sType = item.sSubType if len(item.sSubType) > 0 else item.sType
            yRow.label(text=sType)

            yRow.label(text=item.sDesign)
            # yRow.label(text="{0}x{1}".format(item.iResX, item.iResY))

        # endif

    # enddef


# endclass

##############################################################################
# The create camera panel, where cameras can be added to the scene


class AC_PT_Create(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_label = "Create Camera"
    bl_idname = "AC_PT_Create"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AnyCam"

    def draw(self, context):
        xAcProps = context.window_manager.AcProps
        layout = self.layout

        #######################################
        # Camera Path Row
        yRow = layout.row()
        yRow.prop(xAcProps, "sPathCamData")

        #######################################
        # Refresh Button in camera path row
        yRow.operator("ac.update_camera_db", text="", icon="FILE_REFRESH", emboss=True)

        #######################################
        # Camera List
        iCamCnt = len(xAcProps.clCamDb.values())
        yRow = layout.row()
        if iCamCnt == 0:
            yBox = yRow.box()
            yBox.label(text="No camera data path selected.")
        else:
            yRow.template_list(
                "AC_UL_CamDbList",
                "",
                xAcProps,
                "clCamDb",
                xAcProps,
                "iCamDbSelIdx",
                item_dyntip_propname="sToolTip",
                type="DEFAULT",
            )
        # endif

        #######################################
        # Show description about selected camera
        yRow = layout.row()
        yRow.label(text="Selected Camera")

        iSelCamIdx = xAcProps.iCamDbSelIdx
        # print(iSelCamIdx)
        # print(ac_global.lCamNames)
        yRow = layout.row()
        yBox = yRow.box()
        if iSelCamIdx < 0 or iSelCamIdx >= iCamCnt:
            yBox.label(text="No camera selected")
        else:
            yBox.label(text=xAcProps.clCamDb[iSelCamIdx].sLabel)
        # endif

        yRow = layout.row()
        sFullCamName = ac_func.CreateFullCameraName(context, iSelCamIdx)
        xItem = next((x for x in bpy.data.objects if x.name == sFullCamName), None)
        # xItem = next((x for x in xAcProps.clCamObj if x.sLabel == sFullCamName), None)
        bCamNameExists = xItem is not None
        if bCamNameExists:
            yRow.alert = True
        # endif
        yRow.prop(xAcProps, "sCamName", text="Name")

        yRow = layout.row()
        ySplit = yRow.split(factor=0.5)
        yCol1 = ySplit.column()
        yCol2 = ySplit.column()
        yCol1.prop(xAcProps, "fCameraScale")
        yCol2.prop(xAcProps, "bOverwriteCamera", text="Overwrite")

        yRow = layout.row()
        yRow.label(text=sFullCamName)

        # Show button to create selected camera
        yRow = layout.row()
        yRow.operator("ac.create_selected_camera", text="Create Camera", emboss=True)
        if iSelCamIdx < 0 or iSelCamIdx >= iCamCnt or (bCamNameExists and not xAcProps.bOverwriteCamera):
            yRow.enabled = False
        else:
            yRow.enabled = True
        # endif

    # enddef


# endclass

##############################################################################
# The render panel, where cameras can be selected for rendering


class AC_PT_Render(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_label = "Render"
    bl_idname = "AC_PT_Render"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AnyCam"

    def draw(self, context):
        xAcProps = context.window_manager.AcProps
        if xAcProps.bAutoUpdateCamObjList:
            ac_func.CamObjUpdate(self, context)
        # endif

        iCamCnt = len(xAcProps.clCamObj.values())
        iSelCamIdx = xAcProps.iCamObjSelIdx
        bValidCamSel = iSelCamIdx >= 0 and iSelCamIdx < iCamCnt

        layout = self.layout

        #######################################
        # Refresh Button in camera path row
        yRow = layout.row()
        yRow.operator(
            "ac.update_camera_obj_list",
            text="Refresh",
            icon="FILE_REFRESH",
            emboss=True,
        )
        yRow.prop(xAcProps, "bAutoUpdateCamObjList", text="Auto")

        #######################################
        # Camera List
        yRow = layout.row()
        if iCamCnt == 0:
            yBox = yRow.box()
            yBox.label(text="No AnyCam cameras available.")
        else:
            yRow.template_list(
                "AC_UL_CamObjList",
                "",
                xAcProps,
                "clCamObj",
                xAcProps,
                "iCamObjSelIdx",
                item_dyntip_propname="sToolTip",
                type="DEFAULT",
            )
        # endif

        #######################################
        # Show description about selected camera
        yRow = layout.row()
        yRow.label(text="Selected Camera")

        yRow = layout.row()
        yBox = yRow.box()
        if not bValidCamSel:
            yBox.label(text="No camera selected")
        else:
            xItem = xAcProps.clCamObj[iSelCamIdx]
            if xItem.sType == "std":
                yBox.label(text="Standard")
                yRow = yBox.row()
                ySplit = yRow.split(factor=0.4)
                yCol1 = ySplit.column()
                yCol2 = ySplit.column()
                yCol1.alignment = "RIGHT"

                yCol1.label(text="Res. X")
                yCol2.prop(xAcProps, "iCamResX", text="")

                yCol1.label(text="Y")
                yCol2.prop(xAcProps, "iCamResY", text="")
            else:
                if xItem.sType == "lft":
                    sTypeTitle = "LFT"
                elif xItem.sType == "pano":
                    sTypeTitle = "Panoramic"
                elif xItem.sType == "pin":
                    sTypeTitle = "Pinhole"
                elif xItem.sType == "pingen":
                    sTypeTitle = "Gen. Pinhole"
                elif xItem.sType == "poly":
                    sTypeTitle = "Polynomial"
                else:
                    sTypeTitle = xItem.sType
                # endif
                yBox.label(text="{0}, {1}x{2}".format(sTypeTitle, xItem.iResX, xItem.iResY))
            # endif
        # endif

        # if len(xItem.sRenderPars) == 0:
        # 	yBox.label(text="No Render Parameters")
        # else:
        # 	yRow = yBox.row()
        # 	yRow.prop(xAcProps, "bShowRenderPars",
        # 		icon="TRIA_DOWN" if xAcProps.bShowRenderPars else "TRIA_RIGHT",
        # 		icon_only=True, emboss=False
        # 	)
        # 	yRow.label(text="Render Parameters")
        # 	if xAcProps.bShowRenderPars:
        # 		yRow = yBox.row()
        # 		yRow.label(text=xItem.sRenderPars)
        # 	# endif
        # # endif

        # Show button to activate selected camera
        yRow = layout.row()
        yRow.enabled = bValidCamSel
        yRow.operator("ac.activate_selected_camera", text="Activate", emboss=True)
        yRow.operator("ac.remove_selected_camera", text="Remove", emboss=True)
        # yRow.operator("ac.select_selected_camera", text="Select", emboss=True)

        yRow = layout.row()
        yRow.enabled = bValidCamSel
        yRow.prop(xAcProps, "bTransformSceneToCameraFrame", text="Scene to Camera Frame")

        yRow = layout.row()
        yRow.label(text="Render Paramters")
        yRow = layout.row()
        yRow.prop(xAcProps, "bApplyRenderParsOnActivation", text="Apply on Activation")
        yRow = layout.row()
        yRow.operator("ac.assign_render_pars_to_selected_camera", text="Assign", emboss=True)
        yRow.operator("ac.apply_render_pars_from_selected_camera", text="Apply", emboss=True)
        yRow.enabled = bValidCamSel

        yRow = layout.row()
        yRow.label(text="LFT Wavelength")
        yRow.prop(xAcProps, "iLftRenderWavelength", text="")

    # enddef


# endclass

##############################################################################
# Register


def register():
    bpy.utils.register_class(AC_UL_CamObjList)
    bpy.utils.register_class(AC_UL_CamDbList)
    bpy.utils.register_class(AC_PT_Create)
    bpy.utils.register_class(AC_PT_Render)


# enddef

##############################################################################
# Unregister


def unregister():
    bpy.utils.unregister_class(AC_PT_Render)
    bpy.utils.unregister_class(AC_PT_Create)
    bpy.utils.unregister_class(AC_UL_CamDbList)
    bpy.utils.unregister_class(AC_UL_CamObjList)


# enddef
