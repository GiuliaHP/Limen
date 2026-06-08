# ============================================================================
#  rigify_snap_runtime.py
# ----------------------------------------------------------------------------
#  Code de snap IK/FK EXTRAIT VERBATIM de Rigify (Blender Foundation,
#  GPL-2.0-or-later) — fichiers sources :
#     rigify/rig_ui_template.py          (maths communes IK/FK)
#     rigify/utils/animation.py          (keying, transform, mixins, snap FK->IK)
#     rigify/rigs/limbs/limb_rigs.py     (snap IK->FK générique d'un membre)
#     rigify/rigs/limbs/leg.py           (snap IK->FK jambe avec foot-roll)
#
#  But : rendre les opérateurs de snap autonomes (le rig_ui généré par Rigify
#  n'étant pas présent dans la scène). On ne porte QUE le snap "image courante"
#  (RigifySingleUpdateMixin) — pas le bake multi-frames, inutile ici.
#
#  Les classes d'opérateurs sont renommées en POSE_OT_raccoon_* pour ne pas
#  entrer en collision avec un éventuel rig_ui Rigify.
# ============================================================================

import bpy
import math
import json
import traceback
from math import pi
from bpy.props import StringProperty
from mathutils import Euler, Matrix, Quaternion, Vector
from rna_prop_ui import rna_idprop_quote_path


############################
## Math utility functions ##
############################

def perpendicular_vector(v):
    """ Returns a vector that is perpendicular to the one given.
        The returned vector is _not_ guaranteed to be normalized.
    """
    # Create a vector that is not aligned with v.
    if abs(v[0]) < abs(v[1]):
        tv = Vector((1, 0, 0))
    else:
        tv = Vector((0, 1, 0))

    # Use cross product to generate a vector perpendicular to both.
    return v.cross(tv)


def rotation_difference(mat1, mat2):
    """ Returns the shortest-path rotational difference between two matrices.
    """
    q1 = mat1.to_quaternion()
    q2 = mat2.to_quaternion()
    angle = math.acos(min(1, max(-1, q1.dot(q2)))) * 2
    if angle > pi:
        angle = -angle + (2 * pi)
    return angle


def find_min_range(f, start_angle, delta=pi / 8):
    """ finds the range where lies the minimum of function f applied on bone_ik
        and bone_fk at a certain angle.
    """
    angle = start_angle
    while (angle > (start_angle - 2 * pi)) and (angle < (start_angle + 2 * pi)):
        l_dist = f(angle - delta)
        c_dist = f(angle)
        r_dist = f(angle + delta)
        if min((l_dist, c_dist, r_dist)) == c_dist:
            return (angle - delta, angle + delta)
        else:
            angle = angle + delta


def ternarySearch(f, left, right, absolutePrecision):
    """ Find minimum of uni-modal function f() within [left, right]. """
    while True:
        if abs(right - left) < absolutePrecision:
            return (left + right) / 2

        leftThird = left + (right - left) / 3
        rightThird = right - (right - left) / 3

        if f(leftThird) > f(rightThird):
            left = leftThird
        else:
            right = rightThird


#########################################
## "Visual Transform" helper functions ##
#########################################

def get_pose_matrix_in_other_space(mat, pose_bone):
    """ Returns the transform matrix relative to pose_bone's current
        transform space.
    """
    return pose_bone.id_data.convert_space(
        matrix=mat, pose_bone=pose_bone, from_space='POSE', to_space='LOCAL')


def convert_pose_matrix_via_rest_delta(mat, from_bone, to_bone):
    """Convert pose of one bone to another, preserving the rest pose difference."""
    return mat @ from_bone.bone.matrix_local.inverted() @ to_bone.bone.matrix_local


def convert_pose_matrix_via_pose_delta(mat, from_bone, to_bone):
    """Convert pose of one bone to another, preserving the current pose difference."""
    return mat @ from_bone.matrix.inverted() @ to_bone.matrix


def get_local_pose_matrix(pose_bone):
    """ Returns the local transform matrix of the given pose bone. """
    return get_pose_matrix_in_other_space(pose_bone.matrix, pose_bone)


def set_pose_translation(pose_bone, mat):
    """ Sets the pose bone's translation to the given matrix (bone local space). """
    pose_bone.location = mat.to_translation()


