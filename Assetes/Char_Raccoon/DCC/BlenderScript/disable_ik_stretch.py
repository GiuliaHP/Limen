"""
Bride l'étirement d'un rig Rigify (générique, par détection).

Objectif : un stretch met du SCALE non-uniforme sur les os → shear inexportable
en TRS (.anim). On enlève ce qu'on ne veut pas, et on BRIDE ce qui reste utile.

Trois actions :
  1. MEMBRES — prop `*IK_Stretch*` : DÉFAUT + valeur à 0 (on n'en veut pas).
  2. TÊTE/COU — la translation du contrôle de tête est UTILE (expression) mais
     étire le cou si on va trop loin (×3+). On garde la translation MAIS on la
     BRIDE avec une contrainte Limit Location (≈ étirement max raisonnable).
     (On ré-active le STRETCH_TO du cou + on déverrouille la tête si une ancienne
     version du script les avait mutés/verrouillés.)

⚠️ Éléments du rig GÉNÉRÉ. Après un Rigify > Generate → relancer + sauver le .blend.
À lancer dans l'éditeur de texte Blender (Run Script).
"""

import bpy
import re

LIMIT_NAME = "Limit Head Translation"


def disable_ik_stretch(value=0.0):
    """DÉFAUT + valeur des props `*IK_Stretch*` (membres) → value."""
    n = 0
    for obj in bpy.data.objects:
        if obj.type != 'ARMATURE':
            continue
        for pb in obj.pose.bones:
            for k in list(pb.keys()):
                if "ik_stretch" in k.lower():
                    try:
                        pb.id_properties_ui(k).update(default=value)
                        pb[k] = value
                        n += 1
                    except Exception:
                        pass
        obj.update_tag()
    return n


def _is_head_control(name):
    if name.startswith(("ORG-", "DEF-", "MCH-", "VIS_")):
        return False
    base = re.sub(r"\.\d+$", "", name).lower()
    return base == "head" or base.endswith("_head")


def limit_head_translation(limit=0.08):
    """Contrainte Limit Location sur les contrôles de tête : translation bornée à
    ±`limit` (par axe) → le cou ne peut pas s'étirer au-delà d'une distance.
    limit ≈ 0.05→×1.3, 0.08→×1.5, 0.10→×1.8 d'étirement de cou (ajustable)."""
    n = 0
    for obj in bpy.data.objects:
        if obj.type != 'ARMATURE':
            continue
        for pb in obj.pose.bones:
            if not _is_head_control(pb.name):
                continue
            pb.lock_location = (False, False, False)   # cleanup ancienne version
            old = pb.constraints.get(LIMIT_NAME)
            if old:
                pb.constraints.remove(old)
            c = pb.constraints.new('LIMIT_LOCATION')
            c.name = LIMIT_NAME
            c.owner_space = 'LOCAL'
            c.use_transform_limit = True
            for ax in ("x", "y", "z"):
                setattr(c, f"use_min_{ax}", True)
                setattr(c, f"use_max_{ax}", True)
                setattr(c, f"min_{ax}", -limit)
                setattr(c, f"max_{ax}", limit)
            n += 1
        obj.update_tag()
    return n


def _unmute_neck_stretch():
    """Ré-active le STRETCH_TO du cou (au cas où une ancienne version l'a muté) —
    on veut que le cou suive la tête (étirement borné par la Limit Location)."""
    for obj in bpy.data.objects:
        if obj.type != 'ARMATURE':
            continue
        for pb in obj.pose.bones:
            if "MCH-STR" in pb.name:
                for c in pb.constraints:
                    if c.type == 'STRETCH_TO':
                        c.mute = False


def main(value=0.0, head_limit=0.08):
    n_ik = disable_ik_stretch(value)
    _unmute_neck_stretch()
    n_head = limit_head_translation(head_limit)
    bpy.context.view_layer.update()
    print(f"✅ {n_ik} IK_Stretch (membres) à 0 + {n_head} contrôle(s) tête bridé(s) "
          f"en translation (±{head_limit}).")
    if n_ik == 0 and n_head == 0:
        print("   ⚠️ rien trouvé (rig non généré, ou rig différent ?)")
    else:
        print("   (Sauve le .blend → fichier des animateurs. Relance après Rigify > Generate.)")
        print(f"   Ajuste la distance en changeant head_limit (ou la contrainte '{LIMIT_NAME}').")


if __name__ == "__main__":
    main(0.0, 0.08)
