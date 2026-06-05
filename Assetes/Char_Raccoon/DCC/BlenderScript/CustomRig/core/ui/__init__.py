import bpy
import importlib

# On importe UNIQUEMENT notre nouveau panneau unique
from . import main_panel

importlib.reload(main_panel)

classes = (
    main_panel.VIEW3D_PT_raccoon_main_ui,
)

def register():
    for cls in classes:
        if hasattr(bpy.types, cls.__name__):
            try: bpy.utils.unregister_class(getattr(bpy.types, cls.__name__))
            except Exception: pass
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        try: bpy.utils.unregister_class(cls)
        except Exception: pass