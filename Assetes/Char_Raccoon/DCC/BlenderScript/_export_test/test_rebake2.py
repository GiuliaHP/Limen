import bpy, sys, traceback
ROOT = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript"
sys.path.insert(0, ROOT)
ctx = bpy.context


def set_morph(ctrl, v):
    ctrl.pose.bones["root"]["morph_blend"] = v
    ctrl.update_tag(); ctx.view_layer.update()


def eval_verts(name):
    o = bpy.data.objects[name]
    ev = o.evaluated_get(ctx.evaluated_depsgraph_get())
    me = ev.to_mesh(); vs = [v.co.copy() for v in me.vertices]; ev.to_mesh_clear()
    return vs


def run():
    import importlib
    from SetupDefContrites import Contrites_core as sdc
    importlib.reload(sdc); sdc.reload_core()
    defr = bpy.data.objects["Def"]; ctrl = bpy.data.objects["RIG-CtrlRig"]

    # assigne une action pour SIMULER le cas UI (action qui pilote morph_blend)
    from AnimExport.core import exporter
    exporter._assign_action(ctrl, bpy.data.actions["Test 2"])
    ctx.scene.frame_set(1)   # morph_blend=0 a la frame 1 (piege)
    ctx.view_layer.update()

    print("--- update_adult_shape (avec action Test 2 assignee, frame 1) ---")
    n, msg = sdc.update_adult_shape(defr, ctrl, sdc.MAPPING_DICT)
    print("retour:", n, msg)

    # validation : production + Adult_shape(1) vs sculpt .BlendShape_*
    set_morph(ctrl, 1.0)
    print("\n--- VALIDATION : production+Adult_shape(morph=1) vs sculpt ---")
    for orig, sculpt in (("MSH_Racoon_Body", ".BlendShape_MSH_Racoon_Body"),
                         ("MSH_Racoon_TailDetails", ".BlendShape_MSH_Racoon_TailDetails")):
        got = eval_verts(orig)
        # sculpt en local orig
        so = bpy.data.objects[sculpt]; oo = bpy.data.objects[orig]
        s2o = oo.matrix_world.inverted() @ so.matrix_world
        tgt = [s2o @ v.co for v in so.data.vertices]
        nN = len(got)
        d = sorted(((tgt[i] - got[i]).length for i in range(nN)), reverse=True)
        print(f"  {orig}: moy={sum(d)/nN*1000:.3f}mm max={d[0]*1000:.3f}mm ({nN} verts)")

    set_morph(ctrl, 0.0)
    sk = bpy.data.objects["MSH_Racoon_Body"].data.shape_keys
    print(f"\n  morph=0 -> Adult_shape value = {sk.key_blocks['Adult_shape'].value:.3f} (doit 0)")


try:
    run()
except Exception:
    traceback.print_exc()
