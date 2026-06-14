"""
Sérialisation directe de fichiers Unity .anim (YAML) depuis les poses évaluées
du Def — sans passer par FBX.

Conversion d'espace : basis empiriques par os
---------------------------------------------
Unity applique les valeurs des courbes TELLES QUELLES dans localPosition /
localRotation (vérifié par échantillonnage batchmode). Il faut donc écrire les
locaux EXACTS de la hiérarchie Unity, qui vient de l'import FBX du modèle —
et l'exporteur FBX re-base chaque os de façon non uniforme (aucun swizzle
global n'est correct).

Modèle mesuré (unity_basis.json, généré par _export_test/compute_basis.py
depuis un dump batchmode du squelette importé — erreur monde validée = 0) :

    L_unity(b,t) = scaleTrans_s( A_b @ L_blender(b,t) @ H_b )

 - H_b : rotation pure par os (basis FBX)
 - A_b = H_parent^-1, ou Ĝ = diag(-1,1,1) pour les os racine (miroir X)
 - s = 0.01 appliqué aux SEULES translations (les locaux Unity sont en
   mètres/100, compensés par le scale ×100 du nœud Def)

⚠ Si le squelette change : re-générer unity_basis.json
   (test_dump_rest.py + DumpSkeleton.Run + compute_basis.py).

Chemins de binding :
    Def/root/spine/…   (os)        classID 4   (Transform)
    MSH_xxx            (mesh)      classID 137 (SkinnedMeshRenderer, blendShape.*)
"""

import bpy
import os
import json

from mathutils import Matrix

from . import config
from . import exporter


# ---------------------------------------------------------------------------
# Basis par os (mesurées sur le squelette réellement importé dans Unity)
# ---------------------------------------------------------------------------

_BASIS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "unity_basis.json")


def load_basis():
    """{bone: (path, A, H, s)} depuis unity_basis.json."""
    with open(_BASIS_FILE, encoding='utf-8') as fh:
        raw = json.load(fh)
    out = {}
    for bone, d in raw.items():
        Ubind = Matrix([d["Ubind"][i*4:(i+1)*4] for i in range(4)])
        Bbinv = Matrix([d["Bbinv"][i*4:(i+1)*4] for i in range(4)])
        Q     = Matrix([d["Q"][i*4:(i+1)*4] for i in range(4)])
        out[bone] = (d["path"], Ubind, Bbinv, Q, d["s"])
    return out


def _bone_local(ev, pb):
    """Matrice locale de l'os par rapport à son parent (espace armature)."""
    if pb.parent:
        return ev.pose.bones[pb.parent.name].matrix.inverted() @ pb.matrix
    return pb.matrix.copy()


# ---------------------------------------------------------------------------
# Émission YAML avec tangentes linéaires
# ---------------------------------------------------------------------------

def _slopes(vals, i, dt):
    """(inSlope, outSlope) par différences finies — interpolation quasi linéaire."""
    n = len(vals)
    in_s  = (vals[i] - vals[i - 1]) / dt if i > 0     else 0.0
    out_s = (vals[i + 1] - vals[i]) / dt if i < n - 1 else 0.0
    return in_s, out_s


def _emit_keys(times, comps, dt, fields):
    """comps : liste par composante de listes de valeurs ; fields : 'xyz'/'xyzw'."""
    lines = []
    n_f = len(fields)
    weights = ", ".join(f"{f}: 0.33333334" for f in fields)
    for i, t in enumerate(times):
        sl   = [_slopes(comps[k], i, dt) for k in range(n_f)]
        val  = ", ".join(f"{fields[k]}: {comps[k][i]:.6g}" for k in range(n_f))
        ins  = ", ".join(f"{fields[k]}: {sl[k][0]:.6g}"    for k in range(n_f))
        outs = ", ".join(f"{fields[k]}: {sl[k][1]:.6g}"    for k in range(n_f))
        lines.append(
            f"      - serializedVersion: 3\n"
            f"        time: {t:.6g}\n"
            f"        value: {{{val}}}\n"
            f"        inSlope: {{{ins}}}\n"
            f"        outSlope: {{{outs}}}\n"
            f"        tangentMode: 0\n"
            f"        weightedMode: 0\n"
            f"        inWeight: {{{weights}}}\n"
            f"        outWeight: {{{weights}}}"
        )
    return "\n".join(lines)


