"""
Test headless du writer .anim : exporte tous les clips dans _export_test
et fait des sanity-checks (parse, nb de courbes, valeurs racine).
"""
import bpy, sys, os

root_dir    = os.path.dirname(bpy.data.filepath)
script_root = os.path.join(root_dir, "BlenderScript")
if script_root not in sys.path:
    sys.path.insert(0, script_root)

ctrl = bpy.data.objects.get("RIG-CtrlRig")
defr = bpy.data.objects.get("Def")

from SetupDefContrites import Contrites_core as sdc
sdc.reload_core()
sdc.clear_rig_data("Def")
sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)

from AnimExport import core as anim_core
anim_core.reload_core()
from AnimExport.core import exporter, unity_anim

out_dir = os.path.join(root_dir, "_export_test")
os.makedirs(out_dir, exist_ok=True)

for action, rng in exporter.list_exportable_actions():
    name = exporter._sanitize(action.name)
    path = os.path.join(out_dir, name + ".anim")
    unity_anim.write_anim(path, action.name, bpy.context, ctrl, defr, action, rng)
    size = os.path.getsize(path)

    with open(path, encoding='utf-8') as fh:
        txt = fh.read()
    n_rot = txt.count("m_RotationOrder: 4")
    n_pos = txt.split("m_PositionCurves:")[1].split("m_ScaleCurves:")[0].count("- curve:")
    n_flt = txt.split("m_FloatCurves:")[1].split("m_PPtrCurves:")[0].count("- curve:") \
            if "m_FloatCurves:\n" in txt else 0
    print(f"OK  {name + '.anim':35} {size//1024:>5} Ko  "
          f"rot={n_rot} pos={n_pos} float={n_flt}  [{rng[0]}-{rng[1]}]")

# Sanity : valeurs du root au 1er frame de Test 1
print("\n--- extrait Test 1 (1re courbe rot, 1re clef) ---")
with open(os.path.join(out_dir, "Test 1.anim"), encoding='utf-8') as fh:
    txt = fh.read()
seg = txt.split("m_RotationCurves:")[1]
print("\n".join(seg.splitlines()[:8]))
print("path :", [l for l in seg.splitlines() if "path:" in l][0].strip())
print("=== FIN ===")
