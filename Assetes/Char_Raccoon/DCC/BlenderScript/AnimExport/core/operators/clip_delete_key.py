import bpy
from ..clips import active_clip_action


class ANIM_OT_raccoon_clip_delete_key(bpy.types.Operator):
    """Relais touche Suppr : supprime le clip actif quand on est dans le N-panel.
    (Le contexte du bouton survolé n'existe pas dans un opérateur de keymap ;
    on se base donc sur la région N-panel + le clip sélectionné.)"""
    bl_idname = "anim.raccoon_clip_delete_key"
    bl_label = "Supprimer le clip (Suppr)"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        area = context.area
        region = context.region
        # On n'agit que dans le N-panel (région UI) d'une vue 3D
        if not (area and area.type == 'VIEW_3D' and region and region.type == 'UI'):
            return {'PASS_THROUGH'}
        action = active_clip_action(context)
        if action is None:
            return {'PASS_THROUGH'}
        # EXEC_DEFAULT → suppression directe, sans la confirmation
        bpy.ops.anim.raccoon_clip_delete('EXEC_DEFAULT', action_name=action.name)
        return {'FINISHED'}
