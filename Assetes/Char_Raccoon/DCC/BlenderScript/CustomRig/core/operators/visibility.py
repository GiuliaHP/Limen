import bpy
from bpy.props import StringProperty

class ARMATURE_OT_toggle_skeleton_raccoon(bpy.types.Operator):
    bl_idname = "armature.toggle_skeleton_raccoon"
    bl_label = "Toggle Skeleton"
    bl_options = {'UNDO'}
    
    skeleton_type: StringProperty(default="Adult")
    
    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE': return {'CANCELLED'}
        
        armature = obj.data
        
        # 1. On enregistre l'état pour l'interface
        armature["active_skeleton"] = self.skeleton_type
        
        # 2. On parcourt les os en mode POSE (Essentiel pour Blender 5.0+)
        for p_bone in obj.pose.bones:
            hide_bone = None
            
            # Détermine si l'os doit être caché
            if "Adult" in p_bone.name:
                hide_bone = (self.skeleton_type != "Adult")
            elif "Child" in p_bone.name:
                hide_bone = (self.skeleton_type != "Child")
                
            # Applique la visibilité et gère la sélection (Mimique la touche 'H')
            if hide_bone is not None:
                # -- GESTION DE LA VISIBILITÉ --
                # Blender 5.0+ (Stocké sur le PoseBone)
                if hasattr(p_bone, "hide"):
                    p_bone.hide = hide_bone
                # Blender 4.x (Et pour le mode Edit de Blender 5.0+)
                if hasattr(p_bone.bone, "hide"):
                    p_bone.bone.hide = hide_bone
                
                # -- GESTION DE LA SÉLECTION --
                # IMPORTANT : Un os caché ne doit plus être sélectionné
                if hide_bone:
                    # Blender 5.0+ (Sélection indépendante sur le PoseBone)
                    if hasattr(p_bone, "select"):
                        p_bone.select = False
                    # Blender 4.x (Sélection partagée sur le Data Bone)
                    if hasattr(p_bone.bone, "select"):
                        p_bone.bone.select = False
                        p_bone.bone.select_head = False
                        p_bone.bone.select_tail = False
        
        # 3. L'électrochoc pour forcer Blender à rafraîchir la vue 3D
        armature.update_tag()
        context.view_layer.update()
        
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
                
        return {'FINISHED'}

classes = (ARMATURE_OT_toggle_skeleton_raccoon,)

def register():
    for cls in classes:
        if hasattr(bpy.types, cls.__name__):
            try: bpy.utils.unregister_class(getattr(bpy.types, cls.__name__))
            except Exception: pass
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        try: bpy.utils.unregister_class(cls)
        except Exception: pass