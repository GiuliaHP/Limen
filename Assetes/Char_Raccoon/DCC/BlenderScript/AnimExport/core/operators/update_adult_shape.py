import bpy

from .. import character


class ANIM_OT_raccoon_update_adult_shape(bpy.types.Operator):
    bl_idname = "anim.raccoon_update_adult_shape"
    bl_label = "Update Adult Shape"
    bl_description = ("Re-bake le blendshape Adult_shape par dé-skinning : crée/met à jour "
                      "le shape (galbe adulte) et assigne le driver morph_blend. "
                      "Laisse le rig en mode production (sans scale d'os)")

    def execute(self, context):
        defr, ctrl, char = character.resolve(context)
        if ctrl is None or defr is None:
            self.report({'ERROR'}, "Sélectionne un objet du perso (DEF-<Char> / RIG-<Char>)")
            return {'CANCELLED'}
        try:
            import importlib
            from SetupDefContrites import Contrites_core as sdc
            importlib.reload(sdc)   # recharge le __init__ (importe morph_bake, binde update_adult_shape)
            sdc.reload_core()       # recharge les sous-modules (applier use_stretch, etc.)
            n, msg = sdc.update_adult_shape(defr, ctrl, sdc.MAPPING_DICT)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"Update Adult Shape échoué : {e}")
            return {'CANCELLED'}
        self.report({'INFO'} if n else {'WARNING'}, f"Adult Shape : {msg}")
        return {'FINISHED'}
