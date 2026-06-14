import bpy
import os

from .. import config, exporter


class ANIM_OT_raccoon_update_model(bpy.types.Operator):
    bl_idname  = "anim.raccoon_update_model"
    bl_label   = "Update Model"
    bl_description = (
        "Exporte le mesh + squelette Def en rest pose (sans animation) "
        "vers Output/Model/Raccoon.fbx"
    )

    def execute(self, context):
        defr = bpy.data.objects.get(config.DEF_ARMATURE)
        if defr is None:
            self.report({'ERROR'}, f"Armature '{config.DEF_ARMATURE}' introuvable")
            return {'CANCELLED'}

        # Meshes skinnés au Def
        skinned = [o for o in bpy.data.objects
                   if o.type == 'MESH'
                   and any(m.type == 'ARMATURE' and m.object is defr
                           for m in o.modifiers)]
        if not skinned:
            self.report({'WARNING'}, "Aucun mesh skinné au Def trouvé")
            return {'CANCELLED'}

        out_dir  = os.path.normpath(bpy.path.abspath(config.MODEL_EXPORT_DIR))
        out_path = os.path.join(out_dir, config.MODEL_EXPORT_FILENAME)
        os.makedirs(out_dir, exist_ok=True)

        # Sélection : Def + tous les meshes skinnés
        for o in context.view_layer.objects:
            o.select_set(False)
        defr.select_set(True)
        for o in skinned:
            o.select_set(True)
        context.view_layer.objects.active = defr

        # Rest pose : reset le Ctrl (qui pilote le Def via contraintes) + vide son action
        ctrl = bpy.data.objects.get(config.ANIM_SOURCE)
        if ctrl:
            exporter._reset_to_default(ctrl)
            if ctrl.animation_data:
                ctrl.animation_data.action = None
        if defr.animation_data:
            defr.animation_data.action = None
        context.scene.frame_set(0)
        context.view_layer.update()

        try:
            bpy.ops.export_scene.fbx(
                filepath=out_path,
                use_selection=True,
                object_types={'ARMATURE', 'MESH'},
                use_mesh_modifiers=True,
                use_armature_deform_only=False,
                add_leaf_bones=False,
                bake_anim=False,
                axis_forward='-Z',
                axis_up='Y',
                apply_scale_options='FBX_SCALE_NONE',
                global_scale=1.0,
                apply_unit_scale=True,
                path_mode='AUTO',
                mesh_smooth_type='FACE',
            )
        except Exception as e:
            self.report({'ERROR'}, f"Export FBX échoué : {e}")
            return {'CANCELLED'}

        size_kb = os.path.getsize(out_path) // 1024
        self.report({'INFO'}, f"Model exporté ({size_kb} Ko)  →  {out_path}")
        return {'FINISHED'}
