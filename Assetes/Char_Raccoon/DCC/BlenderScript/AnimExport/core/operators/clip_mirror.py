import bpy
from bpy.props import StringProperty
from .. import config
from .. import exporter
from ..clips import get_anim_source, _resolve_target, _next_order, _select


class ANIM_OT_raccoon_clip_mirror(bpy.types.Operator):
    """Crée une copie miroir L<->R du clip (pose-flip natif, baked frame par frame)"""
    bl_idname = "anim.raccoon_clip_mirror"
    bl_label = "Mirror L<->R"
    bl_options = {'REGISTER', 'UNDO'}

    action_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return bool(bpy.data.actions)

    def execute(self, context):
        src = get_anim_source()
        base = _resolve_target(self, context)
        if not src:
            self.report({'ERROR'}, f"'{config.ANIM_SOURCE}' introuvable.")
            return {'CANCELLED'}
        if not base:
            self.report({'WARNING'}, "Aucun clip ciblé.")
            return {'CANCELLED'}
        rng = exporter._action_frame_range(base)
        if not rng:
            self.report({'WARNING'}, "Clip vide : rien à miroiter.")
            return {'CANCELLED'}
        start, end = rng

        scene = context.scene
        saved_frame = scene.frame_current
        saved_active = context.view_layer.objects.active
        saved_sel = [o for o in context.view_layer.objects if o.select_get()]

        mir = base.copy()
        mir.name = base.name + "_Mirror"
        mir.use_fake_user = True
        mir.raccoon_order = _next_order()
        exporter._assign_action(src, mir)

        try:
            for o in context.view_layer.objects:
                o.select_set(False)
            src.select_set(True)
            context.view_layer.objects.active = src
            if src.mode != 'POSE':
                bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='SELECT')

            for f in range(start, end + 1):
                scene.frame_set(f)
                bpy.ops.pose.copy()
                bpy.ops.pose.paste(flipped=True)
                for pb in src.pose.bones:
                    if pb.bone.select:
                        self._key_bone(pb, f)
        except Exception as e:
            self.report({'ERROR'}, f"Mirror échoué : {e}")
        finally:
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass
            scene.frame_set(saved_frame)
            for o in context.view_layer.objects:
                o.select_set(o in saved_sel)
            if saved_active:
                context.view_layer.objects.active = saved_active

        _select(context, mir)
        self.report({'INFO'}, f"Mirror : {mir.name}  (⚠ props custom IK/FK non miroitées)")
        return {'FINISHED'}

    @staticmethod
    def _key_bone(pb, frame):
        pb.keyframe_insert("location", frame=frame)
        if pb.rotation_mode == 'QUATERNION':
            pb.keyframe_insert("rotation_quaternion", frame=frame)
        elif pb.rotation_mode == 'AXIS_ANGLE':
            pb.keyframe_insert("rotation_axis_angle", frame=frame)
        else:
            pb.keyframe_insert("rotation_euler", frame=frame)
        pb.keyframe_insert("scale", frame=frame)
