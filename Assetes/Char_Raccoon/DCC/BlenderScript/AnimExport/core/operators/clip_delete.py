import bpy
from bpy.props import StringProperty
from ..clips import _resolve_target, get_anim_source, INDEX_PROP


class ANIM_OT_raccoon_clip_delete(bpy.types.Operator):
    """Supprime le clip"""
    bl_idname = "anim.raccoon_clip_delete"
    bl_label = "Supprimer le clip"
    bl_options = {'REGISTER', 'UNDO'}

    action_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return bool(bpy.data.actions)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        action = _resolve_target(self, context)
        if not action:
            self.report({'WARNING'}, "Aucun clip ciblé.")
            return {'CANCELLED'}
        name = action.name
        idx = getattr(context.scene, INDEX_PROP, 0)

        src = get_anim_source()
        if src and src.animation_data and src.animation_data.action == action:
            src.animation_data.action = None

        bpy.data.actions.remove(action)
        setattr(context.scene, INDEX_PROP, max(0, min(idx, len(bpy.data.actions) - 1)))
        self.report({'INFO'}, f"Supprimé : {name}")
        return {'FINISHED'}
