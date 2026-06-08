import bpy

# --- CONFIG ---
MASTER_BONE_NAME = "root"          # Os porteur de la propriété de blend (sur le ctrl_rig)
BLEND_PROP       = "morph_blend"   # 0.0 = Child  /  1.0 = Adult  (cf. UI main_panel.py)

# Facteurs de stretch par défaut (surchargeables par os dans le MAPPING_DICT)
DEFAULT_FACTOR_Y  = 1.0    # 1 = stretch en longueur complet, 0 = pas de stretch (translation seule)
DEFAULT_FACTOR_XZ = 0.0    # 0 = aucun changement d'épaisseur, 1 = préservation de volume complète


# --- DRIVERS ---

def _config_driver(fcurve, ctrl_rig, expression):
    """Configure un fcurve en driver SCRIPTED lisant root['morph_blend'] sous le nom 'blend'."""
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
    """Branche l'influence d'une contrainte sur morph_blend."""
    return _config_driver(con.driver_add("influence"), ctrl_rig, expression)


def drive_scale_component(def_rig, bone_name, index, ctrl_rig, expression):
    """Branche une composante de scale (0=X, 1=Y, 2=Z) de l'os DEF sur morph_blend."""
    path = f'pose.bones["{bone_name}"].scale'
    return _config_driver(def_rig.driver_add(path, index), ctrl_rig, expression)


# --- BUILDERS DE CONTRAINTES ---

def add_copy_location(pose_bone, ctrl_rig, subtarget, name):
    """Position absolue (World) : tête du DEF sur celle de la cible -> morph des proportions."""
    con = pose_bone.constraints.new('COPY_LOCATION')
    con.name         = name
    con.target       = ctrl_rig
    con.subtarget    = subtarget
    con.target_space = 'WORLD'
    con.owner_space  = 'WORLD'
    return con


def add_copy_rotation(pose_bone, ctrl_rig, subtarget, name):
    """Rotation absolue (World) : robuste aux rest poses différents."""
    con = pose_bone.constraints.new('COPY_ROTATION')
    con.name         = name
    con.target       = ctrl_rig
    con.subtarget    = subtarget
    con.target_space = 'WORLD'
    con.owner_space  = 'WORLD'
    return con


def add_copy_scale_offset(pose_bone, ctrl_rig, subtarget, name):
    """Scale ADDITIVE (use_offset) : la scale animée de la cible se multiplie sur celle du DEF."""
    con = pose_bone.constraints.new('COPY_SCALE')
    con.name         = name
    con.target       = ctrl_rig
    con.subtarget    = subtarget
    con.use_offset   = True
    con.target_space = 'LOCAL'
    con.owner_space  = 'LOCAL'
    return con


# --- COUCHES DE SETUP PAR OS ---

def add_stretch_drivers(def_rig, def_pb, ctrl_rig, child_name, adult_name, factor_y, factor_xz):
    """Étirement le long de l'os (Y) drivé par le ratio de longueur Adult/Child.
    Child == DEF en rest pose -> à blend=0 scale_y=1 (longueur Child), à blend=1 scale_y=ratio."""
    if factor_y == 0.0:
        return

    child_len = ctrl_rig.pose.bones[child_name].bone.length
    adult_len = ctrl_rig.pose.bones[adult_name].bone.length
    if child_len <= 1e-6:
        print(f"   ⚠️  Longueur Child nulle pour '{def_pb.name}', stretch Y ignoré.")
        return

    ratio = adult_len / child_len
    if abs(ratio - 1.0) <= 1e-6:
        return  # même longueur -> rien à étirer

    # scale_y = 1 + fy * (ratio - 1) * blend
    sy_expr = f"1.0 + {factor_y} * ({ratio} - 1.0) * blend"
    drive_scale_component(def_rig, def_pb.name, 1, ctrl_rig, sy_expr)

    # Compensation de volume optionnelle en X/Z : scale_xz = 1 + fxz * (1/sqrt(scale_y) - 1)
    if factor_xz != 0.0:
        sy_inner = f"(1.0 + {factor_y} * ({ratio} - 1.0) * blend)"
        sxz_expr = f"1.0 + {factor_xz} * (1.0 / sqrt(max({sy_inner}, 1e-6)) - 1.0)"
        drive_scale_component(def_rig, def_pb.name, 0, ctrl_rig, sxz_expr)
        drive_scale_component(def_rig, def_pb.name, 2, ctrl_rig, sxz_expr)


