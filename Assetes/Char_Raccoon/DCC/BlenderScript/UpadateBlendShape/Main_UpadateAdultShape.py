import bpy
from mathutils import Matrix

# =========================== CONFIG ===========================
SHAPEKEY_NAME = "Adult_shape"

# Paires : (mesh original AVEC modifier Armature + vertex groups,
#           sculpt déformée dont on ne lit QUE les positions)
PAIRS = [
    ("MSH_Racoon_Body",        ".BlendShape_MSH_Racoon_Body"),
    ("MSH_Racoon_TailDetails", ".BlendShape_MSH_Racoon_TailDetails"),
]
# ==============================================================

_bone_cache = {}


def get_obj(name):
    o = bpy.data.objects.get(name)
    if not o:
        raise ValueError(f"Objet introuvable : '{name}'")
    if o.type != 'MESH':
        raise ValueError(f"'{name}' n'est pas un mesh.")
    return o


def find_armature(orig):
    """Récupère l'armature depuis le modifier Armature du mesh original."""
    for mod in orig.modifiers:
        if mod.type == 'ARMATURE' and mod.object:
            return mod.object
    raise ValueError(f"Aucun modifier Armature trouvé sur '{orig.name}'")


def bone_matrices(arm):
    """{nom_bone: M_armspace = pose * rest^-1} pour les bones deformants.
    Lit la POSE ACTUELLE -> l'armature doit etre dans la pose problematique."""
    if arm.name in _bone_cache:
        return _bone_cache[arm.name]
    m = {}
    for pb in arm.pose.bones:
        if not pb.bone.use_deform:
            continue
        m[pb.name] = pb.matrix @ pb.bone.matrix_local.inverted()
    _bone_cache[arm.name] = m
    return m


def unpose(orig, sculpt):
    arm = find_armature(orig)
    bmats = bone_matrices(arm)

    vo = orig.data.vertices
    vs = sculpt.data.vertices
    if len(vo) != len(vs):
        raise ValueError(
            f"Topologie differente : {orig.name}({len(vo)}) vs {sculpt.name}({len(vs)})"
        )

    # Matrices de passage espace mesh <-> espace armature
    C = orig.matrix_world.inverted() @ arm.matrix_world
    C_inv = C.inverted()
    # Position sculpt (local sculpt) -> local orig
    s2o = orig.matrix_world.inverted() @ sculpt.matrix_world

    idx2name = {vg.index: vg.name for vg in orig.vertex_groups}

    # Shapekey propre + re-executable
    if orig.data.shape_keys is None:
        orig.shape_key_add(name="Basis", from_mix=False)
    else:
        kb = orig.data.shape_keys.key_blocks.get(SHAPEKEY_NAME)
        if kb:
            orig.shape_key_remove(kb)
    sk = orig.shape_key_add(name=SHAPEKEY_NAME, from_mix=False)

    eps = 1e-9
    for i, v in enumerate(vo):
        p_def = s2o @ vs[i].co  # position deformee, en local orig

        # Matrice de skin melangee (LBS) en espace armature
        acc = None
        wtot = 0.0
        for g in v.groups:
            nm = idx2name.get(g.group)
            if nm is None:
                continue
            Mi = bmats.get(nm)
            if Mi is None or g.weight == 0.0:
                continue
            term = Mi * g.weight
            acc = term if acc is None else acc + term
            wtot += g.weight

        if acc is not None and wtot > eps:
            Mblend = acc * (1.0 / wtot)          # normalisation des poids
            Mlocal = C @ Mblend @ C_inv          # en espace mesh local
            try:
                sk.data[i].co = Mlocal.inverted() @ p_def  # un-pose
            except ValueError:
                sk.data[i].co = p_def            # matrice non inversible
        else:
            sk.data[i].co = p_def                # vertex non deforme

    print(f"[OK] '{orig.name}' <- shapekey '{SHAPEKEY_NAME}' "
          f"({len(vo)} verts) via armature '{arm.name}'")


def main():
    bpy.context.view_layer.update()  # s'assure que la pose courante est evaluee
    for o_name, s_name in PAIRS:
        unpose(get_obj(o_name), get_obj(s_name))
    print("Termine.")


main()