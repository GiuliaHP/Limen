import bpy
from . import exporter

# Nom de la propriété d'index de NOTRE liste (sert à reconnaître notre UIList
# dans le menu clic-droit partagé UI_MT_list_item_context_menu).
INDEX_PROP = "raccoon_clip_index"


# ===========================================================================
#  Helpers
# ===========================================================================

def get_anim_source(context=None):
    """Rig de contrôle (RIG-<Char>) résolu par pattern depuis l'objet actif."""
    from . import character
    ctx = context or bpy.context
    _, ctrl, _ = character.resolve(ctx)
    return ctrl


def active_clip_action(context):
    """Clip sélectionné dans la liste (par index)."""
    idx = getattr(context.scene, INDEX_PROP, 0)
    acts = bpy.data.actions
    return acts[idx] if 0 <= idx < len(acts) else None


def _resolve_target(op, context):
    name = getattr(op, "action_name", "")
    if name:
        return bpy.data.actions.get(name)
    return active_clip_action(context)


def iter_fcurves(action):
    layers = getattr(action, "layers", None)
    if layers:
        for layer in layers:
            for strip in layer.strips:
                if getattr(strip, "type", None) != 'KEYFRAME':
                    continue
                for slot in action.slots:
                    cb = strip.channelbag(slot)
                    if cb:
                        for fc in cb.fcurves:
                            yield fc
    elif hasattr(action, "fcurves"):
        for fc in action.fcurves:
            yield fc


def set_active_clip(context, action):
    src = get_anim_source()
    if not src or action is None:
        return
    exporter._reset_to_default(src)       # non-keyé -> défaut (source unique : exporter)
    exporter._assign_action(src, action)  # keyé -> courbe (écrase le reset)
    rng = exporter._action_frame_range(action)
    if rng:
        context.scene.frame_start, context.scene.frame_end = rng
        context.scene.frame_set(rng[0])
    context.view_layer.update()


def _select(context, action):
    """Sélectionne un clip (met l'index) → déclenche le chargement."""
    if action is None:
        return
    setattr(context.scene, INDEX_PROP, bpy.data.actions.find(action.name))


# ===========================================================================
#  Propriétés
# ===========================================================================

def _on_index_update(self, context):
    set_active_clip(context, active_clip_action(context))


def register_props():
    if not hasattr(bpy.types.Action, "raccoon_export"):
        bpy.types.Action.raccoon_export = bpy.props.BoolProperty(
            name="Exporter",
            description="Inclure ce clip dans l'export FBX",
            default=True,
        )
    # Ordre d'affichage dans la liste (bpy.data.actions n'est pas réordonnable)
    if not hasattr(bpy.types.Action, "raccoon_order"):
        bpy.types.Action.raccoon_order = bpy.props.IntProperty(
            name="Ordre", default=0)
    if not hasattr(bpy.types.Scene, INDEX_PROP):
        setattr(bpy.types.Scene, INDEX_PROP, bpy.props.IntProperty(
            name="Clip", default=0, min=0, update=_on_index_update))
    # État déplié/replié de la section "Rig & Morph" (style CustomRig) — replié par défaut
    if not hasattr(bpy.types.Scene, "raccoon_show_rigmorph"):
        bpy.types.Scene.raccoon_show_rigmorph = bpy.props.BoolProperty(default=False)


def unregister_props():
    if hasattr(bpy.types.Action, "raccoon_export"):
        del bpy.types.Action.raccoon_export
    if hasattr(bpy.types.Action, "raccoon_order"):
        del bpy.types.Action.raccoon_order
    if hasattr(bpy.types.Scene, INDEX_PROP):
        delattr(bpy.types.Scene, INDEX_PROP)
    if hasattr(bpy.types.Scene, "raccoon_show_rigmorph"):
        del bpy.types.Scene.raccoon_show_rigmorph


def _normalize_orders():
    """Réassigne des ordres séquentiels distincts (0,1,2,…) selon l'ordre courant."""
    ordered = sorted(bpy.data.actions, key=lambda a: (a.raccoon_order, a.name))
    for k, a in enumerate(ordered):
        if a.raccoon_order != k:
            a.raccoon_order = k


def _next_order():
    return max((a.raccoon_order for a in bpy.data.actions), default=-1) + 1


# ===========================================================================
#  Menus clic-droit : nettoyage des anciens hooks
# ---------------------------------------------------------------------------
#  Note : on n'override PAS le clic droit (Blender réinjecte ses entrées
#  natives côté C, non retirables). Le menu d'actions est le ▾ (cf. ui.py).
#  Cette fonction démantèle juste les greffes laissées par d'anciennes versions.
# ===========================================================================

def cleanup_button_menu():
    for menu_name in ("UI_MT_button_context_menu", "UI_MT_list_item_context_menu"):
        menu = getattr(bpy.types, menu_name, None)
        funcs = getattr(getattr(menu, "draw", None), "_draw_funcs", None)
        if funcs:
            for f in list(funcs):
                if getattr(f, "__name__", "") in (
                    "_draw_clip_context_menu", "_draw_our_clip_menu", "_wrapped",
                    "_native_button_menu_draw", "_native_draw", "_draw_list_item_menu",
                ):
                    funcs.remove(f)


def register_context_menu():
    cleanup_button_menu()


def unregister_context_menu():
    cleanup_button_menu()


# ===========================================================================
#  Raccourci clavier : Suppr supprime le clip actif (dans le N-panel)
# ===========================================================================

_addon_keymaps = []


def _purge_our_keymap_items():
    """Retire nos items (par nom d'opérateur) — attrape aussi les orphelins
    laissés par les relances/reloads du bootstrap."""
    kc = bpy.context.window_manager.keyconfigs.addon
    if not kc:
        return
    km = kc.keymaps.get('User Interface')
    if km:
        for kmi in list(km.keymap_items):
            if kmi.idname == "anim.raccoon_clip_delete_key":
                km.keymap_items.remove(kmi)
    _addon_keymaps.clear()


def register_keymaps():
    _purge_our_keymap_items()  # anti-accumulation au re-lancement
    kc = bpy.context.window_manager.keyconfigs.addon
    if not kc:
        return
    km = kc.keymaps.new(name='User Interface', space_type='EMPTY')
    kmi = km.keymap_items.new("anim.raccoon_clip_delete_key", 'DEL', 'PRESS')
    _addon_keymaps.append((km, kmi))


def unregister_keymaps():
    _purge_our_keymap_items()