def setup_bone_blend(def_rig, def_pb, ctrl_rig, child_name, adult_name, factor_y, factor_xz):
    """Loc/Rot absolus blendés par empilement (1 driver) + scale additive + stretch Y par ratio."""
    # --- LOCATION : Child = base, Adult = mix drivé ---
    add_copy_location(def_pb, ctrl_rig, child_name, "RT_Loc_Child")
    c = add_copy_location(def_pb, ctrl_rig, adult_name, "RT_Loc_Adult")
    drive_influence(c, ctrl_rig, "blend")

    # --- ROTATION : Child = base, Adult = mix drivé ---
    add_copy_rotation(def_pb, ctrl_rig, child_name, "RT_Rot_Child")
    c = add_copy_rotation(def_pb, ctrl_rig, adult_name, "RT_Rot_Adult")
    drive_influence(c, ctrl_rig, "blend")

    # --- SCALE ADDITIVE : blend sur Child ET Adult ---
    c = add_copy_scale_offset(def_pb, ctrl_rig, child_name, "RT_Scale_Child")
    drive_influence(c, ctrl_rig, "1.0 - blend")
    c = add_copy_scale_offset(def_pb, ctrl_rig, adult_name, "RT_Scale_Adult")
    drive_influence(c, ctrl_rig, "blend")

    # --- STRETCH Y (longueur) + compensation X/Z optionnelle ---
    add_stretch_drivers(def_rig, def_pb, ctrl_rig, child_name, adult_name, factor_y, factor_xz)


def setup_bone_follow_parent(def_pb, ctrl_rig, target_name, present_side):
    """Cible manquante d'un côté : l'os suit la cible présente, et FOND vers le parentage
    de la hiérarchie DEF quand on va vers le côté manquant (suit bêtement son parent)."""
    # côté Child présent -> influence forte à blend=0, nulle à blend=1 (= suit le parent côté Adult)
    expr = "1.0 - blend" if present_side == 'Child' else "blend"
    c = add_copy_location(def_pb, ctrl_rig, target_name, "RT_Loc")
    drive_influence(c, ctrl_rig, expr)
    c = add_copy_rotation(def_pb, ctrl_rig, target_name, "RT_Rot")
    drive_influence(c, ctrl_rig, expr)
    c = add_copy_scale_offset(def_pb, ctrl_rig, target_name, "RT_Scale")
    drive_influence(c, ctrl_rig, expr)


def apply_constraints_from_dict(def_rig, ctrl_rig, mapping_dict):
    print("=== 🚀 APPLICATION DES CONTRAINTES (Loc/Rot World + scale additive + stretch Y) ===")

    root = ctrl_rig.pose.bones.get(MASTER_BONE_NAME)
    if root is None:
        print(f"⚠️  Os maître '{MASTER_BONE_NAME}' introuvable sur '{ctrl_rig.name}' : driver impossible.")
    elif BLEND_PROP not in root:
        root[BLEND_PROP] = 1.0  # défaut = Adult
        ui = root.id_properties_ui(BLEND_PROP)
        ui.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, description="0 = Child  /  1 = Adult")
        print(f"   ➕ Propriété '{BLEND_PROP}' créée sur '{MASTER_BONE_NAME}'.")

    ctrl_bones = ctrl_rig.pose.bones
    n_full = n_partial = n_skip = 0

    for def_name, targets in mapping_dict.items():
        def_pb = def_rig.pose.bones.get(def_name)
        if def_pb is None:
            print(f"   ❌ Os DEF '{def_name}' absent de '{def_rig.name}'. Ignoré.")
            n_skip += 1
            continue

        adult_name = (targets.get('Adult') or '').strip()
        child_name = (targets.get('Child') or '').strip()
        factor_y   = targets.get('scale_y', DEFAULT_FACTOR_Y)
        factor_xz  = targets.get('scale_xz', DEFAULT_FACTOR_XZ)

        has_adult = adult_name in ctrl_bones
        has_child = child_name in ctrl_bones

        # Log des cibles renseignées mais introuvables (vs. volontairement vides)
        if adult_name and not has_adult:
            print(f"   ⚠️  Cible Adult '{adult_name}' introuvable (os DEF '{def_name}').")
        if child_name and not has_child:
            print(f"   ⚠️  Cible Child '{child_name}' introuvable (os DEF '{def_name}').")

        # --- CAS 1 : blend complet Child <-> Adult ---
        if has_child and has_adult:
            setup_bone_blend(def_rig, def_pb, ctrl_rig, child_name, adult_name, factor_y, factor_xz)
            n_full += 1

        # --- CAS 2 : une seule cible -> suit la cible présente, fond vers le parent à l'autre extrême ---
        elif has_child or has_adult:
            if has_child:
                setup_bone_follow_parent(def_pb, ctrl_rig, child_name, 'Child')
            else:
                setup_bone_follow_parent(def_pb, ctrl_rig, adult_name, 'Adult')
            print(f"   ➖ '{def_name}' : cible unique, suit le parent à l'extrême manquant.")
            n_partial += 1

        # --- CAS 3 : aucune cible valide ---
        else:
            print(f"   ⛔ '{def_name}' : aucune cible valide. Ignoré.")
            n_skip += 1

    print(f"✅ Setup terminée. Blend complet: {n_full} | Suit-parent: {n_partial} | Ignorés: {n_skip}")