def set_pose_rotation(pose_bone, mat):
    """ Sets the pose bone's rotation to the given matrix (bone local space). """
    q = mat.to_quaternion()

    if pose_bone.rotation_mode == 'QUATERNION':
        pose_bone.rotation_quaternion = q
    elif pose_bone.rotation_mode == 'AXIS_ANGLE':
        pose_bone.rotation_axis_angle[0] = q.angle
        pose_bone.rotation_axis_angle[1] = q.axis[0]
        pose_bone.rotation_axis_angle[2] = q.axis[1]
        pose_bone.rotation_axis_angle[3] = q.axis[2]
    else:
        pose_bone.rotation_euler = q.to_euler(pose_bone.rotation_mode)


def set_pose_scale(pose_bone, mat):
    """ Sets the pose bone's scale to the given matrix (bone local space). """
    pose_bone.scale = mat.to_scale()


def match_pose_translation(pose_bone, target_bone):
    mat = get_pose_matrix_in_other_space(target_bone.matrix, pose_bone)
    set_pose_translation(pose_bone, mat)


def match_pose_rotation(pose_bone, target_bone):
    mat = get_pose_matrix_in_other_space(target_bone.matrix, pose_bone)
    set_pose_rotation(pose_bone, mat)


def match_pose_scale(pose_bone, target_bone):
    mat = get_pose_matrix_in_other_space(target_bone.matrix, pose_bone)
    set_pose_scale(pose_bone, mat)


##############################
## IK/FK snapping functions ##
##############################

def correct_rotation(view_layer, bone_ik, target_matrix, *, ctrl_ik=None):
    """ Corrects the ik rotation in ik2fk snapping functions. """
    axis = target_matrix.to_3x3().col[1].normalized()
    ctrl_ik = ctrl_ik or bone_ik

    def distance(angle):
        ctrl_ik.rotation_euler[1] = angle
        view_layer.update()
        return -(bone_ik.vector.normalized().dot(axis))

    if ctrl_ik.rotation_mode in {'QUATERNION', 'AXIS_ANGLE'}:
        ctrl_ik.rotation_mode = 'ZXY'

    start_angle = ctrl_ik.rotation_euler[1]

    alpha_range = find_min_range(distance, start_angle)
    alpha_min = ternarySearch(distance, alpha_range[0], alpha_range[1], pi / 180)

    ctrl_ik.rotation_euler[1] = alpha_min
    view_layer.update()


def correct_scale(view_layer, bone_ik, target_matrix, *, ctrl_ik=None):
    """ Correct the scale of the base IK bone. """
    input_scale = target_matrix.to_scale()
    ctrl_ik = ctrl_ik or bone_ik

    for i in range(3):
        cur_scale = bone_ik.matrix.to_scale()

        ctrl_ik.scale = [
            v * i / c for v, i, c in zip(bone_ik.scale, input_scale, cur_scale)
        ]

        view_layer.update()

        if all(abs((c - i) / i) < 0.01 for i, c in zip(input_scale, cur_scale)):
            break


def match_pole_target(view_layer, ik_first, ik_last, pole, match_bone_matrix, length):
    """ Places an IK chain's pole target to match ik_first's transforms. """
    a = ik_first.matrix.to_translation()
    b = ik_last.matrix.to_translation() + ik_last.vector

    ikv = b - a

    pv = perpendicular_vector(ikv).normalized() * length

    def set_pole(pvi):
        pole_loc = a + (ikv / 2) + pvi
        mat = get_pose_matrix_in_other_space(Matrix.Translation(pole_loc), pole)
        set_pose_translation(pole, mat)
        view_layer.update()

    set_pole(pv)

    angle = rotation_difference(ik_first.matrix, match_bone_matrix)

    pv1 = Matrix.Rotation(angle, 4, ikv) @ pv
    set_pole(pv1)
    ang1 = rotation_difference(ik_first.matrix, match_bone_matrix)

    pv2 = Matrix.Rotation(-angle, 4, ikv) @ pv
    set_pole(pv2)
    ang2 = rotation_difference(ik_first.matrix, match_bone_matrix)

    if ang1 < ang2:
        set_pole(pv1)


######################
## Keyframing tools ##
######################

