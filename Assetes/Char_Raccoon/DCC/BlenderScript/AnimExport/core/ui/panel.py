import bpy
from .. import config
from .. import character
from .. import exporter
from .. import clips


class VIEW3D_PT_raccoon_anim_export(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_label = "Raccoon Anim Export"

    @staticmethod
    def _section_header(layout, scene, prop, label, icon):
        """En-tête repliable (triangle cliquable, sans boîte) — style CustomRig."""
        is_open = getattr(scene, prop, True)
        header = layout.row(align=True)
        header.prop(scene, prop, text="",
                    icon='TRIA_DOWN' if is_open else 'TRIA_RIGHT', emboss=False)
        header.label(text=label, icon=icon)
        return is_open

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Perso résolu par pattern depuis l'objet actif (DEF-<Char> / RIG-<Char>)
        deform_obj, anim_obj, char = character.resolve(context)
        has_rig = deform_obj is not None
        has_ctrl = anim_obj is not None
        morph = has_ctrl and character.has_morph(anim_obj)

        if not has_rig:
            layout.label(text="Sélectionne un objet (DEF-<Char>)", icon='ERROR')
        else:
            layout.label(text=f"Perso : {char}" + ("" if has_ctrl else "  (pas de RIG-)"),
                         icon='OUTLINER_OB_ARMATURE')

        # --- Setup rig + morph (section repliable, style CustomRig) ---
        # boutons morph seulement si le perso a un morph (prop morph_blend détectée)
        if morph and self._section_header(layout, scene, "raccoon_show_rigmorph",
                                          "Rig & Morph", 'CONSTRAINT_BONE'):
            col = layout.column(align=True)
            col.enabled = has_rig and has_ctrl
            col.operator("anim.raccoon_setup_rig", text="Setup Rig", icon='MODIFIER')
            col.operator("anim.raccoon_update_adult_shape",
                         text="Update Adult Shape", icon='SHAPEKEY_DATA')
        if morph:
            layout.separator()

        # --- Clip Manager : UIList + colonne de boutons ---
        layout.label(text="Clips", icon='ACTION')
        row = layout.row()
        row.template_list(
            "ANIM_UL_raccoon_clips", "",
            bpy.data, "actions",
            scene, clips.INDEX_PROP,
            rows=6,
        )
        col = row.column(align=True)
        col.operator("anim.raccoon_clip_new",    icon='ADD',        text="")
        col.operator("anim.raccoon_clip_delete", icon='REMOVE',     text="")
        col.separator()
        col.operator("anim.raccoon_clip_move", icon='TRIA_UP',   text="").direction = 'UP'
        col.operator("anim.raccoon_clip_move", icon='TRIA_DOWN', text="").direction = 'DOWN'
        col.separator()
        col.menu("ANIM_MT_raccoon_clip_specials", icon='DOWNARROW_HLT', text="")

        # --- Export animations ---
        layout.separator()
        exportable = exporter.list_exportable_actions()
        can_export = bool(exportable) and anim_obj is not None and deform_obj is not None

        row = layout.row()
        row.scale_y = 1.5
        row.enabled = can_export
        row.operator("anim.raccoon_export_unity_anim",
                     text=f"Export {len(exportable)} Clips → .anim",
                     icon='EXPORT')

        # --- Update Model ---
        layout.separator()
        row = layout.row()
        row.scale_y = 1.3
        row.enabled = deform_obj is not None
        row.operator("anim.raccoon_update_model",
                     text="Update Model",
                     icon='ARMATURE_DATA')
