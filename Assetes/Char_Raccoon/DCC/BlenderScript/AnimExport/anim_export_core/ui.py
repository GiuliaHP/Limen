import bpy
from . import config
from . import exporter
from . import clips


class VIEW3D_PT_raccoon_anim_export(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_label = "Raccoon Anim Export"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        anim_obj = bpy.data.objects.get(config.ANIM_SOURCE)
        deform_obj = bpy.data.objects.get(config.DEF_ARMATURE)

        if anim_obj is None:
            layout.label(text=f"'{config.ANIM_SOURCE}' introuvable", icon='ERROR')
        if deform_obj is None:
            layout.label(text=f"'{config.DEF_ARMATURE}' introuvable", icon='ERROR')

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
        col.operator("anim.raccoon_clip_new", icon='ADD', text="")
        col.operator("anim.raccoon_clip_delete", icon='REMOVE', text="")
        col.separator()
        col.operator("anim.raccoon_clip_move", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("anim.raccoon_clip_move", icon='TRIA_DOWN', text="").direction = 'DOWN'
        col.separator()
        col.menu("ANIM_MT_raccoon_clip_specials", icon='DOWNARROW_HLT', text="")

        # --- Export ---
        exportable = exporter.list_exportable_actions()
        row = layout.row()
        row.scale_y = 1.4
        row.enabled = bool(exportable) and anim_obj is not None and deform_obj is not None
        row.operator("anim.raccoon_export_all",
                     text=f"Export {len(exportable)} Clips → FBX", icon='EXPORT')


classes = (
    VIEW3D_PT_raccoon_anim_export,
)
