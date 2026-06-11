import bpy

# --- CONFIG ---
MASTER_BONE_NAME = "root"          # Os porteur de la propriété de blend (sur le ctrl_rig)
BLEND_PROP       = "morph_blend"   # 0.0 = Child  /  1.0 = Adult
HELPER_COLL      = "Def_RT_Joints" # collection des empties-joints (n'exporte pas)


# ===========================================================================
#  STRATÉGIE : helpers de joint blendés + STRETCH_TO permanent (méthode Rigify)
# ---------------------------------------------------------------------------
#  Par os qui a un joint suivant :
#    COPY_TRANSFORMS (World) Child inf=1  + Adult inf=blend  → base (tête+roll)
#    STRETCH_TO (World) → EMPTY "JNT_<os>" inf=1
#       keep_axis=SWING_Y (préserve le roll), VOLUME_XZX, rest_length=Child
#
#  L'empty JNT suit le joint SUIVANT, blendé Child↔Adult :
#    COPY_LOCATION → ctrl joint Child suivant  inf=1
#    COPY_LOCATION → ctrl joint Adult suivant  inf=blend
#
#  → L'empty est hors de la chaîne du Def : PAS de cycle.
#  → Il est au joint blendé (bouge avec morph_blend au même rythme que la tête)
#    : PAS d'explosion à la transition (1 seule cible cohérente).
#  → Il traque le ctrl en live : l'étirement ANIMÉ est suivi.
#  Les bouts de chaîne (pas de joint suivant) n'ont que le COPY_TRANSFORMS.
# ===========================================================================


# --- DRIVERS ---

def _config_driver(fcurve, ctrl_rig, expression):
    drv = fcurve.driver
    drv.type = 'SCRIPTED'
    var = drv.variables.new()
    var.name = "blend"
    var.type = 'SINGLE_PROP'
    tgt = var.targets[0]
    tgt.id = ctrl_rig
    tgt.data_path = f'pose.bones["{MASTER_BONE_NAME}"]["{BLEND_PROP}"]'
    drv.expression = expression
    return fcurve


def drive_influence(con, ctrl_rig, expression="blend"):
    return _config_driver(con.driver_add("influence"), ctrl_rig, expression)


# --- HELPERS DE JOINT (empties) ---

def _get_helper_collection():
    coll = bpy.data.collections.get(HELPER_COLL)
    if coll is None:
        coll = bpy.data.collections.new(HELPER_COLL)
        bpy.context.scene.collection.children.link(coll)
    return coll


def clear_helpers():
    """Supprime tous les empties-joints (appelé avant un nouveau setup)."""
    coll = bpy.data.collections.get(HELPER_COLL)
    if coll is None:
        return 0
    n = 0
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
        n += 1
    return n


def make_joint_helper(name, ctrl_rig, child_next, adult_next):
    """Empty qui suit le joint SUIVANT, blendé Child↔Adult."""
    coll = _get_helper_collection()
    e = bpy.data.objects.new(name, None)        # empty
    e.empty_display_type = 'PLAIN_AXES'
    e.empty_display_size = 0.02
    coll.objects.link(e)

    c = e.constraints.new('COPY_LOCATION')      # joint Child (base)
    c.target = ctrl_rig
    c.subtarget = child_next
    c.head_tail = 0.0

    c = e.constraints.new('COPY_LOCATION')      # joint Adult (drivé)
    c.target = ctrl_rig
    c.subtarget = adult_next
    c.head_tail = 0.0
    drive_influence(c, ctrl_rig, "blend")
    return e


# --- BUILDERS DE CONTRAINTES (os Def) ---

def add_copy_transforms(def_pb, ctrl_rig, subtarget, name, influence=1.0):
    con = def_pb.constraints.new('COPY_TRANSFORMS')
    con.name         = name
    con.target       = ctrl_rig
    con.subtarget    = subtarget
    con.head_tail    = 0.0
    con.mix_mode     = 'REPLACE'
    con.target_space = 'WORLD'
    con.owner_space  = 'WORLD'
    con.influence    = influence
    return con