def get_keying_flags(context):
    "Retrieve the general keyframing flags from user preferences."
    prefs = context.preferences
    ts = context.scene.tool_settings
    flags = set()
    if prefs.edit.use_keyframe_insert_needed:
        flags.add('INSERTKEY_NEEDED')
    if ts.use_keyframe_cycle_aware:
        flags.add('INSERTKEY_CYCLE_AWARE')
    return flags


def get_autokey_flags(context, ignore_keyingset=False):
    "Retrieve the Auto Keyframe flags, or None if disabled."
    ts = context.scene.tool_settings
    if ts.use_keyframe_insert_auto and (ignore_keyingset or not ts.use_keyframe_insert_keyingset):
        flags = get_keying_flags(context)
        if context.preferences.edit.use_keyframe_insert_available:
            flags.add('INSERTKEY_AVAILABLE')
        if ts.auto_keying_mode == 'REPLACE_KEYS':
            flags.add('INSERTKEY_REPLACE')
        return flags
    else:
        return None


def add_flags_if_set(base, new_flags):
    "Add more flags if base is not None."
    if base is None:
        return None
    else:
        return base | new_flags


def get_4d_rot_lock(bone):
    "Retrieve the lock status for 4D rotation."
    if bone.lock_rotations_4d:
        return [bone.lock_rotation_w, *bone.lock_rotation]
    else:
        return [all(bone.lock_rotation)] * 4


def keyframe_transform_properties(obj, bone_name, keyflags, *,
                                  ignore_locks=False, no_loc=False, no_rot=False, no_scale=False):
    "Keyframe transformation properties, avoiding keying locked channels."
    bone = obj.pose.bones[bone_name]

    def keyframe_channels(prop, locks):
        if ignore_locks or not all(locks):
            if ignore_locks or not any(locks):
                bone.keyframe_insert(prop, group=bone_name, options=keyflags)
            else:
                for i, lock in enumerate(locks):
                    if not lock:
                        bone.keyframe_insert(prop, index=i, group=bone_name, options=keyflags)

    if not (no_loc or bone.bone.use_connect):
        keyframe_channels('location', bone.lock_location)

    if not no_rot:
        if bone.rotation_mode == 'QUATERNION':
            keyframe_channels('rotation_quaternion', get_4d_rot_lock(bone))
        elif bone.rotation_mode == 'AXIS_ANGLE':
            keyframe_channels('rotation_axis_angle', get_4d_rot_lock(bone))
        else:
            keyframe_channels('rotation_euler', bone.lock_rotation)

    if not no_scale:
        keyframe_channels('scale', bone.lock_scale)


######################
## Constraint tools ##
######################

def get_constraint_target_matrix(con):
    target = con.target
    if target:
        if target.type == 'ARMATURE' and con.subtarget:
            if con.subtarget in target.pose.bones:
                bone = target.pose.bones[con.subtarget]
                return target.convert_space(
                    pose_bone=bone, matrix=bone.matrix, from_space='POSE', to_space=con.target_space)
        else:
            return target.convert_space(
                matrix=target.matrix_world, from_space='WORLD', to_space=con.target_space)
    return Matrix.Identity(4)


def undo_copy_scale_with_offset(obj, bone, con, old_matrix):
    "Undo the effects of Copy Scale with Offset constraint on a bone matrix."
    inf = con.influence

    if con.mute or inf == 0 or not con.is_valid or not con.use_offset or con.use_add:
        return old_matrix

    tgt_matrix = get_constraint_target_matrix(con)
    tgt_scale = tgt_matrix.to_scale()
    use = [con.use_x, con.use_y, con.use_z]

    if con.use_make_uniform:
        if con.use_x and con.use_y and con.use_z:
            total = tgt_matrix.determinant()
        else:
            total = 1
            for i, use in enumerate(use):
                if use:
                    total *= tgt_scale[i]

        tgt_scale = [abs(total) ** (1. / 3.)] * 3
    else:
        for i, use in enumerate(use):
            if not use:
                tgt_scale[i] = 1

    scale_delta = [
        1 / (1 + (math.pow(x, con.power) - 1) * inf)
        for x in tgt_scale
    ]

    return old_matrix @ Matrix.Diagonal([*scale_delta, 1])