def _emit_float_keys(times, vals, dt):
    lines = []
    for i, t in enumerate(times):
        in_s, out_s = _slopes(vals, i, dt)
        lines.append(
            f"      - serializedVersion: 3\n"
            f"        time: {t:.6g}\n"
            f"        value: {vals[i]:.6g}\n"
            f"        inSlope: {in_s:.6g}\n"
            f"        outSlope: {out_s:.6g}\n"
            f"        tangentMode: 0\n"
            f"        weightedMode: 0\n"
            f"        inWeight: 0.33333334\n"
            f"        outWeight: 0.33333334"
        )
    return "\n".join(lines)


def _curve_block(path, keys_body, rotation_order=False, attribute=None, class_id=4):
    rot = "      m_RotationOrder: 4\n" if rotation_order else ""
    attr = f"    attribute: {attribute}\n" if attribute else ""
    return (
        f"  - curve:\n"
        f"      serializedVersion: 2\n"
        f"      m_Curve:\n"
        f"{keys_body}\n"
        f"      m_PreInfinity: 2\n"
        f"      m_PostInfinity: 2\n"
        f"{rot}"
        f"{attr}"
        f"    path: {path}\n"
        f"    classID: {class_id}\n"
        f"    script: {{fileID: 0}}\n"
    )


# ---------------------------------------------------------------------------
# Writer principal
# ---------------------------------------------------------------------------

