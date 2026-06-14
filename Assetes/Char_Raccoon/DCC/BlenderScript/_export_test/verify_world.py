"""
Validation finale : positions MONDE des os.

  Unity   : wpos des os après échantillonnage de Test 1.anim à t=1.0s
  Blender : têtes d'os frame 24 (armature space), converties par _defMatrix

Si la sérialisation est bonne, les écarts doivent être ~0.
"""
import json, os, re
from mathutils import Matrix, Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(HERE, name)) as fh:
        txt = fh.read()
    txt = re.sub(r'(\d),(\d)', r'\1.\2', txt)
    return json.loads(txt)


def trs_to_mat(d):
    q = Quaternion(d["quat"])
    m = q.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= d["scale"][j]
    m.translation = Vector(d["pos"])
    return m


TEST = os.environ.get("VERIFY_TEST", "test1")
rest  = load("blender_rest.json")              # pour les parents
pose  = load(f"blender_pose_{TEST}.json")      # locaux parent-relatifs
upose = load(f"unity_pose_{TEST}.json")
print(f"[{TEST}]  blender t={pose.get('_t', '?')}  unity t={upose.get('_time', '?')}")

defM = Matrix([upose["_defMatrix"][i*4:(i+1)*4] for i in range(4)])

# Chaîner les locaux Blender → matrices armature-space
world = {}
def chain(name):
    if name in world:
        return world[name]
    m = trs_to_mat(pose[name])
    par = rest[name]["parent"]
    if par:
        m = chain(par) @ m
    world[name] = m
    return m

uw = {p.split("/")[-1]: d["wpos"] for p, d in upose.items()
      if not p.startswith("_") and p.startswith("Def/")}

MIR = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0))   # miroir X (espace armature)

errs = []
for name in pose:
    if name.startswith("_") or name not in uw:
        continue
    pb = chain(name).translation
    # monde Unity attendu = defM @ ( S · Ĝ @ p_blender ),  S = 0.01
    pred = (defM @ (MIR @ pb)) * 0.01
    u = Vector(uw[name])
    errs.append(((pred - u).length, name, tuple(round(v, 4) for v in pred),
                 tuple(round(v, 4) for v in u)))

errs.sort(reverse=True)
n = len(errs)
mean = sum(e[0] for e in errs) / n
print(f"os comparés : {n}   erreur moyenne : {mean:.5f} m   max : {errs[0][0]:.5f} m")
print("\npires écarts :")
for e, name, p, u in errs[:8]:
    print(f"  {e:8.5f}  {name:24}  pred={p}  unity={u}")
print("\nmeilleurs :")
for e, name, p, u in errs[-3:]:
    print(f"  {e:8.5f}  {name:24}")
