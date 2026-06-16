import bpy
import re
from bpy.props import StringProperty
from ..clips import get_anim_source, _resolve_target, _next_order, _select


# ===========================================================================
#  Miroir par INVERSION DES F-CURVES (pas de bake frame par frame).
#  - La courbe d'un os ".L" est déplacée sur l'os ".R" (et inversement),
#    via bpy.utils.flip_name (gère .L/.R, _L/_R, left/right, .l/.r…).
#  - Les valeurs sont négées selon le canal (miroir plan YZ, axe X) :
#       location        -> X  (index 0)
#       rotation_euler  -> Y,Z (index 1,2)
#       rotation_quat   -> Y,Z (index 2,3)
#       scale / props   -> rien
#  - Les clefs posées (timing + handles) sont conservées : aucune clef ajoutée.
#  - Les custom props par côté (IK/FK…) suivent le flip_name -> miroir complet.
#  - Un os central (pas de .L/.R) est miroité sur place (data_path inchangé).
#  - Le côté non animé n'a aucune courbe -> il reste au repos.
# ===========================================================================


def _mirror_factor(data_path, array_index):
    """Multiplicateur de valeur pour ce canal (miroir plan YZ)."""
    if data_path.endswith('.location'):
        return -1.0 if array_index == 0 else 1.0
    if data_path.endswith('.rotation_euler'):
        return -1.0 if array_index in (1, 2) else 1.0
    if data_path.endswith('.rotation_quaternion'):
        return -1.0 if array_index in (2, 3) else 1.0
    if data_path.endswith('.rotation_axis_angle'):
        return -1.0 if array_index in (2, 3) else 1.0
    return 1.0


def _flip_data_path(data_path):
    """Échange le côté du nom d'os dans pose.bones[\"...\"]."""
    m = re.match(r'pose\.bones\["(.+?)"\](.*)', data_path)
    if not m:
        return data_path
    flipped = bpy.utils.flip_name(m.group(1))
    return f'pose.bones["{flipped}"]{m.group(2)}'


def _channelbags(action):
    """Tous les channelbags (API slotted 4.4+), sinon []."""
    out = []
    layers = getattr(action, "layers", None)
    if layers:
        for layer in layers:
            for strip in layer.strips:
                if getattr(strip, "type", None) != 'KEYFRAME':
                    continue
                for slot in action.slots:
                    cb = strip.channelbag(slot)
                    if cb:
                        out.append(cb)
    return out


def _snap_fcurve(fc):
    keys = []
    for kp in fc.keyframe_points:
        keys.append((
            (kp.co[0], kp.co[1]),
            (kp.handle_left[0], kp.handle_left[1]),
            (kp.handle_right[0], kp.handle_right[1]),
            kp.handle_left_type, kp.handle_right_type,
            kp.interpolation, kp.easing,
        ))
    return (fc.data_path, fc.array_index, fc.extrapolation, keys)


def _fcurves_of(action):
    """(liste_fcurves, fonction_new, fonction_remove) pour slotted ou legacy."""
    cbs = _channelbags(action)
    if cbs:
        cb = cbs[0]
        return list(cb.fcurves), cb.fcurves.new, cb.fcurves.remove
    if hasattr(action, "fcurves"):
        return list(action.fcurves), action.fcurves.new, action.fcurves.remove
    return [], None, None


def mirror_action_fcurves(base, mir):
    """Remplit `mir` (copie de `base`) avec les courbes miroitées. Renvoie le nb de courbes."""
    base_fcs, _, _ = _fcurves_of(base)
    snaps = [_snap_fcurve(fc) for fc in base_fcs]

    mir_fcs, new_fc, remove_fc = _fcurves_of(mir)
    if new_fc is None:
        return 0
    for fc in mir_fcs:                       # repartir d'un channelbag vide
        remove_fc(fc)

    count = 0
    for data_path, array_index, extrap, keys in snaps:
        dp = _flip_data_path(data_path)
        factor = _mirror_factor(data_path, array_index)
        try:
            fc = new_fc(dp, index=array_index)
        except RuntimeError:
            continue                         # canal en double (rare) -> on saute
        fc.extrapolation = extrap
        kps = fc.keyframe_points
        kps.add(len(keys))
        for i, (co, hl, hr, hlt, hrt, interp, easing) in enumerate(keys):
            kp = kps[i]
            kp.co          = (co[0], co[1] * factor)
            kp.handle_left  = (hl[0], hl[1] * factor)
            kp.handle_right = (hr[0], hr[1] * factor)
            kp.handle_left_type  = hlt
            kp.handle_right_type = hrt
            kp.interpolation = interp
            kp.easing = easing
        fc.update()
        count += 1
    return count


class ANIM_OT_raccoon_clip_mirror(bpy.types.Operator):
    """Crée une copie miroir L<->R du clip (inversion des F-curves, clefs conservées)"""
    bl_idname = "anim.raccoon_clip_mirror"
    bl_label = "Mirror L<->R"
    bl_options = {'REGISTER', 'UNDO'}

    action_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return bool(bpy.data.actions)

    def execute(self, context):
        src = get_anim_source(context)
        base = _resolve_target(self, context)
        if not src:
            self.report({'ERROR'}, "Sélectionne un objet du perso (RIG-<Char>)")
            return {'CANCELLED'}
        if not base:
            self.report({'WARNING'}, "Aucun clip ciblé.")
            return {'CANCELLED'}

        mir = base.copy()
        mir.name = base.name + "_Mirror"
        mir.use_fake_user = True
        mir.raccoon_order = _next_order()

        n = mirror_action_fcurves(base, mir)
        if n == 0:
            bpy.data.actions.remove(mir)
            self.report({'WARNING'}, "Clip sans courbe : rien à miroiter.")
            return {'CANCELLED'}

        _select(context, mir)
        self.report({'INFO'}, f"Mirror : {mir.name}  ({n} courbes inversées)")
        return {'FINISHED'}
