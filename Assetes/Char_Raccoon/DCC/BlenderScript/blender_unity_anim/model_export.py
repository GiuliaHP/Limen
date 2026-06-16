"""
Exporteur modèle souverain Blender → JSON (consommé par le loader Unity custom).

Tout est converti dans la base Unity ICI (via convert.py), comme le .anim → le
loader Unity bâtit verbatim, sans math de coordonnées. Aucun FBX.

Le swap (x,z,y) est une RÉFLEXION (det -1) → il inverse le sens des triangles :
on renverse donc le winding (a,b,c)→(a,c,b) et on garde les normales converties.

Format JSON :
{
  "name": "...",
  "bones": [ {"name","parent":idx|-1,"pos":[3],"rot":[xyzw],"scale":[3]}, ... ],
  "meshes": [ {
     "name", "vertices":[[3]], "normals":[[3]], "uvs":[[2]],
     "triangles":[int...], "bonesPerVertex":[int...],
     "boneIndices":[int...], "boneWeights":[float...],   # aplatis, longueur = somme(bonesPerVertex)
     "blendshapes":[ {"name","deltaVertices":[[3]],"deltaNormals":[[3]]} ]
  } ]
}
Les bindposes sont calculées côté loader (bone.worldToLocalMatrix au bind).
"""

import json
import os

import bpy

from . import convert


def _swap_v(v):
    return (v.x, v.z, v.y)


def _bone_hierarchy(arm):
    """Liste ordonnée (parents avant enfants) + index par nom. Bind local Unity."""
    bones = list(arm.data.bones)
    # tri topologique (parents d'abord)
    ordered = sorted(bones, key=lambda b: len(b.parent_recursive))
    index = {b.name: i for i, b in enumerate(ordered)}
    out = []
    for b in ordered:
        # bind local Blender = parent_rest^-1 @ rest
        if b.parent:
            L = b.parent.matrix_local.inverted() @ b.matrix_local
            parent = index[b.parent.name]
        else:
            L = b.matrix_local.copy()
            parent = -1
        pos, rot, scl = convert.local_to_unity(L)
        out.append({"name": b.name, "parent": parent,
                    "pos": list(pos), "rot": list(rot), "scale": list(scl)})
    return out, index


def _mesh_data(obj, arm, bone_index, max_weights=255, weight_eps=1e-4):
    me = obj.data
    mesh_to_arm = arm.matrix_world.inverted() @ obj.matrix_world

    # rest = Basis si shape keys, sinon les coords du mesh
    if me.shape_keys:
        basis = me.shape_keys.key_blocks[0].data
        rest = [mesh_to_arm @ basis[i].co for i in range(len(me.vertices))]
    else:
        rest = [mesh_to_arm @ v.co for v in me.vertices]

    # normales (par vertex) en espace armature
    nrm_rot = mesh_to_arm.to_3x3()
    vnormals = [(nrm_rot @ v.normal).normalized() for v in me.vertices]

    vertices = [_swap_v(co) for co in rest]
    normals = [_swap_v(n) for n in vnormals]

    # UV (premier layer)
    uvs = [[0.0, 0.0] for _ in me.vertices]
    if me.uv_layers:
        uvl = me.uv_layers[0].data
        for loop in me.loops:
            uvs[loop.vertex_index] = [uvl[loop.index].uv.x, uvl[loop.index].uv.y]

    # matériaux + sous-meshes (un submesh par slot matériau)
    mats, triangles, submeshIndexCounts = _triangles_by_material(obj, me)

    # poids (top-N normalisés) → indices dans bones[]
    gname = {g.index: g.name for g in obj.vertex_groups}
    bpv, bidx, bw = [], [], []
    for v in me.vertices:
        ws = []
        for g in v.groups:
            n = gname.get(g.group)
            if n in bone_index and g.weight > weight_eps:
                ws.append((bone_index[n], g.weight))
        ws.sort(key=lambda x: x[1], reverse=True)   # Unity attend des poids décroissants
        ws = ws[:max_weights]
        tot = sum(w for _, w in ws)
        if tot <= 1e-8:
            ws = [(0, 1.0)]; tot = 1.0
        bpv.append(len(ws))
        for bi, w in ws:
            bidx.append(bi); bw.append(w / tot)

    # blendshapes (deltas vs Basis) — aplatis. Le delta est un VECTEUR : on lui
    # applique la rotation mesh→armature (comme les verts) puis le swap, sinon
    # incohérence d'espace si le mesh n'est pas aligné sur l'armature.
    shapes = []
    if me.shape_keys:
        kbs = me.shape_keys.key_blocks
        basis = kbs[0].data
        m2a3 = mesh_to_arm.to_3x3()
        for kb in kbs[1:]:
            dV = []
            for i in range(len(me.vertices)):
                d = _swap_v(m2a3 @ (kb.data[i].co - basis[i].co))
                dV += [d[0], d[1], d[2]]
            shapes.append({"name": kb.name, "deltaVertices": dV})

    # tout aplati en 1D (compatible JsonUtility côté Unity, sans librairie)
    vflat, nflat, uflat = [], [], []
    for v in vertices:
        vflat += [v[0], v[1], v[2]]
    for n in normals:
        nflat += [n[0], n[1], n[2]]
    for u in uvs:
        uflat += [u[0], u[1]]

    return {"name": obj.name,
            "vertices": vflat,
            "normals": nflat,
            "uvs": uflat,
            "triangles": triangles,
            "materials": mats,
            "submeshIndexCounts": submeshIndexCounts,
            "bonesPerVertex": bpv,
            "boneIndices": bidx,
            "boneWeights": bw,
            "blendshapes": shapes}


