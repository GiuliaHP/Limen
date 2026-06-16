"""
Teste la conversion ANALYTIQUE io_object_mu (taniwha) contre la verite-terrain
Unity (ulocal_bind.json, squelette FBX importe), au bind/rest.

io_object_mu (par canal LOCAL) :
  pos   Unity(x,y,z) = Blender(x, z, y)
  quat  Unity(w,x,y,z) = Blender(w, -x, -z, -y)
  scale Unity(x,y,z) = Blender(x, z, y)

Si l'erreur est ~0 sur les os profonds (parent=os) : l'analytique marche pour
notre FBX → on peut jeter la basis empirique. Sinon : le FBX re-base.
"""
import bpy, sys, os, json
from mathutils import Matrix, Quaternion, Vector
HERE = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript/_export_test"
sys.path.insert(0, r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript")
ctx = bpy.context

ub = json.loads(open(os.path.join(HERE, "ulocal_bind.json")).read())
defr = bpy.data.objects["Def"]
defbones = {b.name: b for b in defr.data.bones}


def upath(bone):
    parts = []; cur = defbones.get(bone)
    while cur: parts.append(cur.name); cur = cur.parent
    parts.reverse(); return "Def/" + "/".join(parts)


# locaux Blender au REST (parent-relatif, espace armature)
ctx.scene.frame_set(0); ctx.view_layer.update()
ev = defr.evaluated_get(ctx.evaluated_depsgraph_get())


def blocal(name):
    pb = ev.pose.bones[name]
    if pb.parent:
        return pb.parent.matrix.inverted() @ pb.matrix
    return pb.matrix.copy()


def iomu(L):
    """Conversion io_object_mu d'une matrice locale Blender → TRS Unity."""
    loc, q, s = L.decompose()
    pos_u = Vector((loc.x, loc.z, loc.y))
    quat_u = Quaternion((q.w, -q.x, -q.z, -q.y))
    scl_u = Vector((s.x, s.z, s.y))
    return pos_u, quat_u, scl_u


def trs(d):
    return Vector(d["pos"]), Quaternion(d["quat"]), Vector(d["scale"])


errs = []
for name, b in defbones.items():
    p = upath(name)
    if p not in ub:
        continue
    has_bone_parent = b.parent is not None
    pos_u, quat_u, scl_u = iomu(blocal(name))
    tpos, tquat, tscl = trs(ub[p])
    dp = (pos_u - tpos).length
    dq = min((quat_u - tquat).magnitude, (quat_u + tquat).magnitude)  # signe libre
    errs.append((dq, dp, name, has_bone_parent))

errs.sort(reverse=True)
deep = [e for e in errs if e[3]]   # parent = os
print("=== io_object_mu vs Unity FBX (bind) — os profonds (parent=os) ===")
for dq, dp, n, _ in deep[:8]:
    print(f"   {n:24s} dquat={dq:.4f}  dpos={dp*1000:.2f}mm")
import statistics
print(f"  mediane dquat (os profonds) = {statistics.median([e[0] for e in deep]):.4f}")
print(f"  #os profonds dquat<0.01 : {sum(1 for e in deep if e[0]<0.01)}/{len(deep)}")
print("  -> si ~tous <0.01 : analytique OK. Sinon : FBX re-base, basis empirique requise.")
