"""
Résolution du personnage par PATTERN (aucun nom d'objet en dur).

Conventions :
  - armature de déformation : "DEF-<Char>"   (ex. DEF-Player)
  - rig de contrôle          : "RIG-<Char>"   (ex. RIG-Player)
  - <Char> = ce qui suit le préfixe.

On résout depuis l'OBJET ACTIF (armature DEF-/RIG-, ou mesh skinné/bone-parenté
à une DEF-). Morph détecté par la présence de la prop `morph_blend` sur un os du
ctrl (pas de nom d'os en dur).

Nommage : clips `ANIM_<Char>_<nom>`, modèle `CHAR_<Char>` (.racmodel).
"""

import bpy

DEF_PREFIX = "DEF-"
RIG_PREFIX = "RIG-"
MORPH_PROP = "morph_blend"


def char_of(def_arm):
    n = def_arm.name
    return n[len(DEF_PREFIX):] if n.startswith(DEF_PREFIX) else n


def find_def_armature(obj):
    """Remonte à l'armature DEF-<Char> depuis n'importe quel objet du perso."""
    if obj is None:
        return None
    if obj.type == 'ARMATURE':
        if obj.name.startswith(DEF_PREFIX):
            return obj
        if obj.name.startswith(RIG_PREFIX):
            return bpy.data.objects.get(DEF_PREFIX + obj.name[len(RIG_PREFIX):])
    if obj.type == 'MESH':
        for m in obj.modifiers:
            if m.type == 'ARMATURE' and m.object and m.object.name.startswith(DEF_PREFIX):
                return m.object
        if obj.parent and obj.parent.type == 'ARMATURE' and obj.parent.name.startswith(DEF_PREFIX):
            return obj.parent
    return None


def resolve(context):
    """(def_armature, ctrl_rig, char) depuis l'objet actif ; (None, None, None) sinon."""
    obj = getattr(context, "active_object", None) or context.view_layer.objects.active
    def_arm = find_def_armature(obj)
    if def_arm is None:
        return None, None, None
    char = char_of(def_arm)
    ctrl = bpy.data.objects.get(RIG_PREFIX + char)
    return def_arm, ctrl, char


def morph_bone(ctrl):
    """Os du ctrl portant `morph_blend` (détection, pas de nom en dur), ou None."""
    if ctrl is None:
        return None
    for pb in ctrl.pose.bones:
        if MORPH_PROP in pb:
            return pb
    return None


def has_morph(ctrl):
    return morph_bone(ctrl) is not None


# --- nommage ---------------------------------------------------------------

def clip_name(char, action_name):
    return f"ANIM_{char}_{action_name}"


def model_name(char):
    return f"CHAR_{char}"


def model_filename(char):
    return f"CHAR_{char}.racmodel"
