import bpy
import importlib

# On importe UNIQUEMENT notre nouveau panneau unique
from . import main_panel

importlib.reload(main_panel)

classes = (
    main_panel.VIEW3D_PT_raccoon_main_ui,
)


def register_props():
    # Propriétés d'état (sections dépliées/repliées)
    main_panel.register_props()


def unregister_props():
    main_panel.unregister_props()