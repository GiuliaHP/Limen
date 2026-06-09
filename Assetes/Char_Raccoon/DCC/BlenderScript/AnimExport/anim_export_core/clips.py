import bpy
from bpy.props import StringProperty
from . import config
from . import exporter

# Nom de la propriété d'index de NOTRE liste (sert à reconnaître notre UIList
# dans le menu clic-droit partagé UI_MT_list_item_context_menu).
INDEX_PROP = "raccoon_clip_index"


# ===========================================================================
#  Helpers
# ===========================================================================

def get_anim_source():
    return bpy.data.objects.get(config.ANIM_SOURCE)


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
    exporter._assign_action(src, action)
    rng = exporter._action_frame_range(action)
    if rng:
        context.scene.frame_start, context.scene.frame_end = rng


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


def unregister_props():
    if hasattr(bpy.types.Action, "raccoon_export"):
        del bpy.types.Action.raccoon_export
    if hasattr(bpy.types.Action, "raccoon_order"):
        del bpy.types.Action.raccoon_order
    if hasattr(bpy.types.Scene, INDEX_PROP):
        delattr(bpy.types.Scene, INDEX_PROP)


def _normalize_orders():
    """Réassigne des ordres séquentiels distincts (0,1,2,…) selon l'ordre courant."""
    ordered = sorted(bpy.data.actions, key=lambda a: (a.raccoon_order, a.name))
    for k, a in enumerate(ordered):
        if a.raccoon_order != k:
            a.raccoon_order = k


def _next_order():
    return max((a.raccoon_order for a in bpy.data.actions), default=-1) + 1


# ===========================================================================
#  Opérateurs
# ===========================================================================

class ANIM_OT_raccoon_clip_new(bpy.types.Operator):
    """Crée un nouveau clip (Action) vide sur le rig de contrôle"""
    bl_idname = "anim.raccoon_clip_new"
    bl_label = "Nouveau clip"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        src = get_anim_source()
        if not src:
            self.report({'ERROR'}, f"'{config.ANIM_SOURCE}' introuvable.")
            return {'CANCELLED'}
        action = bpy.data.actions.new("NewClip")
        action.use_fake_user = True
        action.raccoon_order = _next_order()
        exporter._assign_action(src, action)
        _select(context, action)
        return {'FINISHED'}


class ANIM_OT_raccoon_clip_duplicate(bpy.types.Operator):
    """Duplique le clip"""
    bl_idname = "anim.raccoon_clip_duplicate"
    bl_label = "Dupliquer le clip"
    bl_options = {'REGISTER', 'UNDO'}

    action_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return bool(bpy.data.actions)

    def execute(self, context):
        base = _resolve_target(self, context)
        if not base:
            self.report({'WARNING'}, "Aucun clip ciblé.")
            return {'CANCELLED'}
        new = base.copy()
        new.name = base.name + "_copy"
        new.use_fake_user = True
        new.raccoon_order = _next_order()
        _select(context, new)
        self.report({'INFO'}, f"Dupliqué : {new.name}")
        return {'FINISHED'}


class ANIM_OT_raccoon_clip_delete(bpy.types.Operator):
    """Supprime le clip"""
    bl_idname = "anim.raccoon_clip_delete"
    bl_label = "Supprimer le clip"
    bl_options = {'REGISTER', 'UNDO'}

    action_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return bool(bpy.data.actions)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        action = _resolve_target(self, context)
        if not action:
            self.report({'WARNING'}, "Aucun clip ciblé.")
            return {'CANCELLED'}
        name = action.name
        idx = getattr(context.scene, INDEX_PROP, 0)

        src = get_anim_source()
        if src and src.animation_data and src.animation_data.action == action:
            src.animation_data.action = None

        bpy.data.actions.remove(action)
        setattr(context.scene, INDEX_PROP, max(0, min(idx, len(bpy.data.actions) - 1)))
        self.report({'INFO'}, f"Supprimé : {name}")
        return {'FINISHED'}


class ANIM_OT_raccoon_clip_reverse(bpy.types.Operator):
    """Crée une copie du clip jouée à l'envers"""
    bl_idname = "anim.raccoon_clip_reverse"
    bl_label = "Reverse (à l'envers)"
    bl_options = {'REGISTER', 'UNDO'}

    action_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return bool(bpy.data.actions)

    def execute(self, context):
        base = _resolve_target(self, context)
        if not base:
            self.report({'WARNING'}, "Aucun clip ciblé.")
            return {'CANCELLED'}
        rng = exporter._action_frame_range(base)
        if not rng:
            self.report({'WARNING'}, "Clip vide : rien à inverser.")
            return {'CANCELLED'}
        start, end = rng
        total = start + end

        rev = base.copy()
        rev.name = base.name + "_Reverse"
        rev.use_fake_user = True
        rev.raccoon_order = _next_order()

        for fc in iter_fcurves(rev):
            for kp in fc.keyframe_points:
                hl = kp.handle_left.copy()
                hr = kp.handle_right.copy()
                kp.co.x = total - kp.co.x
                kp.handle_left.x = total - hr.x
                kp.handle_left.y = hr.y
                kp.handle_right.x = total - hl.x
                kp.handle_right.y = hl.y
            fc.update()

        _select(context, rev)
        self.report({'INFO'}, f"Reverse : {rev.name}")
        return {'FINISHED'}


