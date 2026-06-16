"""Sérialisation YAML d'un AnimationClip Unity (!u!74) — pur texte, sans bpy.

Entrées déjà préparées (aucune notion d'os/armature ici) :
 - times        : liste de temps (s)
 - bone_curves  : liste de (path, pos[3 listes], rot[4 listes], scl[3 listes])
 - float_curves : liste de (path, attribute, vals[liste])   ex. blendShape.*

Courbes en tangentes linéaires (différences finies), ordre quaternion x,y,z,w.
"""


def _slopes(vals, i, dt):
    """(inSlope, outSlope) par différences finies — interpolation quasi linéaire."""
    n = len(vals)
    in_s = (vals[i] - vals[i - 1]) / dt if i > 0 else 0.0
    out_s = (vals[i + 1] - vals[i]) / dt if i < n - 1 else 0.0
    return in_s, out_s


def _emit_keys(times, comps, dt, fields):
    """comps : liste par composante de listes de valeurs ; fields : 'xyz'/'xyzw'."""
    lines = []
    n_f = len(fields)
    weights = ", ".join(f"{f}: 0.33333334" for f in fields)
    for i, t in enumerate(times):
        sl = [_slopes(comps[k], i, dt) for k in range(n_f)]
        val = ", ".join(f"{fields[k]}: {comps[k][i]:.6g}" for k in range(n_f))
        ins = ", ".join(f"{fields[k]}: {sl[k][0]:.6g}" for k in range(n_f))
        outs = ", ".join(f"{fields[k]}: {sl[k][1]:.6g}" for k in range(n_f))
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


def build_clip(clip_name, fps, times, bone_curves, float_curves):
    """Assemble le YAML complet d'un AnimationClip Unity."""
    dt = 1.0 / fps
    stop_time = max(times[-1], dt) if times else dt

    rot_block = "".join(
        _curve_block(p, _emit_keys(times, rot, dt, "xyzw"), rotation_order=True)
        for p, _pos, rot, _scl in bone_curves)
    pos_block = "".join(
        _curve_block(p, _emit_keys(times, pos, dt, "xyz"))
        for p, pos, _rot, _scl in bone_curves)
    scl_block = "".join(
        _curve_block(p, _emit_keys(times, scl, dt, "xyz"))
        for p, _pos, _rot, scl in bone_curves)

    if float_curves:
        # PAS de m_RotationOrder sur les float curves (blendshape) sinon Unity
        # peut ignorer la courbe.
        float_block = "".join(
            _curve_block(path, _emit_float_keys(times, vals, dt),
                         rotation_order=False, attribute=attr, class_id=137)
            for path, attr, vals in float_curves)
        float_section = f"  m_FloatCurves:\n{float_block}"
    else:
        float_section = "  m_FloatCurves: []\n"

    return (
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
