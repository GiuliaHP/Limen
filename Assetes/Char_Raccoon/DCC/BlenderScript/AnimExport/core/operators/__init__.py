import importlib

# Un fichier par opérateur (SOLID)
from . import clip_new
from . import clip_duplicate
from . import clip_delete
from . import clip_reverse
from . import clip_mirror
from . import clip_move
from . import clip_delete_key
from . import export_all

_modules = (
    clip_new, clip_duplicate, clip_delete, clip_reverse,
    clip_mirror, clip_move, clip_delete_key, export_all,
)
for _m in _modules:
    importlib.reload(_m)

classes = (
    clip_new.ANIM_OT_raccoon_clip_new,
    clip_duplicate.ANIM_OT_raccoon_clip_duplicate,
    clip_delete.ANIM_OT_raccoon_clip_delete,
    clip_reverse.ANIM_OT_raccoon_clip_reverse,
    clip_mirror.ANIM_OT_raccoon_clip_mirror,
    clip_move.ANIM_OT_raccoon_clip_move,
    clip_delete_key.ANIM_OT_raccoon_clip_delete_key,
    export_all.ANIM_OT_raccoon_export_all,
)