def undo_copy_scale_constraints(obj, bone, matrix):
    "Undo the effects of all Copy Scale with Offset constraints on a bone matrix."
    for con in reversed(bone.constraints):
        if con.type == 'COPY_SCALE':
            matrix = undo_copy_scale_with_offset(obj, bone, con, matrix)
    return matrix


###############################
## Assign and keyframe tools ##
###############################

def set_custom_property_value(obj, bone_name, prop, value, *, keyflags=None):
    "Assign the value of a custom property, and optionally keyframe it."
    from rna_prop_ui import rna_idprop_ui_prop_update
    bone = obj.pose.bones[bone_name]
    bone[prop] = value
    rna_idprop_ui_prop_update(bone, prop)
    if keyflags is not None:
        bone.keyframe_insert(rna_idprop_quote_path(prop), group=bone.name, options=keyflags)


def get_transform_matrix(obj, bone_name, *, space='POSE', with_constraints=True):
    "Retrieve the matrix of the bone before or after constraints in the given space."
    bone = obj.pose.bones[bone_name]
    if with_constraints:
        return obj.convert_space(pose_bone=bone, matrix=bone.matrix, from_space='POSE', to_space=space)
    else:
        return obj.convert_space(pose_bone=bone, matrix=bone.matrix_basis, from_space='LOCAL', to_space=space)


def get_chain_transform_matrices(obj, bone_names, **options):
    return [get_transform_matrix(obj, name, **options) for name in bone_names]


def set_transform_from_matrix(obj, bone_name, matrix, *, space='POSE', undo_copy_scale=False,
                              ignore_locks=False, no_loc=False, no_rot=False, no_scale=False, keyflags=None):
    """Apply the matrix to the bone, honoring locked channels, mode and certain constraints."""
    bone = obj.pose.bones[bone_name]

    def restore_channels(prop, old_vec, locks, extra_lock):
        if extra_lock or (not ignore_locks and all(locks)):
            setattr(bone, prop, old_vec)
        else:
            if not ignore_locks and any(locks):
                new_vec = Vector(getattr(bone, prop))

                for i, lock in enumerate(locks):
                    if lock:
                        new_vec[i] = old_vec[i]

                setattr(bone, prop, new_vec)

    # Save the old values of the properties
    old_loc = Vector(bone.location)
    old_rot_euler = Vector(bone.rotation_euler)
    old_rot_quat = Vector(bone.rotation_quaternion)
    old_rot_axis = Vector(bone.rotation_axis_angle)
    old_scale = Vector(bone.scale)

    # Compute and assign the local matrix
    if space != 'LOCAL':
        matrix = obj.convert_space(pose_bone=bone, matrix=matrix, from_space=space, to_space='LOCAL')

    if undo_copy_scale:
        matrix = undo_copy_scale_constraints(obj, bone, matrix)

    bone.matrix_basis = matrix

    # Restore locked properties
    restore_channels('location', old_loc, bone.lock_location, no_loc or bone.bone.use_connect)

    if bone.rotation_mode == 'QUATERNION':
        restore_channels('rotation_quaternion', old_rot_quat, get_4d_rot_lock(bone), no_rot)
        bone.rotation_axis_angle = old_rot_axis
        bone.rotation_euler = old_rot_euler
    elif bone.rotation_mode == 'AXIS_ANGLE':
        bone.rotation_quaternion = old_rot_quat
        restore_channels('rotation_axis_angle', old_rot_axis, get_4d_rot_lock(bone), no_rot)
        bone.rotation_euler = old_rot_euler
    else:
        bone.rotation_quaternion = old_rot_quat
        bone.rotation_axis_angle = old_rot_axis
        restore_channels('rotation_euler', old_rot_euler, bone.lock_rotation, no_rot)

    restore_channels('scale', old_scale, bone.lock_scale, no_scale)

    # Keyframe properties
    if keyflags is not None:
        keyframe_transform_properties(
            obj, bone_name, keyflags, ignore_locks=ignore_locks,
            no_loc=no_loc, no_rot=no_rot, no_scale=no_scale
        )


def set_chain_transforms_from_matrices(context, obj, bone_names, matrices, **options):
    for bone, matrix in zip(bone_names, matrices):
        set_transform_from_matrix(obj, bone, matrix, **options)
        context.view_layer.update()


#######################################
## Operator framework (single frame) ##
#######################################

