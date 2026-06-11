import importlib

# Un fichier par élément d'UI (SOLID)
from . import clip_list
from . import clip_menu
from . import panel

_modules = (clip_list, clip_menu, panel)
for _m in _modules:
    importlib.reload(_m)

classes = (
    clip_list.ANIM_UL_raccoon_clips,
    clip_menu.ANIM_MT_raccoon_clip_specials,
    panel.VIEW3D_PT_raccoon_anim_export,
)