def add_stretch_to_empty(def_pb, empty, name):
    con = def_pb.constraints.new('STRETCH_TO')
    con.name        = name
    con.target      = empty           # objet empty, pas de subtarget
    con.volume      = 'VOLUME_XZX'
    con.keep_axis   = 'SWING_Y'       # préserve le roll posé par COPY_TRANSFORMS
    con.rest_length = def_pb.bone.length   # repos = Child (le fix)
    return con


def _next_joint(ctrl_rig, bone_name):
    pb = ctrl_rig.pose.bones.get(bone_name)
    if pb is None:
        return None
    for child in pb.children:
        if child.bone.use_connect:
            return child.name
    return None


# --- COUCHES DE SETUP PAR OS ---

def setup_bone_blend(def_pb, ctrl_rig, child_name, adult_name):
    # BASE : COPY_TRANSFORMS (tête + roll), blendé
    add_copy_transforms(def_pb, ctrl_rig, child_name, "RT_Child", 1.0)
    c = add_copy_transforms(def_pb, ctrl_rig, adult_name, "RT_Adult")
    drive_influence(c, ctrl_rig, "blend")

    # STRETCH vers l'empty-joint blendé (si l'os a un joint suivant)
    nc = _next_joint(ctrl_rig, child_name)
    na = _next_joint(ctrl_rig, adult_name)
    if nc and na:
        e = make_joint_helper(f"JNT_{def_pb.name}", ctrl_rig, nc, na)
        add_stretch_to_empty(def_pb, e, "RT_Stretch")


def setup_bone_follow_parent(def_pb, ctrl_rig, target_name, present_side):
    expr = "1.0 - blend" if present_side == 'Child' else "blend"
    c = add_copy_transforms(def_pb, ctrl_rig, target_name, "RT", 0.0)
    drive_influence(c, ctrl_rig, expr)


def apply_constraints_from_dict(def_rig, ctrl_rig, mapping_dict):
    print("=== 🚀 APPLICATION (helpers de joint + STRETCH_TO permanent) ===")
    n_h = clear_helpers()
    if n_h:
        print(f"   🧹 {n_h} anciens empties-joints supprimés.")

    root = ctrl_rig.pose.bones.get(MASTER_BONE_NAME)
    if root is None:
        print(f"⚠️  Os maître '{MASTER_BONE_NAME}' introuvable sur '{ctrl_rig.name}'.")
    elif BLEND_PROP not in root:
        root[BLEND_PROP] = 1.0
        ui = root.id_properties_ui(BLEND_PROP)
        ui.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, description="0 = Child  /  1 = Adult")
        print(f"   ➕ Propriété '{BLEND_PROP}' créée sur '{MASTER_BONE_NAME}'.")

    ctrl_bones = ctrl_rig.pose.bones
    n_full = n_partial = n_skip = 0

    for def_name, targets in mapping_dict.items():
        def_pb = def_rig.pose.bones.get(def_name)
        if def_pb is None:
            print(f"   ❌ Os DEF '{def_name}' absent. Ignoré.")
            n_skip += 1
            continue

        adult_name = (targets.get('Adult') or '').strip()
        child_name = (targets.get('Child') or '').strip()
        has_adult = adult_name in ctrl_bones
        has_child = child_name in ctrl_bones

        if adult_name and not has_adult:
            print(f"   ⚠️  Cible Adult '{adult_name}' introuvable (os '{def_name}').")
        if child_name and not has_child:
            print(f"   ⚠️  Cible Child '{child_name}' introuvable (os '{def_name}').")

        if has_child and has_adult:
            setup_bone_blend(def_pb, ctrl_rig, child_name, adult_name)
            n_full += 1
        elif has_child or has_adult:
            if has_child:
                setup_bone_follow_parent(def_pb, ctrl_rig, child_name, 'Child')
            else:
                setup_bone_follow_parent(def_pb, ctrl_rig, adult_name, 'Adult')
            print(f"   ➖ '{def_name}' : cible unique.")
            n_partial += 1
        else:
            print(f"   ⛔ '{def_name}' : aucune cible valide. Ignoré.")
            n_skip += 1

    print(f"✅ Setup terminée. Blend: {n_full} | Suit-parent: {n_partial} | Ignorés: {n_skip}")
