"""
Diagnostic : où la chaîne casse-t-elle ?
 A. rest : defM @ blender_rest_world  vs  wpos Unity rest   (doit matcher si defM ok)
 B. rest : chaîne des locaux Unity + defM                   (cohérence interne dump)
 C. pose : quels os ont bougé dans Blender vs Unity
"""
import json, os, re
from mathutils import Matrix, Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

def load(n):
    txt = open(n).read()
    return json.loads(re.sub(r'(\d),(\d)', r'\1.\2', txt))

def trs_to_mat(d):
    q = Quaternion(d["quat"])
    m = q.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= d["scale"][j]
    m.translation = Vector(d["pos"])
    return m

b_rest = load("blender_rest.json")
u_rest = load("unity_rest.json")
u_pose = load("unity_pose_test1.json")
b_pose = load("blender_pose_test1.json")

defM = Matrix([u_pose["_defMatrix"][i*4:(i+1)*4] for i in range(4)])
print("defM :")
for r in range(4):
    print("   ", [round(v, 4) for v in defM[r]])

# Monde blender rest
bw = {}
def bchain(n, data, parent_of):
    if n in bw: return bw[n]
    m = trs_to_mat(data[n])
    p = parent_of(n)
    if p: m = bchain(p, data, parent_of) @ m
    bw[n] = m
    return m

# A. rest : defM @ blender_world vs unity wpos (rest dump)
print("\nA. defM @ blender_rest vs unity rest wpos :")
for name in ["root", "spine", "head", "Ear.l", "hand.L", "foot.L"]:
    if name not in b_rest: continue
    pb = bchain(name, b_rest, lambda n: b_rest[n]["parent"]).translation
    pred = defM @ pb
    upath = [k for k in u_rest if not k.startswith("_") and k.split("/")[-1] == name]
    if not upath: continue
    u = Vector(u_rest[upath[0]]["wpos"])
    print(f"   {name:10} pred={tuple(round(v,3) for v in pred)}  unity={tuple(round(v,3) for v in u)}  err={(pred-u).length:.4f}")

# B. cohérence interne : defM @ chaîne(locals unity) vs wpos
print("\nB. defM @ chaîne(locals Unity rest) vs wpos rest :")
uw_loc = {k[len('Def/'):]: trs_to_mat(v) for k, v in u_rest.items()
          if k.startswith("Def/")}
chains = {}
for path in sorted(uw_loc, key=lambda p: p.count("/")):
    par = path.rsplit("/", 1)[0] if "/" in path else None
    chains[path] = (chains[par] @ uw_loc[path]) if par else uw_loc[path].copy()
worst = 0; wname = ""
for path, m in chains.items():
    u = Vector(u_rest["Def/" + path]["wpos"])
    e = (defM @ m.translation - u).length
    if e > worst: worst, wname = e, path
print(f"   erreur max : {worst:.5f}  ({wname})")

# C. os animés : Blender vs Unity
def moved(rest_d, pose_d, keys):
    out = set()
    for k in keys:
        r, p = rest_d.get(k), pose_d.get(k)
        if not r or not p: continue
        dq = max(abs(a-b) for a, b in zip(r["quat"], p["quat"]))
        dp = max(abs(a-b) for a, b in zip(r["pos"],  p["pos"]))
        if dq > 1e-3 or dp > 1e-4:
            out.add(k.split("/")[-1])
    return out

bk = [k for k in b_pose if not k.startswith("_")]
uk = [k for k in u_pose if not k.startswith("_")]
b_moved = moved(b_rest, b_pose, bk)
# unity : comparer par chemin
u_moved = moved({k: v for k, v in u_rest.items()},
                {k: v for k, v in u_pose.items()}, uk)
print(f"\nC. os bougés Blender : {len(b_moved)}, Unity : {len(u_moved)}")
print("   Blender seulement :", sorted(b_moved - u_moved)[:12])
print("   Unity seulement   :", sorted(u_moved - b_moved)[:12])