def _triangles_by_material(obj, me):
    """(materials, triangles aplatis groupés par submesh, submeshIndexCounts).
    Winding renversé (a,c,b) pour compenser la réflexion du swap."""
    mats = [(s.material.name if s.material else f"{obj.name}_mat") for s in obj.material_slots]
    if not mats:
        mats = [f"{obj.name}_mat"]
    me.calc_loop_triangles()
    by_mat = {i: [] for i in range(len(mats))}
    for t in me.loop_triangles:
        mi = min(t.material_index, len(mats) - 1)
        a, b, c = (t.vertices[0], t.vertices[1], t.vertices[2])
        by_mat[mi] += [a, c, b]
    tris, smc = [], []
    for i in range(len(mats)):
        tris += by_mat[i]
        smc.append(len(by_mat[i]))
    return mats, tris, smc


def _rigid_mesh_data(obj, arm, context):
    """Mesh RIGIDE parenté à un os (yeux, nez…) : modifiers appliqués (évalué),
    childé à l'os côté Unity avec sa transform relative (rest)."""
    dg = context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        vflat, nflat, uflat = [], [], []
        for v in me.vertices:
            c = _swap_v(v.co); vflat += [c[0], c[1], c[2]]
            n = _swap_v(v.normal); nflat += [n[0], n[1], n[2]]
        uvs = [[0.0, 0.0] for _ in me.vertices]
        if me.uv_layers:
            uvl = me.uv_layers[0].data
            for loop in me.loops:
                uvs[loop.vertex_index] = [uvl[loop.index].uv.x, uvl[loop.index].uv.y]
        for u in uvs:
            uflat += [u[0], u[1]]
        mats, tris, smc = _triangles_by_material(obj, me)
    finally:
        ev.to_mesh_clear()

    bone = arm.data.bones[obj.parent_bone]
    rigid_local = bone.matrix_local.inverted() @ (arm.matrix_world.inverted() @ obj.matrix_world)
    p, q, s = convert.local_to_unity(rigid_local)
    return {"name": obj.name, "bone": obj.parent_bone,
            "pos": list(p), "rot": list(q), "scale": list(s),
            "vertices": vflat, "normals": nflat, "uvs": uflat,
            "triangles": tris, "materials": mats, "submeshIndexCounts": smc}


def _material_def(name):
    """Propriétés d'un matériau Blender → couleur/metallic/smoothness (équivalent FBX)."""
    mat = bpy.data.materials.get(name)
    base = [0.8, 0.8, 0.8, 1.0]
    metal, rough = 0.0, 0.5
    if mat:
        bsdf = None
        if mat.use_nodes:
            bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf:
            base = list(bsdf.inputs['Base Color'].default_value)
            metal = float(bsdf.inputs['Metallic'].default_value)
            rough = float(bsdf.inputs['Roughness'].default_value)
        else:
            c = mat.diffuse_color
            base = [c[0], c[1], c[2], c[3]]
            metal = float(getattr(mat, "metallic", 0.0))
            rough = float(getattr(mat, "roughness", 0.5))
    return {"name": name, "baseColor": base, "metallic": metal, "smoothness": 1.0 - rough}


def export_model(filepath, deform_armature, context, name=None):
    """Écrit le modèle (skinné + rigides bone-parentés + os + blendshapes + matériaux)
    en JSON. La scène doit être en pose de REPOS (l'appelant reset le ctrl)."""
    name = name or deform_armature.name
    bones, bone_index = _bone_hierarchy(deform_armature)

    skinned, rigid = [], []
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        if any(m.type == 'ARMATURE' and m.object is deform_armature for m in o.modifiers):
            skinned.append(o)
        elif o.parent is deform_armature and o.parent_type == 'BONE' and o.parent_bone:
            rigid.append(o)

    meshes = [_mesh_data(o, deform_armature, bone_index) for o in skinned]
    rigid_meshes = [_rigid_mesh_data(o, deform_armature, context) for o in rigid]

    used = set()
    for m in meshes + rigid_meshes:
        used.update(m["materials"])
    materials = [_material_def(n) for n in sorted(used)]

    data = {"name": name, "bones": bones, "meshes": meshes,
            "rigidMeshes": rigid_meshes, "materials": materials}
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    nv = sum(len(m["vertices"]) // 3 for m in meshes) + sum(len(m["vertices"]) // 3 for m in rigid_meshes)
    return filepath, len(bones), nv
