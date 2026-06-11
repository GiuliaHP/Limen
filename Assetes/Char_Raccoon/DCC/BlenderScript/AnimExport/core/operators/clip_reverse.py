import bpy
from bpy.props import StringProperty
from .. import exporter
from ..clips import _resolve_target, _next_order, iter_fcurves, _select


class ANIM_OT_raccoon_clip_reverse(bpy.types.Operator):
    """Crée une copie du clip jouée à l'envers"""
    bl_idname = "anim.raccoon_clip_reverse"
    bl_label = "Reverse (à l'envers)"
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
        rng = exporter._action_frame_range(base)
        if not rng:
            self.report({'WARNING'}, "Clip vide : rien à inverser.")
            return {'CANCELLED'}
        start, end = rng
        total = start + end

        rev = base.copy()
        rev.name = base.name + "_Reverse"
        rev.use_fake_user = True
        rev.raccoon_order = _next_order()

        for fc in iter_fcurves(rev):
            for kp in fc.keyframe_points:
                hl = kp.handle_left.copy()
                hr = kp.handle_right.copy()
                kp.co.x = total - kp.co.x
                kp.handle_left.x = total - hr.x
                kp.handle_left.y = hr.y
                kp.handle_right.x = total - hl.x
                kp.handle_right.y = hl.y
            fc.update()

        _select(context, rev)
        self.report({'INFO'}, f"Reverse : {rev.name}")
        return {'FINISHED'}
