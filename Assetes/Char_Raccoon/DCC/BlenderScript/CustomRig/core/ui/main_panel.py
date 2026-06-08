import bpy
import collections
from ..constants import RIG_ID, IKFK_DATA


def flatten_children(iterable):
    for item in iterable:
        yield item
        yield from flatten_children(item.children)


# Sections repliables du panneau : (nom_prop_scene, valeur_par_defaut)
SECTION_PROPS = [
    ("raccoon_show_skeleton", True),
    ("raccoon_show_layers", True),
    ("raccoon_show_ikfk", False),
]


def register_props():
    """Enregistre les BoolProperty d'état (déplié/replié) sur la Scene."""
    for name, default in SECTION_PROPS:
        if not hasattr(bpy.types.Scene, name):
            setattr(bpy.types.Scene, name,
                    bpy.props.BoolProperty(default=default))


def unregister_props():
    for name, _default in SECTION_PROPS:
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)


class VIEW3D_PT_raccoon_main_ui(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_label = "Raccoon Rig UI"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE' and context.mode in {'POSE', 'OBJECT'}

    @staticmethod
    def _section_header(layout, scene, prop, label, icon):
        """Dessine un en-tête repliable (triangle cliquable, sans boîte).
        Renvoie est_ouvert : le contenu n'est dessiné que si vrai."""
        is_open = getattr(scene, prop, True)
        header = layout.row(align=True)
        header.prop(scene, prop, text="",
                    icon='TRIA_DOWN' if is_open else 'TRIA_RIGHT', emboss=False)
        header.label(text=label, icon=icon)
        return is_open

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object
        pose_bones = obj.pose.bones
        armature = obj.data
        is_pose_mode = context.mode == 'POSE'
        active_skel = armature.get("active_skeleton", "Adult")

        # ===== 1. SKELETON (Adult / Child) =====
        if self._section_header(layout, scene, "raccoon_show_skeleton",
                                "Morphe", 'ARMATURE_DATA'):
            row = layout.row(align=True)
            op_child = row.operator("armature.toggle_skeleton_raccoon", text="Child",
                                    depress=(active_skel == "Child"))
            op_child.skeleton_type = "Child"

            op_adult = row.operator("armature.toggle_skeleton_raccoon", text="Adult",
                                    depress=(active_skel == "Adult"))
            op_adult.skeleton_type = "Adult"

            # Morphology Blend Slider (Pose mode uniquement)
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

        # ===== 2. RIG LAYERS =====
        if self._section_header(layout, scene, "raccoon_show_layers",
                                "Rig Layers", 'HIDE_OFF'):
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

        # ===== 3. IK/FK SLIDERS + SNAP (Pose mode uniquement) =====
        if is_pose_mode:
            if self._section_header(layout, scene, "raccoon_show_ikfk",
                                    f"IK / FK ({active_skel})", 'CON_KINEMATIC'):
                # On s'appuie directement sur IKFK_DATA (la source de vérité)
                limb_data = IKFK_DATA.get(active_skel, {})

                col = layout.column(align=True)
                for limb_name, data in limb_data.items():
                    bone_name = data["prop"]
                    if bone_name not in pose_bones:
                        continue

                    pb = pose_bones[bone_name]
                    sub = col.column(align=True)

                    # Slider de blend IK <-> FK
                    if "IK_FK" in pb:
                        sub.prop(pb, '["IK_FK"]', text=limb_name, slider=True)
                    else:
                        sub.label(text=f"{limb_name} : Prop 'IK_FK' manquante", icon='ERROR')

                    # Boutons de snap
                    row_snap = sub.row(align=True)
                    op = row_snap.operator("pose.raccoon_ikfk_snap", text="IK → FK")
                    op.limb = limb_name
                    op.direction = "ik2fk"

                    op = row_snap.operator("pose.raccoon_ikfk_snap", text="FK → IK")
                    op.limb = limb_name
                    op.direction = "fk2ik"

                    col.separator()


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
