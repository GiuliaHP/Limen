import bpy

def clear_rig_data(obj_name="Def"):
    obj = bpy.data.objects.get(obj_name)
    if not obj or obj.type != 'ARMATURE':
        print(f"❌ Objet '{obj_name}' non trouvé.")
        return

    print(f"=== 🧹 NETTOYAGE TOTAL DE : {obj_name} ===")
    
    count_constraints = 0
    count_drivers = 0

    for pb in obj.pose.bones:
        # Suppression des contraintes
        for i in range(len(pb.constraints) - 1, -1, -1):
            pb.constraints.remove(pb.constraints[i])
            count_constraints += 1

    # Suppression des drivers
    if obj.animation_data and obj.animation_data.drivers:
        drivers_to_remove = [f for f in obj.animation_data.drivers if "pose.bones" in f.data_path]
        for fcurve in drivers_to_remove:
            obj.driver_remove(fcurve.data_path, fcurve.array_index)
            count_drivers += 1

    print(f"✅ Nettoyage : {count_constraints} contraintes et {count_drivers} drivers supprimés.")