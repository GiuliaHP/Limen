import bpy
import sys
import os
import importlib

os.system('cls')

# 1. Racine commune des outils
blend_dir = os.path.dirname(bpy.data.filepath)
script_root = os.path.join(blend_dir, "BlenderScript")
if script_root not in sys.path:
    sys.path.append(script_root)

from AnimExport import anim_export_core as core
importlib.reload(core)
core.reload_core()


def register():
    core.register()


def unregister():
    core.unregister()


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass

    register()
    print("AnimExport chargé : panneau 'Raccoon Anim Export' dispo (onglet Item).")
