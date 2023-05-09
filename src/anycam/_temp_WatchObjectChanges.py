#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \_temp_WatchObjectChanges.py
# Created Date: Monday, May 3rd 2021, 8:56:15 am
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


class Watcher:
    def __init__(self, object, property, function):
        # if the property object needs deep copy
        try:
            self.oldValue = getattr(object, property).copy()
            self.newValue = getattr(object, property).copy()
        # if the property object doesn't need it (and don't have a copy method)
        except AttributeError:
            self.oldValue = getattr(object, property)
            self.newValue = getattr(object, property)

        self.object = object
        self.property = property
        self.function = function

    # Call the function if the object property changed
    def update(self):
        try:
            self.oldValue = self.newValue.copy()
            self.newValue = getattr(self.object, self.property).copy()
        except AttributeError:
            self.oldValue = self.newValue
            self.newValue = getattr(self.object, self.property)

        if self.oldValue != self.newValue:
            self.function(object=self.object, new=self.newValue, old=self.oldValue)


# this holds all the watchers
watchers = []


def add_watcher(object, property, function):
    watchers.append(Watcher(object, property, function))


# create the function to be called when name changes
# it can change scene property or whatever
def name_change(object, new, old):
    print("old value: " + str(old))
    print("new value: " + str(new))
    return


# lets watch your_object_name's name
add_watcher(bpy.data.objects["YOUR OBJECT NAME"], "name", name_change)


def watcher(scene):
    """This function will be run everytime after scene updates"""
    global watchers
    for watcher in watchers:
        watcher.update()
    return


# add handler if not in app.handlers
if watcher not in bpy.app.handlers.scene_update_post:
    bpy.app.handlers.scene_update_post.append(watcher)