class RigifyOperatorMixinBase:
    bl_options = {'UNDO', 'INTERNAL'}

    def init_invoke(self, context):
        "Override to initialize the operator before invoke."

    def init_execute(self, context):
        "Override to initialize the operator before execute."

    def before_save_state(self, context, rig):
        "Override to prepare for saving state."

    def after_save_state(self, context, rig):
        "Override to undo before_save_state."


class RigifySingleUpdateMixin(RigifyOperatorMixinBase):
    """Basic framework for an operator that updates only the current frame."""

    def execute(self, context):
        self.init_execute(context)
        obj = context.active_object
        self.keyflags = get_autokey_flags(context, ignore_keyingset=True)
        self.keyflags_switch = add_flags_if_set(self.keyflags, {'INSERTKEY_AVAILABLE'})

        try:
            try:
                self.before_save_state(context, obj)
                state = self.save_frame_state(context, obj)
            finally:
                self.after_save_state(context, obj)

            self.apply_frame_state(context, obj, state)

        except Exception as e:
            traceback.print_exc()
            self.report({'ERROR'}, 'Exception: ' + str(e))

        return {'FINISHED'}

    def invoke(self, context, event):
        self.init_invoke(context)

        if hasattr(self, 'draw'):
            return context.window_manager.invoke_props_popup(self, event)
        else:
            return self.execute(context)


#############################
## Generic Snap (FK to IK) ##
#############################

class RigifyGenericSnapBase:
    input_bones:   StringProperty(name="Input Chain")
    output_bones:  StringProperty(name="Output Chain")
    ctrl_bones:    StringProperty(name="Input Controls")

    tooltip:         StringProperty(name="Tooltip", default="FK to IK")
    locks:           bpy.props.BoolVectorProperty(name="Locked", size=3, default=[False, False, False])
    undo_copy_scale: bpy.props.BoolProperty(name="Undo Copy Scale", default=False)

    def init_execute(self, context):
        self.input_bone_list = json.loads(self.input_bones)
        self.output_bone_list = json.loads(self.output_bones)
        self.ctrl_bone_list = json.loads(self.ctrl_bones)

    def save_frame_state(self, context, obj):
        return get_chain_transform_matrices(obj, self.input_bone_list)

    def apply_frame_state(self, context, obj, matrices):
        set_chain_transforms_from_matrices(
            context, obj, self.output_bone_list, matrices,
            undo_copy_scale=self.undo_copy_scale, keyflags=self.keyflags,
            no_loc=self.locks[0], no_rot=self.locks[1], no_scale=self.locks[2],
        )


class POSE_OT_raccoon_generic_snap(RigifyGenericSnapBase, RigifySingleUpdateMixin, bpy.types.Operator):
    bl_idname = "pose.raccoon_generic_snap"
    bl_label = "Snap Bones"
    bl_description = "Snap on the current frame"

    @classmethod
    def description(cls, context, props):
        return "Snap " + props.tooltip + " on the current frame"


########################
## Limb Snap IK to FK ##
########################

