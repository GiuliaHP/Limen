import bpy
from ..clips import _normalize_orders, active_clip_action, INDEX_PROP


class ANIM_OT_raccoon_clip_move(bpy.types.Operator):
    """Déplace le clip dans la liste (vers le haut / le bas)"""
    bl_idname = "anim.raccoon_clip_move"
    bl_label = "Déplacer le clip"
    # Pas de 'REGISTER' → pas de panneau "Ajuster la dernière opération"
    bl_options = {'UNDO', 'INTERNAL'}

    direction: bpy.props.EnumProperty(
        items=[('UP', "Haut", ""), ('DOWN', "Bas", "")], default='UP',
        options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return active_clip_action(context) is not None

    def execute(self, context):
        _normalize_orders()
        active = active_clip_action(context)
        ordered = sorted(bpy.data.actions, key=lambda a: a.raccoon_order)
        i = ordered.index(active)
        j = i - 1 if self.direction == 'UP' else i + 1
        if not (0 <= j < len(ordered)):
            return {'CANCELLED'}
        a, b = ordered[i], ordered[j]
        a.raccoon_order, b.raccoon_order = b.raccoon_order, a.raccoon_order
        # garder le clip actif sélectionné (l'index pointe sur bpy.data.actions)
        setattr(context.scene, INDEX_PROP, bpy.data.actions.find(active.name))
        return {'FINISHED'}
