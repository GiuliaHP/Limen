import bpy
import os
from .. import config
from ..exporter import list_exportable_actions, _resolve_export_dir, _export_one


class ANIM_OT_raccoon_export_all(bpy.types.Operator):
    """Exporte chaque Action en FBX anim-only (squelette Def baked) dans le dossier de sortie"""
    bl_idname = "anim.raccoon_export_all"
    bl_label = "Export All Clips → FBX"
    bl_options = {'REGISTER'}

    def execute(self, context):
        anim_obj = bpy.data.objects.get(config.ANIM_SOURCE)
        deform_obj = bpy.data.objects.get(config.DEF_ARMATURE)

        if anim_obj is None:
            self.report({'ERROR'}, f"Objet animé '{config.ANIM_SOURCE}' introuvable.")
            return {'CANCELLED'}
        if deform_obj is None:
            self.report({'ERROR'}, f"Armature '{config.DEF_ARMATURE}' introuvable.")
            return {'CANCELLED'}

        actions = list_exportable_actions()

        if not actions:
            self.report({'WARNING'}, "Aucun clip coché pour l'export.")
            return {'CANCELLED'}

        out_dir = _resolve_export_dir(context)
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception as e:
            self.report({'ERROR'}, f"Dossier de sortie invalide : {e}")
            return {'CANCELLED'}

        # --- Sauvegarde de l'état ---
        saved = self._save_state(context, anim_obj)

        ok_count = 0
        try:
            self._ensure_object_mode(context)
            for action, rng in actions:
                ok, msg = _export_one(context, action, rng, anim_obj, deform_obj, out_dir)
                print(("  [OK] " if ok else "  [ERR] ") + msg)
                if ok:
                    ok_count += 1
                else:
                    self.report({'WARNING'}, msg)
        finally:
            self._restore_state(context, anim_obj, saved)

        summary = f"{ok_count}/{len(actions)} clips exportés → {out_dir}"
        self.report({'INFO'}, summary)
        return {'FINISHED'}

    # --- gestion d'état ---
    @staticmethod
    def _ensure_object_mode(context):
        obj = context.view_layer.objects.active
        if obj and obj.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass

    @staticmethod
    def _save_state(context, anim_obj):
        scene = context.scene
        ad = anim_obj.animation_data
        return {
            "action": ad.action if ad else None,
            "slot": getattr(ad, "action_slot", None) if ad else None,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "frame_current": scene.frame_current,
            "active": context.view_layer.objects.active,
            "selected": [o for o in context.view_layer.objects if o.select_get()],
        }

    @staticmethod
    def _restore_state(context, anim_obj, saved):
        scene = context.scene
        if anim_obj.animation_data is not None:
            try:
                anim_obj.animation_data.action = saved["action"]
                if saved["slot"] is not None and hasattr(anim_obj.animation_data, "action_slot"):
                    anim_obj.animation_data.action_slot = saved["slot"]
            except Exception:
                pass
        scene.frame_start = saved["frame_start"]
        scene.frame_end = saved["frame_end"]
        scene.frame_set(saved["frame_current"])
        for o in context.view_layer.objects:
            o.select_set(o in saved["selected"])
        if saved["active"]:
            context.view_layer.objects.active = saved["active"]
