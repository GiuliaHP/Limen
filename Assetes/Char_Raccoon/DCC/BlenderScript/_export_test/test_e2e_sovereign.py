"""
Preuve end-to-end (Blender seul) du pipeline souverain :
  modèle JSON (bind+verts+poids+blendshape, espace Unity) + anim (convert) +
  skinning façon Unity  ==  mesh Blender réel.

Si l'écart est ~0 sur Test 2 frame 24 (morph plein), tout le pipeline (exporteur
modèle + parser .anim + loader Unity) est correct par construction.
"""
import bpy, sys, importlib, json, tempfile, os, traceback
from mathutils import Matrix, Quaternion, Vector
sys.path.insert(0, r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript")
ctx = bpy.context
MESH = "MSH_Racoon_Body"
F = 24


def swap(v):  # M = swap(x,z,y), involutif (M^-1 = M)
    return Vector((v.x, v.z, v.y))


def umat(p, q, s):
    """(pos(x,y,z), quat(x,y,z,w), scale) Unity → Matrix 4x4."""
    m = Quaternion((q[3], q[0], q[1], q[2])).to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= s[j]
    m.translation = Vector(p)
    return m


def run():
    import blender_unity_anim as bua
    bua.reload()
    from SetupDefContrites import Contrites_core as sdc
    importlib.reload(sdc); sdc.reload_core()
    defr = bpy.data.objects["Def"]; ctrl = bpy.data.objects["RIG-CtrlRig"]
    sdc.clear_rig_data("Def")
    sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT, use_stretch=False)
    from AnimExport.core import exporter as axe
    axe._reset_to_default(ctrl); axe._assign_action(ctrl, bpy.data.actions["Test 2"])

    # 1) modèle JSON
    jp = os.path.join(tempfile.gettempdir(), "m.json")
    bua.export_model(jp, defr, ctx, name="Chara_Raccoon")
    M = json.loads(open(jp).read())
    bones = M["bones"]; bidx = {b["name"]: i for i, b in enumerate(bones)}
    body = next(m for m in M["meshes"] if m["name"] == MESH)
    vc = len(body["vertices"]) // 3
    verts = [Vector((body["vertices"][i*3], body["vertices"][i*3+1], body["vertices"][i*3+2])) for i in range(vc)]
    adult = next(s for s in body["blendshapes"] if s["name"] == "Adult_shape")
    dv = [Vector((adult["deltaVertices"][i*3], adult["deltaVertices"][i*3+1], adult["deltaVertices"][i*3+2])) for i in range(vc)]

    # bind world + bindpose
    bindW = [None]*len(bones)
    for i, b in enumerate(bones):
        L = umat(b["pos"], b["rot"], b["scale"])
        bindW[i] = (bindW[b["parent"]] @ L) if b["parent"] >= 0 else L
    bindpose = [w.inverted() for w in bindW]

    # 2) pose animée frame F (convert depuis Blender) → world Unity
    ctx.scene.frame_set(F); ctx.view_layer.update()
    ev = defr.evaluated_get(ctx.evaluated_depsgraph_get())
    mb = ctrl.pose.bones["root"]["morph_blend"]
    animW = [None]*len(bones)
    # ordre parents d'abord = ordre JSON
    for i, b in enumerate(bones):
        pb = ev.pose.bones[b["name"]]
        Lloc = (ev.pose.bones[pb.parent.name].matrix.inverted() @ pb.matrix) if pb.parent else pb.matrix.copy()
        p, q, s = bua.convert.local_to_unity(Lloc)
        Lu = umat(p, q, s)
        animW[i] = (animW[b["parent"]] @ Lu) if b["parent"] >= 0 else Lu

    # 3) skinning Unity-style, puis inverse-swap → espace Blender
    ptr = 0
    pred = []
    for v in range(vc):
        base = verts[v] + dv[v] * mb           # Basis + morph (espace Unity)
        acc = Vector((0, 0, 0))
        n = body["bonesPerVertex"][v]
        for k in range(n):
            bi = body["boneIndices"][ptr+k]; w = body["boneWeights"][ptr+k]
            skinmat = animW[bi] @ bindpose[bi]
            acc += (skinmat @ base.to_4d()).to_3d() * w
        ptr += n
        pred.append(swap(acc))                 # retour espace Blender

    # 4) mesh Blender réel
    em = bpy.data.objects[MESH].evaluated_get(ctx.evaluated_depsgraph_get())
    me = em.to_mesh()
    arm_to_mesh = bpy.data.objects[MESH].matrix_world.inverted() @ defr.matrix_world
    # pred est en espace armature → ramener en espace mesh-local pour comparer
    mesh_to_arm = defr.matrix_world.inverted() @ bpy.data.objects[MESH].matrix_world
    truth = [v.co.copy() for v in me.vertices]
    em.to_mesh_clear()
    pred_mesh = [(defr.matrix_world.inverted() @ bpy.data.objects[MESH].matrix_world).inverted() @ p for p in pred]

    d = sorted(((truth[i] - pred_mesh[i]).length for i in range(vc)), reverse=True)
    print(f"=== E2E souverain (Test 2 frame {F}, morph={mb:.2f}) ===")
    print(f"  écart Unity-simulé vs Blender : moy={sum(d)/vc*1000:.3f}mm  max={d[0]*1000:.3f}mm  ({vc} verts)")
    print("  -> ~0 : modèle + anim + loader corrects par construction (sans FBX, sans calibration)")


try:
    run()
except Exception:
    traceback.print_exc()
