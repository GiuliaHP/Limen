import bpy
import importlib

from . import config
from . import character
from . import exporter
from . import unity_anim
from . import clips
from . import operators
from . import ui


def reload_core():
    """Recharge les sous-modules (TD : nettoie la RAM entre deux runs)."""
    # Purge complète du paquet générique : delete+reimport (robuste si un sous-module
    # a été supprimé/renommé — un importlib.reload planterait sur 'spec not found').
    import sys
    for _n in [n for n in list(sys.modules)
               if n == "blender_unity_anim" or n.startswith("blender_unity_anim.")]:
        del sys.modules[_n]
    importlib.reload(config)
    importlib.reload(character)
    importlib.reload(exporter)
    importlib.reload(unity_anim)
    importlib.reload(clips)
    importlib.reload(operators)
    importlib.reload(ui)


def _all_classes():
    # Opérateurs puis UI (Panel/UIList/Menu)
    return (*operators.classes, *ui.classes)


def register():
    clips.register_props()
    for cls in _all_classes():
        # Hack TD : on désenregistre une éventuelle ancienne version
        if hasattr(bpy.types, cls.__name__):
            try: bpy.utils.unregister_class(getattr(bpy.types, cls.__name__))
            except Exception: pass
        bpy.utils.register_class(cls)
    clips.register_context_menu()
    clips.register_keymaps()


def unregister():
    clips.unregister_keymaps()
    clips.unregister_context_menu()
    for cls in reversed(_all_classes()):
        try: bpy.utils.unregister_class(cls)
        except Exception: pass
    clips.unregister_props()
