import bpy
import importlib

from . import config
from . import exporter
from . import clips
from . import operators
from . import ui


def reload_core():
    """Recharge les sous-modules (TD : nettoie la RAM entre deux runs)."""
    importlib.reload(config)
    importlib.reload(exporter)
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
