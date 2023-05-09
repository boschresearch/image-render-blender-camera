#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /poly_vignetting.py
# Created Date: Thursday, November 24nd 2021
# Author: Peter Seitz
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


##########################################################
# Function for linear combination vector group
import bpy
from anyblend.node import align as nalign
from anyblend.node import shader as nsh

##########################################################


def Create(bForce=False):
    """
    Create shader node group for vignetting
    Optional Parameters:
        Force: Renew node tree even if group already exists.
    """

    ngMain = bpy.data.node_groups.get("AnyCam.Vignetting")

    if ngMain is None:
        ngMain = bpy.data.node_groups.new("AnyCam.Vignetting", "ShaderNodeTree")
        bUpdate = True
    else:
        bUpdate = bForce
    # endif

    if bUpdate is True:
        # Output pasted from Node Tree Source Plugin
        # INPUTS
        ngMain.inputs.new("NodeSocketFloat", "radius")
        ngMain.inputs.new("NodeSocketFloat", "Vignetting Coef 1")
        ngMain.inputs.new("NodeSocketFloat", "Vignetting Coef 2")
        ngMain.inputs.new("NodeSocketFloat", "Vignetting Coef 3")
        # OUTPUTS
        ngMain.outputs.new("NodeSocketFloat", "Value")
        # NODES
        group_input_2 = ngMain.nodes.new("NodeGroupInput")
        if hasattr(group_input_2, "active_preview"):
            group_input_2.active_preview = False
        if hasattr(group_input_2, "color"):
            group_input_2.color = (
                0.6079999804496765,
                0.6079999804496765,
                0.6079999804496765,
            )
        if hasattr(group_input_2, "hide"):
            group_input_2.hide = False
        if hasattr(group_input_2, "location"):
            group_input_2.location = (-428.7643737792969, -211.8608856201172)
        if hasattr(group_input_2, "mute"):
            group_input_2.mute = False
        if hasattr(group_input_2, "name"):
            group_input_2.name = "Group Input"
        if hasattr(group_input_2, "use_custom_color"):
            group_input_2.use_custom_color = False
        if hasattr(group_input_2, "width"):
            group_input_2.width = 140.0
        group_input_2.outputs[0].default_value = 0.5
        group_input_2.outputs[1].default_value = 0.0
        group_input_2.outputs[2].default_value = 0.0
        group_input_2.outputs[3].default_value = 0.0

        r_squared_2 = ngMain.nodes.new("ShaderNodeMath")
        if hasattr(r_squared_2, "active_preview"):
            r_squared_2.active_preview = False
        if hasattr(r_squared_2, "color"):
            r_squared_2.color = (
                0.6079999804496765,
                0.6079999804496765,
                0.6079999804496765,
            )
        if hasattr(r_squared_2, "hide"):
            r_squared_2.hide = False
        if hasattr(r_squared_2, "label"):
            r_squared_2.label = "r^2"
        if hasattr(r_squared_2, "location"):
            r_squared_2.location = (-203.703369140625, 0.22352059185504913)
        if hasattr(r_squared_2, "mute"):
            r_squared_2.mute = False
        if hasattr(r_squared_2, "name"):
            r_squared_2.name = "r_squared"
        if hasattr(r_squared_2, "operation"):
            r_squared_2.operation = "POWER"
        if hasattr(r_squared_2, "use_clamp"):
            r_squared_2.use_clamp = False
        if hasattr(r_squared_2, "use_custom_color"):
            r_squared_2.use_custom_color = False
        if hasattr(r_squared_2, "width"):
            r_squared_2.width = 140.0
        r_squared_2.inputs[0].default_value = 0.5
        r_squared_2.inputs[1].default_value = 2.0
        r_squared_2.inputs[2].default_value = 0.0
        r_squared_2.outputs[0].default_value = 0.0

        r_fourth_order_2 = ngMain.nodes.new("ShaderNodeMath")
        if hasattr(r_fourth_order_2, "active_preview"):
            r_fourth_order_2.active_preview = False
        if hasattr(r_fourth_order_2, "color"):
            r_fourth_order_2.color = (
                0.6079999804496765,
                0.6079999804496765,
                0.6079999804496765,
            )
        if hasattr(r_fourth_order_2, "hide"):
            r_fourth_order_2.hide = False
        if hasattr(r_fourth_order_2, "label"):
            r_fourth_order_2.label = "r^4"
        if hasattr(r_fourth_order_2, "location"):
            r_fourth_order_2.location = (-0.00024541220045648515, 2.0747909545898438)
        if hasattr(r_fourth_order_2, "mute"):
            r_fourth_order_2.mute = False
        if hasattr(r_fourth_order_2, "name"):
            r_fourth_order_2.name = "r_fourth_order"
        if hasattr(r_fourth_order_2, "operation"):
            r_fourth_order_2.operation = "POWER"
        if hasattr(r_fourth_order_2, "use_clamp"):
            r_fourth_order_2.use_clamp = False
        if hasattr(r_fourth_order_2, "use_custom_color"):
            r_fourth_order_2.use_custom_color = False
        if hasattr(r_fourth_order_2, "width"):
            r_fourth_order_2.width = 140.0
        r_fourth_order_2.inputs[0].default_value = 0.5
        r_fourth_order_2.inputs[1].default_value = 4.0
        r_fourth_order_2.inputs[2].default_value = 0.0
        r_fourth_order_2.outputs[0].default_value = 0.0

        r_sixth_order_2 = ngMain.nodes.new("ShaderNodeMath")
        if hasattr(r_sixth_order_2, "active_preview"):
            r_sixth_order_2.active_preview = False
        if hasattr(r_sixth_order_2, "color"):
            r_sixth_order_2.color = (
                0.6079999804496765,
                0.6079999804496765,
                0.6079999804496765,
            )
        if hasattr(r_sixth_order_2, "hide"):
            r_sixth_order_2.hide = False
        if hasattr(r_sixth_order_2, "label"):
            r_sixth_order_2.label = "r^6"
        if hasattr(r_sixth_order_2, "location"):
            r_sixth_order_2.location = (195.3720703125, 4.778696537017822)
        if hasattr(r_sixth_order_2, "mute"):
            r_sixth_order_2.mute = False
        if hasattr(r_sixth_order_2, "name"):
            r_sixth_order_2.name = "r_sixth_order"
        if hasattr(r_sixth_order_2, "operation"):
            r_sixth_order_2.operation = "POWER"
        if hasattr(r_sixth_order_2, "use_clamp"):
            r_sixth_order_2.use_clamp = False
        if hasattr(r_sixth_order_2, "use_custom_color"):
            r_sixth_order_2.use_custom_color = False
        if hasattr(r_sixth_order_2, "width"):
            r_sixth_order_2.width = 140.0
        r_sixth_order_2.inputs[0].default_value = 0.5
        r_sixth_order_2.inputs[1].default_value = 6.0
        r_sixth_order_2.inputs[2].default_value = 0.0
        r_sixth_order_2.outputs[0].default_value = 0.0

        multiply_r2_2 = ngMain.nodes.new("ShaderNodeMath")
        if hasattr(multiply_r2_2, "active_preview"):
            multiply_r2_2.active_preview = False
        if hasattr(multiply_r2_2, "color"):
            multiply_r2_2.color = (
                0.6079999804496765,
                0.6079999804496765,
                0.6079999804496765,
            )
        if hasattr(multiply_r2_2, "hide"):
            multiply_r2_2.hide = False
        if hasattr(multiply_r2_2, "location"):
            multiply_r2_2.location = (0.65771484375, -209.3232421875)
        if hasattr(multiply_r2_2, "mute"):
            multiply_r2_2.mute = False
        if hasattr(multiply_r2_2, "name"):
            multiply_r2_2.name = "multiply_r2"
        if hasattr(multiply_r2_2, "operation"):
            multiply_r2_2.operation = "MULTIPLY"
        if hasattr(multiply_r2_2, "use_clamp"):
            multiply_r2_2.use_clamp = False
        if hasattr(multiply_r2_2, "use_custom_color"):
            multiply_r2_2.use_custom_color = False
        if hasattr(multiply_r2_2, "width"):
            multiply_r2_2.width = 140.0
        multiply_r2_2.inputs[0].default_value = 0.5
        multiply_r2_2.inputs[1].default_value = 0.5
        multiply_r2_2.inputs[2].default_value = 0.0
        multiply_r2_2.outputs[0].default_value = 0.0

        multiply_r4_2 = ngMain.nodes.new("ShaderNodeMath")
        if hasattr(multiply_r4_2, "active_preview"):
            multiply_r4_2.active_preview = False
        if hasattr(multiply_r4_2, "color"):
            multiply_r4_2.color = (
                0.6079999804496765,
                0.6079999804496765,
                0.6079999804496765,
            )
        if hasattr(multiply_r4_2, "hide"):
            multiply_r4_2.hide = False
        if hasattr(multiply_r4_2, "location"):
            multiply_r4_2.location = (203.8188934326172, -210.0365753173828)
        if hasattr(multiply_r4_2, "mute"):
            multiply_r4_2.mute = False
        if hasattr(multiply_r4_2, "name"):
            multiply_r4_2.name = "multiply_r4"
        if hasattr(multiply_r4_2, "operation"):
            multiply_r4_2.operation = "MULTIPLY"
        if hasattr(multiply_r4_2, "use_clamp"):
            multiply_r4_2.use_clamp = False
        if hasattr(multiply_r4_2, "use_custom_color"):
            multiply_r4_2.use_custom_color = False
        if hasattr(multiply_r4_2, "width"):
            multiply_r4_2.width = 140.0
        multiply_r4_2.inputs[0].default_value = 0.5
        multiply_r4_2.inputs[1].default_value = 0.5
        multiply_r4_2.inputs[2].default_value = 0.0
        multiply_r4_2.outputs[0].default_value = 0.0

        multiply_r6_2 = ngMain.nodes.new("ShaderNodeMath")
        if hasattr(multiply_r6_2, "active_preview"):
            multiply_r6_2.active_preview = False
        if hasattr(multiply_r6_2, "color"):
            multiply_r6_2.color = (
                0.6079999804496765,
                0.6079999804496765,
                0.6079999804496765,
            )
        if hasattr(multiply_r6_2, "hide"):
            multiply_r6_2.hide = False
        if hasattr(multiply_r6_2, "location"):
            multiply_r6_2.location = (396.287353515625, -216.45660400390625)
        if hasattr(multiply_r6_2, "mute"):
            multiply_r6_2.mute = False
        if hasattr(multiply_r6_2, "name"):
            multiply_r6_2.name = "multiply_r6"
        if hasattr(multiply_r6_2, "operation"):
            multiply_r6_2.operation = "MULTIPLY"
        if hasattr(multiply_r6_2, "use_clamp"):
            multiply_r6_2.use_clamp = False
        if hasattr(multiply_r6_2, "use_custom_color"):
            multiply_r6_2.use_custom_color = False
        if hasattr(multiply_r6_2, "width"):
            multiply_r6_2.width = 140.0
        multiply_r6_2.inputs[0].default_value = 0.5
        multiply_r6_2.inputs[1].default_value = 0.5
        multiply_r6_2.inputs[2].default_value = 0.0
        multiply_r6_2.outputs[0].default_value = 0.0

        add_r2_2 = ngMain.nodes.new("ShaderNodeMath")
        if hasattr(add_r2_2, "active_preview"):
            add_r2_2.active_preview = False
        if hasattr(add_r2_2, "color"):
            add_r2_2.color = (
                0.6079999804496765,
                0.6079999804496765,
                0.6079999804496765,
            )
        if hasattr(add_r2_2, "hide"):
            add_r2_2.hide = False
        if hasattr(add_r2_2, "location"):
            add_r2_2.location = (204.77447509765625, -430.2543640136719)
        if hasattr(add_r2_2, "mute"):
            add_r2_2.mute = False
        if hasattr(add_r2_2, "name"):
            add_r2_2.name = "add_r2"
        if hasattr(add_r2_2, "operation"):
            add_r2_2.operation = "ADD"
        if hasattr(add_r2_2, "use_clamp"):
            add_r2_2.use_clamp = False
        if hasattr(add_r2_2, "use_custom_color"):
            add_r2_2.use_custom_color = False
        if hasattr(add_r2_2, "width"):
            add_r2_2.width = 140.0
        add_r2_2.inputs[0].default_value = 1.0
        add_r2_2.inputs[1].default_value = 0.5
        add_r2_2.inputs[2].default_value = 0.0
        add_r2_2.outputs[0].default_value = 0.0

        add_r4_2 = ngMain.nodes.new("ShaderNodeMath")
        if hasattr(add_r4_2, "active_preview"):
            add_r4_2.active_preview = False
        if hasattr(add_r4_2, "color"):
            add_r4_2.color = (
                0.6079999804496765,
                0.6079999804496765,
                0.6079999804496765,
            )
        if hasattr(add_r4_2, "hide"):
            add_r4_2.hide = False
        if hasattr(add_r4_2, "location"):
            add_r4_2.location = (412.2237548828125, -431.0880432128906)
        if hasattr(add_r4_2, "mute"):
            add_r4_2.mute = False
        if hasattr(add_r4_2, "name"):
            add_r4_2.name = "add_r4"
        if hasattr(add_r4_2, "operation"):
            add_r4_2.operation = "ADD"
        if hasattr(add_r4_2, "use_clamp"):
            add_r4_2.use_clamp = False
        if hasattr(add_r4_2, "use_custom_color"):
            add_r4_2.use_custom_color = False
        if hasattr(add_r4_2, "width"):
            add_r4_2.width = 140.0
        add_r4_2.inputs[0].default_value = 1.0
        add_r4_2.inputs[1].default_value = 0.5
        add_r4_2.inputs[2].default_value = 0.0
        add_r4_2.outputs[0].default_value = 0.0

        add_r6_2 = ngMain.nodes.new("ShaderNodeMath")
        if hasattr(add_r6_2, "active_preview"):
            add_r6_2.active_preview = False
        if hasattr(add_r6_2, "color"):
            add_r6_2.color = (
                0.6079999804496765,
                0.6079999804496765,
                0.6079999804496765,
            )
        if hasattr(add_r6_2, "hide"):
            add_r6_2.hide = False
        if hasattr(add_r6_2, "location"):
            add_r6_2.location = (610.5086059570312, -435.2565612792969)
        if hasattr(add_r6_2, "mute"):
            add_r6_2.mute = False
        if hasattr(add_r6_2, "name"):
            add_r6_2.name = "add_r6"
        if hasattr(add_r6_2, "operation"):
            add_r6_2.operation = "ADD"
        if hasattr(add_r6_2, "use_clamp"):
            add_r6_2.use_clamp = False
        if hasattr(add_r6_2, "use_custom_color"):
            add_r6_2.use_custom_color = False
        if hasattr(add_r6_2, "width"):
            add_r6_2.width = 140.0
        add_r6_2.inputs[0].default_value = 1.0
        add_r6_2.inputs[1].default_value = 0.5
        add_r6_2.inputs[2].default_value = 0.0
        add_r6_2.outputs[0].default_value = 0.0

        inverse_2 = ngMain.nodes.new("ShaderNodeMath")
        if hasattr(inverse_2, "active_preview"):
            inverse_2.active_preview = False
        if hasattr(inverse_2, "color"):
            inverse_2.color = (
                0.6079999804496765,
                0.6079999804496765,
                0.6079999804496765,
            )
        if hasattr(inverse_2, "hide"):
            inverse_2.hide = False
        if hasattr(inverse_2, "location"):
            inverse_2.location = (814.064697265625, -435.256591796875)
        if hasattr(inverse_2, "mute"):
            inverse_2.mute = False
        if hasattr(inverse_2, "name"):
            inverse_2.name = "inverse"
        if hasattr(inverse_2, "operation"):
            inverse_2.operation = "DIVIDE"
        if hasattr(inverse_2, "use_clamp"):
            inverse_2.use_clamp = False
        if hasattr(inverse_2, "use_custom_color"):
            inverse_2.use_custom_color = False
        if hasattr(inverse_2, "width"):
            inverse_2.width = 140.0
        inverse_2.inputs[0].default_value = 1.0
        inverse_2.inputs[1].default_value = 0.5
        inverse_2.inputs[2].default_value = 0.0
        inverse_2.outputs[0].default_value = 0.0

        group_output_2 = ngMain.nodes.new("NodeGroupOutput")
        if hasattr(group_output_2, "active_preview"):
            group_output_2.active_preview = False
        if hasattr(group_output_2, "color"):
            group_output_2.color = (
                0.6079999804496765,
                0.6079999804496765,
                0.6079999804496765,
            )
        if hasattr(group_output_2, "hide"):
            group_output_2.hide = False
        if hasattr(group_output_2, "is_active_output"):
            group_output_2.is_active_output = True
        if hasattr(group_output_2, "location"):
            group_output_2.location = (1070.2601318359375, -438.6955261230469)
        if hasattr(group_output_2, "mute"):
            group_output_2.mute = False
        if hasattr(group_output_2, "name"):
            group_output_2.name = "Group Output"
        if hasattr(group_output_2, "use_custom_color"):
            group_output_2.use_custom_color = False
        if hasattr(group_output_2, "width"):
            group_output_2.width = 140.0
        group_output_2.inputs[0].default_value = 0.0

        # LINKS
        ngMain.links.new(group_input_2.outputs[0], r_squared_2.inputs[0])
        ngMain.links.new(group_input_2.outputs[0], r_fourth_order_2.inputs[0])
        ngMain.links.new(group_input_2.outputs[0], r_sixth_order_2.inputs[0])
        ngMain.links.new(r_squared_2.outputs[0], multiply_r2_2.inputs[0])
        ngMain.links.new(group_input_2.outputs[1], multiply_r2_2.inputs[1])
        ngMain.links.new(r_fourth_order_2.outputs[0], multiply_r4_2.inputs[0])
        ngMain.links.new(group_input_2.outputs[2], multiply_r4_2.inputs[1])
        ngMain.links.new(r_sixth_order_2.outputs[0], multiply_r6_2.inputs[0])
        ngMain.links.new(group_input_2.outputs[3], multiply_r6_2.inputs[1])
        ngMain.links.new(multiply_r2_2.outputs[0], add_r2_2.inputs[1])
        ngMain.links.new(add_r2_2.outputs[0], add_r4_2.inputs[0])
        ngMain.links.new(multiply_r4_2.outputs[0], add_r4_2.inputs[1])
        ngMain.links.new(add_r4_2.outputs[0], add_r6_2.inputs[0])
        ngMain.links.new(multiply_r6_2.outputs[0], add_r6_2.inputs[1])
        ngMain.links.new(inverse_2.outputs[0], group_output_2.inputs[0])
        ngMain.links.new(add_r6_2.outputs[0], inverse_2.inputs[1])

    return ngMain
