"""
Export modèle : mesh + squelette Def + blendshapes, SANS animation.
"""
import bpy, sys, os

root_dir    = os.path.dirname(bpy.data.filepath)
script_root = os.path.join(root_dir, "BlenderScript")
if script_root not in sys.path:
    sys.path.insert(0, script_root)

defr = bpy.data.objects.get("Def")
if defr is None:
    print("ABORT : armature 'Def' introuvable"); sys.exit(1)

# --- Meshes skinnés au Def ---
skinned = [o for o in bpy.data.objects
           if o.type == 'MESH'
           and any(m.type == 'ARMATURE' and m.object is defr
                   for m in o.modifiers)]
print("=== Meshes skinnés au Def ===")
for o in skinned:
    sk = o.data.shape_keys
    n_sk = len(sk.key_blocks) - 1 if sk else 0   # -1 : on exclut la Basis
    print(f"  {o.name:30}  blendshapes={n_sk}")

if not skinned:
    print("  Aucun mesh skinné trouvé."); sys.exit(1)

# --- Export ---
out_dir  = os.path.normpath(os.path.join(root_dir, "..", "Output", "Model"))
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "Raccoon.fbx")

# Bind pose : aucune action active, frame 0
for o in bpy.context.view_layer.objects:
    o.select_set(False)
defr.select_set(True)
for o in skinned:
    o.select_set(True)
bpy.context.view_layer.objects.active = defr

if defr.animation_data:
    defr.animation_data.action = None
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()

bpy.ops.export_scene.fbx(
    filepath=out_path,
    use_selection=True,
    object_types={'ARMATURE', 'MESH'},
    use_mesh_modifiers=True,
    use_armature_deform_only=False,
    add_leaf_bones=False,
    bake_anim=False,                   # PAS d'animation
    axis_forward='-Z',
    axis_up='Y',
    apply_scale_options='FBX_SCALE_NONE',
    global_scale=1.0,
    apply_unit_scale=True,
    path_mode='AUTO',
    mesh_smooth_type='FACE',
)

size = os.path.getsize(out_path)
print(f"\nOK → {out_path}")
print(f"   Taille : {size:,} octets")
