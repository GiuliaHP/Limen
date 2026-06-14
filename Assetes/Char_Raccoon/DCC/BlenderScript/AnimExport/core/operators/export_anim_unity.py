import bpy
import os

from .. import config, exporter, unity_anim


class ANIM_OT_raccoon_export_unity_anim(bpy.types.Operator):
    bl_idname  = "anim.raccoon_export_unity_anim"
    bl_label   = "Export .anim (Unity)"
    bl_description = "Exporte tous les clips cochés en fichiers .anim natifs Unity"

    def execute(self, context):
        ctrl = bpy.data.objects.get(config.ANIM_SOURCE)
        defr = bpy.data.objects.get(config.DEF_ARMATURE)
        if ctrl is None or defr is None:
            self.report({'ERROR'}, "Objets source/déform introuvables")
            return {'CANCELLED'}

        exportable = exporter.list_exportable_actions()
        if not exportable:
            self.report({'WARNING'}, "Aucun clip à exporter")
            return {'CANCELLED'}

        out_dir = os.path.normpath(bpy.path.abspath(config.EXPORT_DIR))
        os.makedirs(out_dir, exist_ok=True)

        ok_count, err_count = 0, 0
        for action, rng in exportable:
            name = exporter._sanitize(action.name)
            filepath = os.path.join(out_dir, name + ".anim")
            try:
                unity_anim.write_anim(filepath, action.name, context,
                                      ctrl, defr, action, rng)
                print(f"  OK  {action.name}  →  {name}.anim  [{rng[0]}-{rng[1]}]")
                ok_count += 1
            except Exception as e:
                print(f"  ERR {action.name} : {e}")
                err_count += 1

        summary = f"Export .anim : {ok_count} OK"
        if err_count:
            summary += f", {err_count} erreur(s)"
        self.report({'INFO'} if not err_count else {'WARNING'}, summary)
        return {'FINISHED'}
