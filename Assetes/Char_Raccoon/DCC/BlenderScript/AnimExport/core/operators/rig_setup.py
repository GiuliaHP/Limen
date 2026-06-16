import bpy

from .. import character


class ANIM_OT_raccoon_setup_rig(bpy.types.Operator):
    bl_idname = "anim.raccoon_setup_rig"
    bl_label = "Setup Rig"
    bl_description = ("Monte les contraintes du Def (production, sans scale d'os) : "
                      "os déconnectés, COPY_TRANSFORMS Child↔Adult blendés par morph_blend")

    def execute(self, context):
        defr, ctrl, char = character.resolve(context)
        if ctrl is None or defr is None:
            self.report({'ERROR'}, "Sélectionne un objet du perso (DEF-<Char> / RIG-<Char>)")
            return {'CANCELLED'}
        try:
            import importlib
            from SetupDefContrites import Contrites_core as sdc
            importlib.reload(sdc)   # recharge le __init__ + sous-modules (cache RAM Blender)
            sdc.reload_core()
            sdc.clear_rig_data(defr.name)
            sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT, use_stretch=False)
        except Exception as e:
            self.report({'ERROR'}, f"Setup rig échoué : {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, "Rig monté (production, sans scale d'os)")
        return {'FINISHED'}