class ANIM_OT_raccoon_clip_mirror(bpy.types.Operator):
    """Crée une copie miroir L<->R du clip (pose-flip natif, baked frame par frame)"""
    bl_idname = "anim.raccoon_clip_mirror"
    bl_label = "Mirror L<->R"
    bl_options = {'REGISTER', 'UNDO'}

    action_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return bool(bpy.data.actions)

    def execute(self, context):
        src = get_anim_source()
        base = _resolve_target(self, context)
        if not src:
            self.report({'ERROR'}, f"'{config.ANIM_SOURCE}' introuvable.")
            return {'CANCELLED'}
        if not base:
            self.report({'WARNING'}, "Aucun clip ciblé.")
            return {'CANCELLED'}
        rng = exporter._action_frame_range(base)
        if not rng:
            self.report({'WARNING'}, "Clip vide : rien à miroiter.")
            return {'CANCELLED'}
        start, end = rng

        scene = context.scene
        saved_frame = scene.frame_current
        saved_active = context.view_layer.objects.active
        saved_sel = [o for o in context.view_layer.objects if o.select_get()]

        mir = base.copy()
        mir.name = base.name + "_Mirror"
        mir.use_fake_user = True
        mir.raccoon_order = _next_order()
        exporter._assign_action(src, mir)

        try:
            for o in context.view_layer.objects:
                o.select_set(False)
            src.select_set(True)
            context.view_layer.objects.active = src
            if src.mode != 'POSE':
                bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='SELECT')

            for f in range(start, end + 1):
                scene.frame_set(f)
                bpy.ops.pose.copy()
                bpy.ops.pose.paste(flipped=True)
                for pb in src.pose.bones:
                    if pb.bone.select:
                        self._key_bone(pb, f)
        except Exception as e:
            self.report({'ERROR'}, f"Mirror échoué : {e}")
        finally:
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass
            scene.frame_set(saved_frame)
            for o in context.view_layer.objects:
                o.select_set(o in saved_sel)
            if saved_active:
                context.view_layer.objects.active = saved_active

        _select(context, mir)
        self.report({'INFO'}, f"Mirror : {mir.name}  (⚠ props custom IK/FK non miroitées)")
        return {'FINISHED'}

    @staticmethod
    def _key_bone(pb, frame):
        pb.keyframe_insert("location", frame=frame)
        if pb.rotation_mode == 'QUATERNION':
            pb.keyframe_insert("rotation_quaternion", frame=frame)
        elif pb.rotation_mode == 'AXIS_ANGLE':
            pb.keyframe_insert("rotation_axis_angle", frame=frame)
        else:
            pb.keyframe_insert("rotation_euler", frame=frame)
        pb.keyframe_insert("scale", frame=frame)


# ===========================================================================
#  Réordonnancement
# ===========================================================================

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


# ===========================================================================
#  UIList
# ===========================================================================

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


# ===========================================================================
#  MENU CLIC DROIT — via UI_MT_list_item_context_menu (vide nativement !)
# ---------------------------------------------------------------------------
#  Ce menu d'items de UIList n'a AUCUNE entrée native (draw = pass). On y
#  greffe nos actions, filtrées pour n'apparaître QUE sur notre liste
#  (reconnue via context.button_prop.identifier == INDEX_PROP).
# ===========================================================================

class ANIM_MT_raccoon_clip_specials(bpy.types.Menu):
    """Menu d'actions sur le clip — 100% à nous, sans aucune entrée native
    (un Menu invoqué en clic GAUCHE n'a pas d'injection native du C Blender)."""
    bl_idname = "ANIM_MT_raccoon_clip_specials"
    bl_label = "Actions sur le clip"

    def draw(self, context):
        action = active_clip_action(context)
        layout = self.layout
        layout.label(text=action.name if action else "Clip", icon='ACTION')
        layout.separator()
        layout.operator("anim.raccoon_clip_duplicate", icon='DUPLICATE')
        layout.operator("anim.raccoon_clip_mirror", icon='MOD_MIRROR')
        layout.operator("anim.raccoon_clip_reverse", icon='LOOP_BACK')
        layout.separator()
        layout.operator("anim.raccoon_clip_delete", icon='TRASH')


def cleanup_button_menu():
    """Purge les restes de nos anciennes tentatives sur les menus clic-droit
    (greffes nommées) qui pouvaient polluer / casser le natif."""
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
    cleanup_button_menu()   # démantèle les vieux hooks clic-droit


def unregister_context_menu():
    cleanup_button_menu()


# ===========================================================================
#  Raccourci clavier : Suppr supprime le clip survolé (uniquement notre liste)
# ===========================================================================

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


classes = (
    ANIM_OT_raccoon_clip_new,
    ANIM_OT_raccoon_clip_duplicate,
    ANIM_OT_raccoon_clip_delete,
    ANIM_OT_raccoon_clip_reverse,
    ANIM_OT_raccoon_clip_mirror,
    ANIM_OT_raccoon_clip_move,
    ANIM_OT_raccoon_clip_delete_key,
    ANIM_UL_raccoon_clips,
    ANIM_MT_raccoon_clip_specials,
)
