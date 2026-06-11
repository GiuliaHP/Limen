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

from AnimExport import core
importlib.reload(core)
core.reload_core()


def register():
    core.register()


def unregister():
    core.unregister()


def _self_register():
    """Coche 'Register' (use_module) sur ce texte pour qu'il se relance
    automatiquement à chaque ouverture du .blend. Idempotent."""
    me = None
    # 1. Si lancé depuis le Text Editor : on récupère le texte actif
    try:
        me = bpy.context.space_data.text
    except Exception:
        me = None
    # 2. Sinon (autre contexte) : on le retrouve par son nom
    if me is None:
        me = bpy.data.texts.get("Main_AnimExport.py")

    if me and not me.use_module:
        me.use_module = True
        print(f"[Raccoon] '{me.name}' marqué Register (use_module=True). Pense à sauver le .blend.")


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass

    register()
    _self_register()
    print("AnimExport chargé : panneau 'Raccoon Anim Export' dispo (onglet Item).")