class RigifyLimbIk2FkBase:
    prop_bone:    StringProperty(name="Settings Bone")
    pole_prop:    StringProperty(name="Pole target switch", default="pole_vector")
    fk_bones:     StringProperty(name="FK Bone Chain")
    ik_bones:     StringProperty(name="IK Result Bone Chain")
    ctrl_bones:   StringProperty(name="IK Controls")
    tail_bones:   StringProperty(name="Tail IK Controls", default="[]")
    extra_ctrls:  StringProperty(name="Extra IK Controls")

    def init_execute(self, context):
        if self.fk_bones:
            self.fk_bone_list = json.loads(self.fk_bones)
        self.ik_bone_list = json.loads(self.ik_bones)
        self.ctrl_bone_list = json.loads(self.ctrl_bones)
        self.tail_bone_list = json.loads(self.tail_bones)
        self.extra_ctrl_list = json.loads(self.extra_ctrls)

    def get_use_pole(self, obj):
        bone = obj.pose.bones[self.prop_bone]
        return self.pole_prop in bone and bone[self.pole_prop]

    def save_frame_state(self, context, obj):
        return get_chain_transform_matrices(obj, self.fk_bone_list)

    def compute_base_rotation(self, context, ik_bones, ctrl_bones, matrices, use_pole):
        context.view_layer.update()

        if use_pole:
            match_pole_target(
                context.view_layer,
                ik_bones[0], ik_bones[1], ctrl_bones[1], matrices[0],
                (ik_bones[0].length + ik_bones[1].length)
            )

        else:
            correct_rotation(context.view_layer, ik_bones[0], matrices[0], ctrl_ik=ctrl_bones[0])

    def assign_middle_controls(self, context, obj, matrices, ik_bones, ctrl_bones, *, lock=False, keyflags=None):
        for mat, ik, ctrl in reversed(list(zip(matrices[2:-1], ik_bones[2:-1], ctrl_bones[2:-1]))):
            ctrl.bone.use_inherit_rotation = not lock
            ctrl.bone.inherit_scale = 'NONE' if lock else 'FULL'
            context.view_layer.update()
            mat = convert_pose_matrix_via_rest_delta(mat, ik, ctrl)
            set_transform_from_matrix(obj, ctrl.name, mat, keyflags=keyflags)

    def assign_extra_controls(self, context, obj, all_matrices, ik_bones, ctrl_bones):
        for extra in self.extra_ctrl_list:
            set_transform_from_matrix(
                obj, extra, Matrix.Identity(4), space='LOCAL', keyflags=self.keyflags
            )

    def apply_frame_state(self, context, obj, all_matrices):
        ik_bones = [obj.pose.bones[k] for k in self.ik_bone_list]
        ctrl_bones = [obj.pose.bones[k] for k in self.ctrl_bone_list]
        tail_bones = [obj.pose.bones[k] for k in self.tail_bone_list]

        assert len(all_matrices) >= len(ik_bones) + len(tail_bones)

        matrices = all_matrices[0:len(ik_bones)]
        tail_matrices = all_matrices[len(ik_bones):]

        use_pole = self.get_use_pole(obj)

        # Remove foot heel transform, if present
        self.assign_extra_controls(context, obj, all_matrices, ik_bones, ctrl_bones)

        context.view_layer.update()

        # Set the end control position
        end_mat = convert_pose_matrix_via_pose_delta(matrices[-1], ik_bones[-1], ctrl_bones[-1])

        set_transform_from_matrix(
            obj, self.ctrl_bone_list[-1], end_mat, keyflags=self.keyflags,
            undo_copy_scale=True,
        )

        # Set the base bone position
        ctrl_bones[0].matrix_basis = Matrix.Identity(4)

        set_transform_from_matrix(
            obj, self.ctrl_bone_list[0], matrices[0],
            no_scale=True, no_rot=use_pole,
        )

        # Lock middle control transforms (first pass)
        self.assign_middle_controls(context, obj, matrices, ik_bones, ctrl_bones, lock=True)

        # Adjust the base bone state
        self.compute_base_rotation(context, ik_bones, ctrl_bones, matrices, use_pole)

        correct_scale(context.view_layer, ik_bones[0], matrices[0], ctrl_ik=ctrl_bones[0])

        # Assign middle control transforms (final pass)
        self.assign_middle_controls(context, obj, matrices, ik_bones, ctrl_bones, keyflags=self.keyflags)

        # Assign tail control transforms
        for mat, ctrl in zip(tail_matrices, tail_bones):
            context.view_layer.update()
            set_transform_from_matrix(obj, ctrl.name, mat, keyflags=self.keyflags)

        # Keyframe controls
        if self.keyflags is not None:
            if use_pole:
                keyframe_transform_properties(
                    obj, self.ctrl_bone_list[1], self.keyflags,
                    no_rot=True, no_scale=True,
                )

            keyframe_transform_properties(
                obj, self.ctrl_bone_list[0], self.keyflags,
                no_rot=use_pole,
            )


class POSE_OT_raccoon_limb_ik2fk(RigifyLimbIk2FkBase, RigifySingleUpdateMixin, bpy.types.Operator):
    bl_idname = "pose.raccoon_limb_ik2fk"
    bl_label = "Snap IK->FK"
    bl_description = "Snap the IK chain to FK result"


#######################
## Leg Snap IK to FK ##
#######################