def write_anim(filepath, clip_name, context, ctrl_obj, def_obj, action, rng):
    """Bake frame-by-frame du Def évalué et écrit un .anim Unity."""
    scene = context.scene
    fps = scene.render.fps / scene.render.fps_base
    dt  = 1.0 / fps
    start, end = rng

    exporter._reset_to_default(ctrl_obj)
    exporter._assign_action(ctrl_obj, action)
    scene.frame_start = start
    scene.frame_end   = end
    context.view_layer.update()

    basis = load_basis()

    # Meshes skinnés au Def → courbes blendshapes
    skinned = [o for o in bpy.data.objects
               if o.type == 'MESH'
               and o.data.shape_keys
               and any(m.type == 'ARMATURE' and m.object is def_obj
                       for m in o.modifiers)]

    # Seuls les os présents dans la basis (= présents dans le FBX importé)
    bones = [pb for pb in def_obj.pose.bones if pb.name in basis]
    bone_paths = [basis[pb.name][0] for pb in bones]
    pos   = {p: ([], [], [])     for p in bone_paths}   # x, y, z
    rot   = {p: ([], [], [], []) for p in bone_paths}   # x, y, z, w
    scl   = {p: ([], [], [])     for p in bone_paths}
    shape = {}                                          # (mesh, key) -> [vals]
    times = []

    prev_q = {}
    for f in range(start, end + 1):
        scene.frame_set(f)
        context.view_layer.update()
        dg = context.evaluated_depsgraph_get()
        ev = def_obj.evaluated_get(dg)
        times.append((f - start) * dt)

        for pb in bones:
            p, Ubind, Bbinv, Q, s = basis[pb.name]
            ev_pb = ev.pose.bones[pb.name]

            # Retarget : delta Blender (relatif au bind) converti dans l'espace Unity
            # puis appliqué au bind Unity. dB.translation passe en m/100 (s=0.01).
            dB = Bbinv @ _bone_local(ev, ev_pb)
            dB.translation = dB.translation * s
            L = Ubind @ Q.inverted() @ dB @ Q
            loc, q, sc = L.decompose()

            # Continuité : garder le quaternion dans le même hémisphère
            lq = prev_q.get(p)
            if lq is not None and (q.dot(lq) < 0.0):
                q = -q
            prev_q[p] = q

            for k, v in enumerate((loc.x, loc.y, loc.z)):
                pos[p][k].append(v)
            for k, v in enumerate((sc.x, sc.y, sc.z)):
                scl[p][k].append(v)
            for k, v in enumerate((q.x, q.y, q.z, q.w)):    # ordre Unity
                rot[p][k].append(v)

        for o in skinned:
            ev_m = o.evaluated_get(dg)
            sk = ev_m.data.shape_keys
            if not sk:
                continue
            for kb in sk.key_blocks[1:]:                 # skip Basis
                shape.setdefault((o.name, kb.name), []).append(kb.value * 100.0)

    stop_time = max((end - start) * dt, dt)

    rot_block = "".join(
        _curve_block(p, _emit_keys(times, rot[p], dt, "xyzw"), rotation_order=True)
        for p in bone_paths)
    pos_block = "".join(
        _curve_block(p, _emit_keys(times, pos[p], dt, "xyz"))
        for p in bone_paths)
    scl_block = "".join(
        _curve_block(p, _emit_keys(times, scl[p], dt, "xyz"))
        for p in bone_paths)

    if shape:
        float_block = "".join(
            _curve_block(mesh, _emit_float_keys(times, vals, dt),
                         rotation_order=True,
                         attribute=f"blendShape.{key}", class_id=137)
            for (mesh, key), vals in shape.items())
        float_section = f"  m_FloatCurves:\n{float_block}"
    else:
        float_section = "  m_FloatCurves: []\n"

    yaml = (
        f"%YAML 1.1\n"
        f"%TAG !u! tag:unity3d.com,2011:\n"
        f"--- !u!74 &7400000\n"
        f"AnimationClip:\n"
        f"  m_ObjectHideFlags: 0\n"
        f"  m_CorrespondingSourceObject: {{fileID: 0}}\n"
        f"  m_PrefabInstance: {{fileID: 0}}\n"
        f"  m_PrefabAsset: {{fileID: 0}}\n"
        f"  m_Name: {clip_name}\n"
        f"  serializedVersion: 6\n"
        f"  m_Legacy: 0\n"
        f"  m_Compressed: 0\n"
        f"  m_UseHighQualityCurve: 1\n"
        f"  m_RotationCurves:\n"
        f"{rot_block}"
        f"  m_CompressedRotationCurves: []\n"
        f"  m_EulerCurves: []\n"
        f"  m_PositionCurves:\n"
        f"{pos_block}"
        f"  m_ScaleCurves:\n"
        f"{scl_block}"
        f"{float_section}"
        f"  m_PPtrCurves: []\n"
        f"  m_SampleRate: {fps:.6g}\n"
        f"  m_WrapMode: 0\n"
        f"  m_Bounds:\n"
        f"    m_Center: {{x: 0, y: 0, z: 0}}\n"
        f"    m_Extent: {{x: 0, y: 0, z: 0}}\n"
        f"  m_ClipBindingConstant:\n"
        f"    genericBindings: []\n"
        f"    pptrCurveMapping: []\n"
        f"  m_AnimationClipSettings:\n"
        f"    serializedVersion: 2\n"
        f"    m_AdditiveReferencePoseClip: {{fileID: 0}}\n"
        f"    m_AdditiveReferencePoseTime: 0\n"
        f"    m_StartTime: 0\n"
        f"    m_StopTime: {stop_time:.6g}\n"
        f"    m_OrientationOffsetY: 0\n"
        f"    m_Level: 0\n"
        f"    m_CycleOffset: 0\n"
        f"    m_HasAdditiveReferencePose: 0\n"
        f"    m_LoopTime: 1\n"
        f"    m_LoopBlend: 0\n"
        f"    m_LoopBlendOrientation: 0\n"
        f"    m_LoopBlendPositionY: 0\n"
        f"    m_LoopBlendPositionXZ: 0\n"
        f"    m_KeepOriginalOrientation: 0\n"
        f"    m_KeepOriginalPositionY: 1\n"
        f"    m_KeepOriginalPositionXZ: 0\n"
        f"    m_HeightFromFeet: 0\n"
        f"    m_Mirror: 0\n"
        f"  m_EditorCurves: []\n"
        f"  m_EulerEditorCurves: []\n"
        f"  m_HasMotionFloatCurves: 0\n"
        f"  m_Events: []\n"
    )

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(yaml)
