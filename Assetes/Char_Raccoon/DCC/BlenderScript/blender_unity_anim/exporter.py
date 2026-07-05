"""
Writer .anim Unity — conversion ANALYTIQUE (taniwha/io_object_mu), sans calibration.

Chaque os : on prend sa pose LOCALE (relative au parent, espace armature Blender),
on la convertit dans la base Unity (cf. convert.py), on écrit le TRS verbatim.
Aucune basis empirique, aucun FBX, aucun facteur d'unité : le modèle entre dans
Unity via l'importeur custom (même conversion) → os et anim cohérents par
construction. Unités = mètres (l'importeur n'applique pas de ×100).

Blendshapes des meshes skinnés → courbes blendShape.* (classID 137).
"""

import os

import bpy

from .retarget import bone_local
from . import convert
from .yaml_clip import build_clip


def skinned_blendshape_meshes(armature):
    return [o for o in bpy.data.objects
            if o.type == 'MESH'
            and o.data.shape_keys
            and any(m.type == 'ARMATURE' and m.object is armature
                    for m in o.modifiers)]


def _bone_path(armature, bone_name, root):
    bones = {b.name: b for b in armature.data.bones}
    parts = []
    cur = bones.get(bone_name)
    while cur:
        parts.append(cur.name)
        cur = cur.parent
    parts.reverse()
    chain = "/".join(parts)
    # root vide → pas de préfixe (les os sont enfants directs de l'Animator côté Unity)
    return f"{root}/{chain}" if root else chain


def _noscale_world(matrix):
    """Matrice monde avec scale NON-UNIFORME retiré (→ position+rotation, scale 1).
    Le scale uniforme est conservé (il commute, pas de shear). Renvoie (matrix, flattened)."""
    loc, q, s = matrix.decompose()
    if max(s) - min(s) <= 1e-3:        # uniforme (ou ~1) → on garde tel quel
        return matrix, False
    m = q.to_matrix().to_4x4()         # scale non-uniforme → 1 (joints gardés par la translation)
    m.translation = loc
    return m, True


def write_anim(filepath, clip_name, context, deform_armature, frames,
               *, root_name="", blendshape_meshes=None, blendshape_scale=100.0,
               flatten_nonuniform_scale=True):
    """Écrit un .anim Unity depuis les poses évaluées de `deform_armature`.

    root_name : préfixe de chemin des os côté Unity. Vide ("") = os enfants directs
                de l'Animator (cohérent avec le loader custom).
    flatten_nonuniform_scale : convertit le scale d'os NON-UNIFORME en TRANSLATION
                — on garde la position monde de chaque joint (l'allongement) mais on
                met le scale à 1 → plus de shear inexportable en TRS. Le mesh s'étire
                via le blend de skinning. UNIQUEMENT sur les os à ENFANTS (qui
                cisailleraient leurs enfants). Les os FEUILLES gardent leur scale
                non-uniforme (exportable tel quel, ex. squash de joue/œil/sourcil/nez).
    """
    scene = context.scene
    fps = scene.render.fps / scene.render.fps_base
    root = root_name

    frames = list(frames)
    if not frames:
        raise ValueError("write_anim : aucune frame à exporter")
    f0 = frames[0]
    dt = 1.0 / fps

    bones = list(deform_armature.pose.bones)
    paths = {pb.name: _bone_path(deform_armature, pb.name, root) for pb in bones}
    pos = {pb.name: ([], [], []) for pb in bones}
    rot = {pb.name: ([], [], [], []) for pb in bones}
    scl = {pb.name: ([], [], []) for pb in bones}
    shape = {}
    times = []
    prev_q = {}

    if blendshape_meshes is None:
        blendshape_meshes = skinned_blendshape_meshes(deform_armature)

    for f in frames:
        scene.frame_set(f)
        context.view_layer.update()
        dg = context.evaluated_depsgraph_get()
        ev = deform_armature.evaluated_get(dg)
        times.append((f - f0) * dt)

        # mondes par os. Scale non-uniforme aplati UNIQUEMENT sur les os à enfants
        # (qui shearent). GARDÉ sur : les FEUILLES (squash facial : joue/œil/nez…)
        # et les os marqués `keep_nonuniform_scale` (ex. museau — l'enfant quasi
        # aligné ne prend qu'un petit shear, acceptable). pb = os ORIGINAL (props).
        if flatten_nonuniform_scale:
            wns = {}
            for pb in bones:
                W = ev.pose.bones[pb.name].matrix
                keep = (not pb.children) or bool(pb.get("keep_nonuniform_scale"))
                wns[pb.name] = W if keep else _noscale_world(W)[0]
        for pb in bones:
            ev_pb = ev.pose.bones[pb.name]
            if flatten_nonuniform_scale:
                par = ev_pb.parent
                Wb = wns[pb.name]
                local = (wns[par.name].inverted() @ Wb) if (par and par.name in wns) else Wb
            else:
                local = bone_local(ev, ev_pb)
            p, q, s = convert.local_to_unity(local)  # (x,y,z),(x,y,z,w),(x,y,z)

            lq = prev_q.get(pb.name)        # continuité d'hémisphère du quaternion
            if lq is not None and sum(a * b for a, b in zip(q, lq)) < 0.0:
                q = tuple(-c for c in q)
            prev_q[pb.name] = q

            for k in range(3):
                pos[pb.name][k].append(p[k])
                scl[pb.name][k].append(s[k])
            for k in range(4):
                rot[pb.name][k].append(q[k])

        for o in blendshape_meshes:
            ev_m = o.evaluated_get(dg)
            sk = ev_m.data.shape_keys
            if not sk:
                continue
            for kb in sk.key_blocks[1:]:   # skip Basis
                shape.setdefault((o.name, kb.name), []).append(kb.value * blendshape_scale)

    bone_curves = [(paths[pb.name], pos[pb.name], rot[pb.name], scl[pb.name]) for pb in bones]
    float_curves = [(mesh, f"blendShape.{key}", vals) for (mesh, key), vals in shape.items()]

    yaml = build_clip(clip_name, fps, times, bone_curves, float_curves)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(yaml)
    return filepath
