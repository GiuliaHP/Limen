import bpy
import os
import re
from . import config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize(name):
    """Nom de fichier sûr à partir d'un nom d'Action."""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def _resolve_export_dir(context):
    """Chemin absolu du dossier de sortie (fixé dans config.py, non exposé à l'UI)."""
    path = bpy.path.abspath(config.EXPORT_DIR)
    return os.path.normpath(path)


def _action_frame_range(action):
    """(start, end) entiers, ou None si l'action est vide / dégénérée."""
    fr = action.frame_range
    start, end = round(fr[0]), round(fr[1])
    if end <= start:
        return None
    return start, end


# Plage utilisée pour un clip vide : 1 frame → anim statique (rest pose)
STATIC_RANGE = (1, 1)


def export_range(action):
    """Plage à exporter : celle de l'action, ou STATIC_RANGE si elle est vide."""
    return _action_frame_range(action) or STATIC_RANGE


def list_exportable_actions():
    """Tous les clips cochés 'export' (les clips vides s'exportent en statique)."""
    return [(a, export_range(a)) for a in bpy.data.actions
            if getattr(a, "raccoon_export", True)]


# ---------------------------------------------------------------------------
# Reset / assign
# ---------------------------------------------------------------------------

def _prop_default(owner, key):
    try:
        return owner.id_properties_ui(key).as_dict().get("default")
    except Exception:
        return None


def _reset_to_default(src):
    """Remet le rig à son état par défaut AVANT d'assigner un clip.

    Sans ça, un os/prop non keyé dans le clip garderait la valeur résiduelle
    du clip précédent. Les canaux keyés seront ré-écrasés par la courbe.
    """
    for pb in src.pose.bones:
        pb.location          = (0.0, 0.0, 0.0)
        pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pb.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
        pb.rotation_euler    = (0.0, 0.0, 0.0)
        pb.scale             = (1.0, 1.0, 1.0)
        for key in list(pb.keys()):
            d = _prop_default(pb, key)
            if d is not None:
                try:
                    pb[key] = d
                except Exception:
                    pass
    for key in list(src.keys()):
        d = _prop_default(src, key)
        if d is not None:
            try:
                src[key] = d
            except Exception:
                pass


def _assign_action(anim_obj, action):
    """Assigne une Action à l'objet, en gérant les slots de Blender 4.4+/5.0."""
    if anim_obj.animation_data is None:
        anim_obj.animation_data_create()
    ad = anim_obj.animation_data
    ad.action = action
    if hasattr(ad, "action_slot") and getattr(action, "slots", None):
        try:
            ad.action_slot = action.slots[0]
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Export d'un clip
# ---------------------------------------------------------------------------

def _export_one(context, action, rng, anim_obj, deform_obj, out_dir):
    """Exporte UNE action en FBX anim-only du Def. Renvoie (ok, message)."""
    scene = context.scene
    start, end = rng

    # 1. Assigner l'action sur le ctrl rig (il pilote le Def via contraintes)
    _reset_to_default(anim_obj)
    _assign_action(anim_obj, action)

    # 2. Plage scène
    scene.frame_start = start
    scene.frame_end   = end
    scene.frame_set(start)
    context.view_layer.update()

    # 3. Sélectionner QUE le Def
    for o in context.view_layer.objects:
        o.select_set(False)
    deform_obj.select_set(True)
    context.view_layer.objects.active = deform_obj

    # 4. Export FBX — le bake interne évalue les contraintes (COPY_TRANSFORMS + STRETCH_TO)
    filepath = os.path.join(out_dir, _sanitize(action.name) + ".fbx")
    try:
        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=True,
            object_types={'ARMATURE'},
            use_armature_deform_only=False,
            add_leaf_bones=False,
            bake_anim=True,
            bake_anim_use_all_bones=True,
            bake_anim_use_nla_strips=False,
            bake_anim_use_all_actions=False,
            bake_anim_force_startend_keying=True,
            bake_anim_step=1.0,
            bake_anim_simplify_factor=0.1,
            axis_forward='-Z',
            axis_up='Y',
            apply_scale_options='FBX_SCALE_NONE',
            global_scale=1.0,
            apply_unit_scale=True,
            path_mode='AUTO',
        )
        return True, f"{action.name}  →  {os.path.basename(filepath)}  [{start}-{end}]"
    except Exception as e:
        return False, f"{action.name} : échec export ({e})"
