import bpy
from .. import exporter
from ..clips import get_anim_source, _next_order, _select


class ANIM_OT_raccoon_clip_new(bpy.types.Operator):
    """Crée un nouveau clip (Action) vide sur le rig de contrôle"""
    bl_idname = "anim.raccoon_clip_new"
    bl_label = "Nouveau clip"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        src = get_anim_source(context)
        if not src:
            self.report({'ERROR'}, "Sélectionne un objet du perso (RIG-<Char>)")
            return {'CANCELLED'}
        action = bpy.data.actions.new("NewClip")
        action.use_fake_user = True
        action.raccoon_order = _next_order()
        exporter._assign_action(src, action)
        _select(context, action)
        return {'FINISHED'}
