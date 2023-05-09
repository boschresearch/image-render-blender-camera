#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /__init__.py
# Created Date: Thursday, October 22nd 2020, 2:51:39 pm
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

bl_info = {
    "name": "AnyCam",
    "description": "Integrate different types of cameras into your workspace, easily.",
    "author": "Christian Perwass",
    # "version": (settings.VERSION_MAJOR, settings.VERSION_MINOR),
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Toolshelf > AnyCam",
    "warning": "",  # used for warning icon and text in addons panel
    # "wiki_url": "https://docs.google.com/document/d/15iQoycej0DfRhtZTpLxPe6VaAN4Ro5WOmv18fTWN0cY",
    # "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
    #            "Scripts/My_Script",
    # "tracker_url": "http://google.com", <-- a bit rude don't you think?
    # "tracker_url": "https://blenderartists.org/t/graswald/678219",
    "support": "COMMUNITY",
    "category": "Object",
}


##################################################################
try:
    import _bpy

    bInBlenderContext = True

except Exception:
    bInBlenderContext = False
# endtry

if bInBlenderContext is True:
    try:
        # ## DEBUG ##
        # import anybase.module

        # anybase.module.ReloadModule(_sName="anyblend", _bChildren=True, _bDoPrint=True)
        # anybase.module.ReloadCurrentChildModules(_bDoPrint=True)
        # ###########

        from . import ops
        from . import ac_ui
        from . import ac_props
        from . import ac_ops
        from . import ac_pref
        from . import ac_props_camloc
        from . import ac_props_camset
        from . import ac_props_camsetcol
        from . import ac_ui_camset
        from . import ac_ui_camsetcol
        from . import ac_ops_camset
        from . import ac_func_camset
        from . import ap_ac_ui
        from . import ap_ac_props
        from . import ops_ap_ac

        # if "ops" in locals():
        #     importlib.reload(ops)
        # else:
        #     from . import ops
        # # endif

        # if "ac_ui" in locals():
        #     importlib.reload(ac_ui)
        # else:
        #     from . import ac_ui
        # # endif

        # if "ac_props" in locals():
        #     importlib.reload(ac_props)
        # else:
        #     from . import ac_props
        # # endif

        # if "ac_ops" in locals():
        #     importlib.reload(ac_ops)
        # else:
        #     from . import ac_ops
        # # endif

        # if "ac_pref" in locals():
        #     importlib.reload(ac_pref)
        # else:
        #     from . import ac_pref
        # # endif

        # if "ac_props_camloc" in locals():
        #     importlib.reload(ac_props_camloc)
        # else:
        #     from . import ac_props_camloc
        # # endif

        # if "ac_props_camset" in locals():
        #     importlib.reload(ac_props_camset)
        # else:
        #     from . import ac_props_camset
        # # endif

        # if "ac_props_camsetcol" in locals():
        #     importlib.reload(ac_props_camsetcol)
        # else:
        #     from . import ac_props_camsetcol
        # # endif

        # if "ac_ui_camsetcol" in locals():
        #     importlib.reload(ac_ui_camsetcol)
        # else:
        #     from . import ac_ui_camsetcol
        # # endif

        # if "ac_ui_camset" in locals():
        #     importlib.reload(ac_ui_camset)
        # else:
        #     from . import ac_ui_camset
        # # endif

        # if "ac_ops_camset" in locals():
        #     importlib.reload(ac_ops_camset)
        # else:
        #     from . import ac_ops_camset
        # # endif

        # if "ac_func_camset" in locals():
        #     importlib.reload(ac_func_camset)
        # else:
        #     from . import ac_func_camset
        # # endif

        # if "ap_ac_ui" in locals():
        #     importlib.reload(ap_ac_ui)
        # else:
        #     from . import ap_ac_ui
        # # endif

        # if "ap_ac_props" in locals():
        #     importlib.reload(ap_ac_props)
        # else:
        #     from . import ap_ac_props
        # # endif

        # if "ops_ap_ac" in locals():
        #     importlib.reload(ops_ap_ac)
        # else:
        #     from . import ops_ap_ac
        # # endif

    except Exception as xEx:
        # pass
        print(">>>> Exception importing libs:\n{}".format(str(xEx)))
    # endif
# endif in Blender Context


##################################################################
# Register function
def register():
    try:
        ac_pref.register()
        ac_ops.register()
        ac_props.register()
        ac_ui.register()
        ac_props_camsetcol.register()
        ac_ops_camset.register()
        ac_ui_camsetcol.register()
        ac_ui_camset.register()
        ap_ac_props.register()
        ap_ac_ui.register()
        ops_ap_ac.register()
    except Exception as Ex:
        print("Error registering AnyCam plugin classes.")
        print(Ex)
    # endtry


# enddef


##################################################################
# Unregister function
def unregister():
    try:
        ac_props_camsetcol.unregister()
        ac_ops_camset.unregister()
        ac_ui_camset.unregister()
        ac_ui_camsetcol.unregister()
        ac_ui.unregister()
        ac_props.unregister()
        ac_ops.unregister()
        ac_pref.unregister()
        ap_ac_ui.unregister()
        ap_ac_props.unregister()
        ops_ap_ac.unregister()
    except Exception as Ex:
        print("Error unregistering AnyCam plugin classes.")
        print(Ex)
    # endtry


# enddef
