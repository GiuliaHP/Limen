import bpy
import json
from bpy.props import StringProperty
from ..constants import IKFK_DATA


class POSE_OT_raccoon_ikfk_snap(bpy.types.Operator):
    """Snap IK/FK du membre courant (moteur Rigify embarqué, autonome)"""
    bl_idname = "pose.raccoon_ikfk_snap"
    bl_label = "Snap IK/FK"
    bl_options = {'UNDO', 'INTERNAL'}

    # Clé du membre dans IKFK_DATA : "Arm L", "Arm R", "Leg L", "Leg R"
    limb: StringProperty(default="Arm L")
    # Sens du snap : "fk2ik" (FK suit l'IK) ou "ik2fk" (IK suit le FK)
    direction: StringProperty(default="fk2ik")

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE' and context.mode == 'POSE'

    def execute(self, context):
        armature = context.active_object.data
        active_skel = armature.get("active_skeleton", "Adult")

        data = IKFK_DATA.get(active_skel, {}).get(self.limb)
        if data is None:
            self.report({'ERROR'}, f"Membre '{self.limb}' introuvable pour '{active_skel}'.")
            return {'CANCELLED'}

        is_leg = data.get("is_leg", False)

        try:
            if self.direction == "ik2fk":
                self._snap_ik_to_fk(data, is_leg)
            else:
                self._snap_fk_to_ik(data)
        except Exception as e:
            self.report({'ERROR'}, f"Échec du snap {self.direction} sur {self.limb} : {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

    # --- IK -> FK : les contrôleurs IK se calent sur la pose FK actuelle ---
    def _snap_ik_to_fk(self, data, is_leg):
        kwargs = {
            "prop_bone": data["prop"],
            "fk_bones": data["fk"],
            "ik_bones": data["ik"],
            "ctrl_bones": data["ctrl"],
            "tail_bones": data.get("tail", "[]"),
            "extra_ctrls": data.get("extra", "[]"),
        }
        if is_leg:
            # Variante jambe : gère le foot-roll via l'os "heel"
            kwargs["heel_control"] = data.get("heel", "")
            bpy.ops.pose.raccoon_leg_roll_ik2fk(**kwargs)
        else:
            bpy.ops.pose.raccoon_limb_ik2fk(**kwargs)

    # --- FK -> IK : les contrôleurs FK se calent sur la pose IK actuelle ---
    def _snap_fk_to_ik(self, data):
        # output = chaîne FK (déplacée) ; input = chaîne résultat IK + tail (source)
        ik_list = json.loads(data["ik"])
        tail_list = json.loads(data.get("tail", "[]"))
        input_bones = json.dumps(ik_list + tail_list)

        bpy.ops.pose.raccoon_generic_snap(
            output_bones=data["fk"],
            input_bones=input_bones,
            ctrl_bones=input_bones,
            tooltip="FK to IK",
        )
