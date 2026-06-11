import bpy
from bpy.props import StringProperty
from ..clips import _resolve_target, _next_order, _select


class ANIM_OT_raccoon_clip_duplicate(bpy.types.Operator):
    """Duplique le clip"""
    bl_idname = "anim.raccoon_clip_duplicate"
    bl_label = "Dupliquer le clip"
    bl_options = {'REGISTER', 'UNDO'}

    action_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return bool(bpy.data.actions)

    def execute(self, context):
        base = _resolve_target(self, context)
        if not base:
            self.report({'WARNING'}, "Aucun clip ciblé.")
            return {'CANCELLED'}
        new = base.copy()
        new.name = base.name + "_copy"
        new.use_fake_user = True
        new.raccoon_order = _next_order()
        _select(context, new)
        self.report({'INFO'}, f"Dupliqué : {new.name}")
        return {'FINISHED'}
