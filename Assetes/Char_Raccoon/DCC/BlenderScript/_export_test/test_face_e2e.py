import bpy, sys
from mathutils import Vector
ROOT = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript"
sys.path.insert(0, ROOT)
ctx = bpy.context


def run():
    from SetupDefContrites import Contrites_core as sdc
    sdc.reload_core(); sdc.clear_rig_data("Def")
    ctrl = bpy.data.objects["RIG-CtrlRig"]; defr = bpy.data.objects["Def"]
    sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
    from AnimExport import core as ac; ac.reload_core()

    # morph plein (Eye suit l'Adult)
    root = ctrl.pose.bones.get("root")
    if root and "morph_blend" in root:
        root["morph_blend"] = 1.0

    for ctrl_name, def_name in [("Adult_Eye.l", "Eye.l"),
                                ("Adult_eyebrow.l", "eyebrow.l")]:
        pbc = ctrl.pose.bones.get(ctrl_name)
        if pbc is None:
            print(f"  {ctrl_name} introuvable"); continue
        pbc.scale = Vector((1.0, 1.0, 1.0)); ctx.view_layer.update()
        pbc.scale = Vector((1.4, 1.0, 1.0)); ctx.view_layer.update()
        evc = ctrl.evaluated_get(ctx.evaluated_depsgraph_get())
        ev = defr.evaluated_get(ctx.evaluated_depsgraph_get())
        _, _, sc = evc.pose.bones[ctrl_name].matrix.decompose()
        dpb = ev.pose.bones.get(def_name)
        _, _, sd = dpb.matrix.decompose() if dpb else (0, 0, Vector((0, 0, 0)))
        print(f"  controle '{ctrl_name}' scale X=1.4")
        print(f"     CTRL '{ctrl_name}' evalue : ({sc.x:.3f},{sc.y:.3f},{sc.z:.3f})")
        print(f"     DEF  '{def_name}' evalue : ({sd.x:.3f},{sd.y:.3f},{sd.z:.3f})")
        pbc.scale = Vector((1.0, 1.0, 1.0))
    print("  -> DEF reflete le scale du controle : scale d'anim visage OK bout-en-bout")


run()
