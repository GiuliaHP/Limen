import bpy
from .. import exporter
from ..clips import get_anim_source


class ANIM_UL_raccoon_clips(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        action = item
        src = get_anim_source()
        is_loaded = bool(src and src.animation_data and src.animation_data.action == action)

        row = layout.row(align=True)
        row.label(text="", icon='PLAY' if is_loaded else 'BLANK1')
        row.prop(action, "name", text="", emboss=False, icon='ACTION')

        rng = exporter._action_frame_range(action)
        # Plage de frames si présente, sinon rien (pas de label)
        if rng:
            sub = row.row()
            sub.alignment = 'RIGHT'
            sub.label(text=f"{rng[0]}-{rng[1]}")

        # Case d'export toujours cochable (un clip vide = anim statique valide)
        row.prop(action, "raccoon_export", text="",
                 icon='CHECKBOX_HLT' if action.raccoon_export else 'CHECKBOX_DEHLT',
                 emboss=False)

    def filter_items(self, context, data, propname):
        """Trie l'affichage par raccoon_order (sans filtrer)."""
        actions = getattr(data, propname)
        flt_flags = [self.bitflag_filter_item] * len(actions)
        ranked = sorted(range(len(actions)),
                        key=lambda i: (actions[i].raccoon_order, actions[i].name))
        flt_neworder = [0] * len(actions)
        for new_pos, orig_i in enumerate(ranked):
            flt_neworder[orig_i] = new_pos
        return flt_flags, flt_neworder
