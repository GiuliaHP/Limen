import bpy
import os

import blender_unity_anim as bua

from .. import config, character, exporter


class ANIM_OT_raccoon_update_model(bpy.types.Operator):
    bl_idname  = "anim.raccoon_update_model"
    bl_label   = "Update Model"
    bl_description = (
        "Exporte mesh + squelette + meshes rigides (yeux/nez) + blendshapes en "
        ".racmodel souverain (CHAR_<Char>, espace Unity, sans FBX) pour le ScriptedImporter"
    )

    def execute(self, context):
        defr, ctrl, char = character.resolve(context)
        if defr is None:
            self.report({'ERROR'}, "Sélectionne un objet du perso (DEF-<Char>)")
            return {'CANCELLED'}

        # pose de REPOS (bind) : reset le ctrl + frame 0 + morph 0 (yeux/nez rigides
        # placés au repos, comme le bind du mesh skinné)
        if ctrl:
            exporter._reset_to_default(ctrl)
            if ctrl.animation_data:
                ctrl.animation_data.action = None
            mb = character.morph_bone(ctrl)
            if mb:
                mb[character.MORPH_PROP] = 0.0
            ctrl.update_tag()
        context.scene.frame_set(0)
        context.view_layer.update()

        out_dir  = os.path.normpath(bpy.path.abspath(config.MODEL_EXPORT_DIR))
        out_path = os.path.join(out_dir, character.model_filename(char))

        try:
            _, nb, nv = bua.export_model(out_path, defr, context,
                                         name=character.model_name(char))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"Export modèle échoué : {e}")
            return {'CANCELLED'}

        size_kb = os.path.getsize(out_path) // 1024
        self.report({'INFO'},
                    f"Modèle exporté ({nb} os, {nv} verts, {size_kb} Ko)  →  {out_path}")
        return {'FINISHED'}