class RigifyLegRollIk2FkBase(RigifyLimbIk2FkBase):
    heel_control: StringProperty(name="Heel")
    use_roll:     bpy.props.BoolVectorProperty(
        name="Use Roll", size=3, default=(True, True, False),
        description="Specifies which rotation axes of the heel roll control to use"
    )

    MODES = {
        'ZXY': ((0, 2), (1, 0, 2)),
        'XZY': ((2, 0), (2, 0, 1)),
    }

    def save_frame_state(self, context, obj):
        return get_chain_transform_matrices(obj, self.fk_bone_list + self.ctrl_bone_list[-1:])

    def assign_extra_controls(self, context, obj, all_matrices, ik_bones, ctrl_bones):
        for extra in self.extra_ctrl_list:
            set_transform_from_matrix(
                obj, extra, Matrix.Identity(4), space='LOCAL', keyflags=self.keyflags
            )

        if any(self.use_roll):
            foot_matrix = all_matrices[len(ik_bones) - 1]
            ctrl_matrix = all_matrices[len(self.fk_bone_list)]
            heel_bone = obj.pose.bones[self.heel_control]
            foot_bone = ctrl_bones[-1]

            # Relative rotation of heel from orientation of master IK control
            # to actual foot orientation.
            heel_rest = convert_pose_matrix_via_rest_delta(ctrl_matrix, foot_bone, heel_bone)
            heel_rot = convert_pose_matrix_via_rest_delta(foot_matrix, ik_bones[-1], heel_bone)

            # Decode the euler decomposition mode
            rot_mode = heel_bone.rotation_mode
            indices, use_map = self.MODES[rot_mode]
            use_roll = [self.use_roll[i] for i in use_map]
            roll, turn = indices

            # If the last rotation (yaw) is unused, move it to be first for better result
            if not use_roll[turn]:
                rot_mode = rot_mode[1:] + rot_mode[0:1]

            local_rot = (heel_rest.inverted() @ heel_rot).to_euler(rot_mode)

            heel_bone.rotation_euler = [
                (val if use else 0) for val, use in zip(local_rot, use_roll)
            ]

            if self.keyflags is not None:
                keyframe_transform_properties(
                    obj, self.heel_control, self.keyflags, no_loc=True, no_scale=True
                )

            if 'Toe_Roll' in heel_bone and self.tail_bone_list:
                toe_matrix = all_matrices[len(ik_bones)]
                toe_bone = obj.pose.bones[self.tail_bone_list[0]]

                # Compute relative rotation of heel determined by toe
                heel_rot_toe = convert_pose_matrix_via_rest_delta(toe_matrix, toe_bone, heel_bone)
                toe_rot = (heel_rest.inverted() @ heel_rot_toe).to_euler(rot_mode)

                # Determine how much of the already computed heel rotation seems to be applied
                heel_rot = list(heel_bone.rotation_euler)
                heel_rot[roll] = max(0.0, heel_rot[roll])

                # This relies on toe roll interpolation being done in Euler space
                ratios = [
                    toe_rot[i] / heel_rot[i] for i in (roll, turn)
                    if use_roll[i] and heel_rot[i] * toe_rot[i] > 0
                ]

                val = min(1.0, max(0.0, min(ratios) if ratios else 0.0))
                if val < 1e-5:
                    val = 0.0

                set_custom_property_value(
                    obj, heel_bone.name, 'Toe_Roll', val, keyflags=self.keyflags)

    def draw(self, context):
        row = self.layout.row(align=True)
        row.label(text="Use:")
        row.prop(self, 'use_roll', index=0, text="Rock", toggle=True)
        row.prop(self, 'use_roll', index=1, text="Roll", toggle=True)
        row.prop(self, 'use_roll', index=2, text="Yaw", toggle=True)


class POSE_OT_raccoon_leg_roll_ik2fk(RigifyLegRollIk2FkBase, RigifySingleUpdateMixin, bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_idname = "pose.raccoon_leg_roll_ik2fk"
    bl_label = "Snap IK->FK With Roll"
    bl_description = "Snap the IK chain to FK result, using foot roll to preserve the current IK " \
                     "control orientation as much as possible"

    def invoke(self, context, event):
        # On déclenche directement (pas de popup d'axes de roll)
        self.init_invoke(context)
        return self.execute(context)


# Exposé pour l'enregistrement par le package operators
classes = (
    POSE_OT_raccoon_generic_snap,
    POSE_OT_raccoon_limb_ik2fk,
    POSE_OT_raccoon_leg_roll_ik2fk,
)
