import bpy, sys
ROOT = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript"
sys.path.insert(0, ROOT)
ctx = bpy.context
MESH = "MSH_Racoon_Body"; F = 24


def verts():
    ev = bpy.data.objects[MESH].evaluated_get(ctx.evaluated_depsgraph_get())
    me = ev.to_mesh(); vs = [v.co.copy() for v in me.vertices]; ev.to_mesh_clear()
    return vs


def run():
    from SetupDefContrites import Contrites_core as sdc
    sdc.reload_core()
    defr = bpy.data.objects["Def"]; ctrl = bpy.data.objects["RIG-CtrlRig"]
    from AnimExport.core import exporter

    # A) connecte + stretch (etat original)
    sdc.clear_rig_data("Def"); sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
    exporter._reset_to_default(ctrl); exporter._assign_action(ctrl, bpy.data.actions["Test 2"])
    ctx.scene.frame_set(F); ctx.view_layer.update()
    va = verts()

    # B) deconnecte + stretch
    ctx.view_layer.objects.active = defr
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in defr.data.edit_bones: eb.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    sdc.clear_rig_data("Def"); sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
    exporter._reset_to_default(ctrl); exporter._assign_action(ctrl, bpy.data.actions["Test 2"])
    ctx.scene.frame_set(F); ctx.view_layer.update()
    vb = verts()

    n = len(va); d = sorted(((va[i]-vb[i]).length for i in range(n)), reverse=True)
    print(f"connecte+stretch vs deconnecte+stretch : moy={sum(d)/n*1000:.2f}mm max={d[0]*1000:.2f}mm")
    print("  -> si ~0 : on peut deconnecter en permanence sans changer l'adulte cible")


run()
