"""
Re-bake du blendshape Adult_shape par dé-skinning (méthode UpadateBlendShape).

La forme adulte cible = des meshes SCULPTÉS à la main `.BlendShape_<mesh>`
(même topologie). On "un-pose" leurs positions contre la pose adulte des os
(production, morph=1) pour obtenir le shape key en espace repos :

    Adult_shape[i] = Mblend(pose adulte)^-1 @ sculpt_pos[i]

Au runtime : os production (morph=1) + Adult_shape(1) reproduit le sculpt.
Le morph adulte = os position+rotation (exportable) + ce blendshape (exact).

Le bouton enchaîne : setup rig production → morph=1 (action neutralisée) →
un-pose des sculpts → driver Adult_shape.value = morph_blend.
"""

import bpy
from mathutils import Matrix

from . import applier

SHAPE_NAME = "Adult_shape"
SCULPT_PREFIX = ".BlendShape_"     # sculpt cible = .BlendShape_<nom_mesh>
MASTER_BONE = "root"
BLEND_PROP = "morph_blend"


# ---------------------------------------------------------------------------
# Pose adulte (neutralise l'action sinon elle écrase morph_blend)
# ---------------------------------------------------------------------------

def _neutralize(obj):
    saved = None
    if obj.animation_data is not None:
        saved = obj.animation_data.action
        obj.animation_data.action = None
    for pb in obj.pose.bones:
        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pb.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.scale = (1.0, 1.0, 1.0)
    return saved


def _restore_action(obj, action):
    if action is not None:
        if obj.animation_data is None:
            obj.animation_data_create()
        obj.animation_data.action = action


def _set_morph(ctrl_rig, value):
    root = ctrl_rig.pose.bones.get(MASTER_BONE)
    if root is not None and BLEND_PROP in root:
        root[BLEND_PROP] = value
        # update_tag() indispensable : sans lui view_layer.update() ne ré-évalue
        # pas les drivers qui lisent la custom-prop (influences + valeur shape).
        ctrl_rig.update_tag()


# ---------------------------------------------------------------------------
# Un-pose d'un sculpt → shape key (méthode UpadateBlendShape)
# ---------------------------------------------------------------------------

def _bone_matrices(arm):
    """{bone: pose.matrix @ rest.matrix_local^-1} (espace armature), os déformants.
    Lit l'armature ÉVALUÉE → reflète les contraintes."""
    ev = arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
    out = {}
    for pb in ev.pose.bones:
        if not pb.bone.use_deform:
            continue
        out[pb.name] = pb.matrix @ pb.bone.matrix_local.inverted()
    return out


def _unpose(orig, sculpt):
    """Écrit Adult_shape sur `orig` en un-posant les positions de `sculpt`."""
    arm = next((m.object for m in orig.modifiers
                if m.type == 'ARMATURE' and m.object), None)
    if arm is None:
        raise ValueError(f"Aucun modifier Armature sur '{orig.name}'")

    vo, vs = orig.data.vertices, sculpt.data.vertices
    if len(vo) != len(vs):
        raise ValueError(f"Topologie différente : {orig.name}({len(vo)}) "
                         f"vs {sculpt.name}({len(vs)})")

    bmats = _bone_matrices(arm)
    C = orig.matrix_world.inverted() @ arm.matrix_world
    C_inv = C.inverted()
    s2o = orig.matrix_world.inverted() @ sculpt.matrix_world   # local sculpt → local orig
    idx2name = {vg.index: vg.name for vg in orig.vertex_groups}

    # shape key propre + ré-exécutable
    if orig.data.shape_keys is None:
        orig.shape_key_add(name="Basis", from_mix=False)
    else:
        old = orig.data.shape_keys.key_blocks.get(SHAPE_NAME)
        if old:
            orig.shape_key_remove(old)
    sk = orig.shape_key_add(name=SHAPE_NAME, from_mix=False)

    eps = 1e-9
    maxd = 0.0
    for i, v in enumerate(vo):
        p_def = s2o @ vs[i].co
        acc, wtot = None, 0.0
        for g in v.groups:
            nm = idx2name.get(g.group)
            Mi = bmats.get(nm)
            if Mi is None or g.weight == 0.0:
                continue
            term = Mi * g.weight
            acc = term if acc is None else acc + term
            wtot += g.weight
        if acc is not None and wtot > eps:
            Mlocal = C @ (acc * (1.0 / wtot)) @ C_inv
            try:
                co = Mlocal.inverted() @ p_def
            except ValueError:
                co = p_def
        else:
            co = p_def
        sk.data[i].co = co
        maxd = max(maxd, (co - v.co).length)
    return maxd


def _ensure_driver(orig, ctrl_rig):
    sk = orig.data.shape_keys
    kb = sk.key_blocks[SHAPE_NAME]
    data_path = kb.path_from_id("value")
    if sk.animation_data:
        for d in list(sk.animation_data.drivers):
            if d.data_path == data_path:
                sk.driver_remove(data_path)
    drv = sk.driver_add(data_path).driver
    drv.type = 'SCRIPTED'
    var = drv.variables.new()
    var.name = "blend"
    var.type = 'SINGLE_PROP'
    tgt = var.targets[0]
    tgt.id = ctrl_rig
    tgt.data_path = f'pose.bones["{MASTER_BONE}"]["{BLEND_PROP}"]'
    drv.expression = "blend"


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def _pairs(def_rig):
    """(orig, sculpt) pour chaque mesh skinné ayant un sculpt .BlendShape_<nom>."""
    out = []
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        if not any(m.type == 'ARMATURE' and m.object is def_rig for m in o.modifiers):
            continue
        sculpt = bpy.data.objects.get(SCULPT_PREFIX + o.name)
        if sculpt and sculpt.type == 'MESH':
            out.append((o, sculpt))
    return out


def update_adult_shape(def_rig, ctrl_rig, mapping_dict, morph_frame=0):
    """Met le rig en pose adulte (production, morph=1) et re-bake Adult_shape par
    un-pose des sculpts .BlendShape_*. Assigne le driver. Laisse le rig production."""
    ctx = bpy.context
    pairs = _pairs(def_rig)
    if not pairs:
        print(f"⚠️  Aucun sculpt '{SCULPT_PREFIX}<mesh>' trouvé.")
        return 0, f"aucun sculpt {SCULPT_PREFIX}* trouvé"

    # 1) rig production + pose adulte neutre (morph=1, action neutralisée)
    from .cleaner import clear_rig_data
    saved = _neutralize(ctrl_rig)
    clear_rig_data(def_rig.name)
    applier.apply_constraints_from_dict(def_rig, ctrl_rig, mapping_dict, use_stretch=False)
    ctx.scene.frame_set(morph_frame)
    _set_morph(ctrl_rig, 1.0)
    ctx.view_layer.update()

    # 2) un-pose chaque sculpt + driver
    report, n = [], 0
    for orig, sculpt in pairs:
        try:
            maxd = _unpose(orig, sculpt)
            _ensure_driver(orig, ctrl_rig)
            n += 1
            report.append(f"{orig.name}: OK (max delta {maxd*1000:.1f}mm) <- {sculpt.name}")
        except Exception as e:
            report.append(f"{orig.name}: ÉCHEC ({e})")

    # 3) restaure l'action, laisse morph=1 (drivé)
    _restore_action(ctrl_rig, saved)
    _set_morph(ctrl_rig, 1.0)
    ctx.view_layer.update()

    for r in report:
        print("   " + r)
    print(f"✅ Adult_shape re-baké sur {n} mesh(es).")
    return n, f"{n} mesh(es) re-bakés"
