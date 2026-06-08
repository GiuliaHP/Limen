from multiprocessing import context

import bpy
import collections
from ..constants import RIG_ID, IKFK_DATA

def flatten_children(iterable):
    for item in iterable:
        yield item
        yield from flatten_children(item.children)

class VIEW3D_PT_raccoon_main_ui(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_label = "Raccoon Rig UI"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE' and context.mode in {'POSE', 'OBJECT'}

    def draw(self, context):
        layout = self.layout
        pose_bones = context.active_object.pose.bones
        armature = context.active_object.data
        is_pose_mode = context.mode == 'POSE'

        # --- 1. SKELETON VISIBILITY (Adult / Child) ---
        layout.label(text="Skeleton Mode:", icon='ARMATURE_DATA')
        row = layout.row(align=True)
        active_skel = armature.get("active_skeleton", "Adult")

        op_child = row.operator("armature.toggle_skeleton_raccoon", text="Child", depress=(active_skel == "Child"))
        op_child.skeleton_type = "Child"

        op_adult = row.operator("armature.toggle_skeleton_raccoon", text="Adult", depress=(active_skel == "Adult"))
        op_adult.skeleton_type = "Adult"

        # --- Morphology Blend Slider (Pose mode uniquement) ---
        if is_pose_mode:
            master_bone_name = "root"
            if master_bone_name in pose_bones:
                pb = pose_bones[master_bone_name]
                if "morph_blend" in pb:
                    layout.prop(pb, '["morph_blend"]', text="Child  ←→  Adult", slider=True)
                else:
                    layout.label(text=f"Prop 'morph_blend' manquante sur {master_bone_name}", icon='ERROR')
            else:
                layout.label(text=f"Os maître '{master_bone_name}' introuvable", icon='ERROR')

        layout.separator()

        # --- 2. RIG LAYERS ---
        layout.label(text="Rig Layers:", icon='GROUP_BONE')
        
        row_table = collections.defaultdict(list)
        for coll in flatten_children(armature.collections):
            if coll.name in ["Adult", "Child"]:
                continue
            row_id = getattr(coll, "rigify_ui_row", 0)
            if row_id > 0:
                row_table[row_id].append(coll)
        
        col = layout.column()
        if row_table:
            for row_id in range(min(row_table.keys()), 1 + max(row_table.keys())):
                row = col.row()
                row_buttons = row_table.get(row_id, [])
                if row_buttons:
                    for coll in row_buttons:
                        title = getattr(coll, "rigify_ui_title", "") or coll.name
                        row.prop(coll, 'is_visible', toggle=True, text=title)
                else:
                    row.separator()

        layout.separator()

        # --- 3. IK/FK SLIDERS (Pose mode uniquement) ---
        if is_pose_mode:
            layout.label(text=f"IK / FK Blend ({active_skel}):", icon='CON_KINEMATIC')

            ikfk_bones_adult = {
                "Arm L": "Adult_upper_arm_parent.L",
                "Arm R": "Adult_upper_arm_parent.R",
                "Leg L": "Adult_thigh_parent.L",
                "Leg R": "Adult_thigh_parent.R"
            }
            
            ikfk_bones_child = {
                "Arm L": "Child_upper_arm_parent.L",
                "Arm R": "Child_upper_arm_parent.R",
                "Leg L": "Child_thigh_parent.L",
                "Leg R": "Child_thigh_parent.R"
            }

            active_ikfk_list = ikfk_bones_adult if active_skel == "Adult" else ikfk_bones_child

            col = layout.column(align=True)
            for label, bone_name in active_ikfk_list.items():
                if bone_name in pose_bones:
                    if "IK_FK" in pose_bones[bone_name]:
                        col.prop(pose_bones[bone_name], '["IK_FK"]', text=label, slider=True)
                    else:
                        col.label(text=f"{label} : Prop 'IK_FK' manquante", icon='ERROR')

classes = (VIEW3D_PT_raccoon_main_ui,)

def register():
    for cls in classes:
        if hasattr(bpy.types, cls.__name__):
            try: bpy.utils.unregister_class(getattr(bpy.types, cls.__name__))
            except Exception: pass
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        try: bpy.utils.unregister_class(cls)
        except Exception: pass