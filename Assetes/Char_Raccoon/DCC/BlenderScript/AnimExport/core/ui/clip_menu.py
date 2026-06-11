import bpy
from ..clips import active_clip_action


class ANIM_MT_raccoon_clip_specials(bpy.types.Menu):
    """Menu ▾ d'actions sur le clip — 100% à nous, sans entrée native
    (un Menu invoqué en clic GAUCHE n'a pas d'injection native du C Blender)."""
    bl_idname = "ANIM_MT_raccoon_clip_specials"
    bl_label = "Actions sur le clip"

    def draw(self, context):
        action = active_clip_action(context)
        layout = self.layout
        layout.label(text=action.name if action else "Clip", icon='ACTION')
        layout.separator()
        layout.operator("anim.raccoon_clip_duplicate", icon='DUPLICATE')
        layout.operator("anim.raccoon_clip_mirror", icon='MOD_MIRROR')
        layout.operator("anim.raccoon_clip_reverse", icon='LOOP_BACK')
        layout.separator()
        layout.operator("anim.raccoon_clip_delete", icon='TRASH')
