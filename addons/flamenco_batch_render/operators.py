import bpy
import json
import webbrowser
from pathlib import Path

# Store original materials
_original_materials = {}


def update_object_display(obj):
    """Update object material preview for marking"""
    global _original_materials
    
    if obj.type != 'MESH':
        return
    
    if obj.batch_render_type == 'FRONT':
        # Maak ROOD material
        if 'batch_front_preview' not in bpy.data.materials:
            mat = bpy.data.materials.new('batch_front_preview')
            mat.use_nodes = True
            mat.diffuse_color = (1.0, 0.2, 0.2, 1.0)  # Rood
            mat.metallic = 0.0
            mat.roughness = 0.5
        
        mat = bpy.data.materials['batch_front_preview']
        
        # Store originals
        key = f"{obj.name}_{id(obj)}"
        if key not in _original_materials:
            _original_materials[key] = list(obj.data.materials)
        
        # Apply red material
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        
    elif obj.batch_render_type == 'BACK':
        # Maak BLAUW material
        if 'batch_back_preview' not in bpy.data.materials:
            mat = bpy.data.materials.new('batch_back_preview')
            mat.use_nodes = True
            mat.diffuse_color = (0.2, 0.5, 1.0, 1.0)  # Blauw
            mat.metallic = 0.0
            mat.roughness = 0.5
        
        mat = bpy.data.materials['batch_back_preview']
        
        # Store originals
        key = f"{obj.name}_{id(obj)}"
        if key not in _original_materials:
            _original_materials[key] = list(obj.data.materials)
        
        # Apply blue material
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        
    else:
        # Restore originals
        key = f"{obj.name}_{id(obj)}"
        if key in _original_materials:
            obj.data.materials.clear()
            for mat in _original_materials[key]:
                obj.data.materials.append(mat)



class MarkObjectFront(bpy.types.Operator):
    """Mark selected object for front color rendering"""
    bl_idname = "wm.mark_object_front"
    bl_label = "Mark as Front"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        obj = context.active_object
        obj.batch_render_type = 'FRONT'
        update_object_display(obj)
        self.report({'INFO'}, f"'{obj.name}' marked as FRONT (Red)")
        return {'FINISHED'}


class MarkObjectBack(bpy.types.Operator):
    """Mark selected object for back color rendering"""
    bl_idname = "wm.mark_object_back"
    bl_label = "Mark as Back"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        obj = context.active_object
        obj.batch_render_type = 'BACK'
        update_object_display(obj)
        self.report({'INFO'}, f"'{obj.name}' marked as BACK (Blue)")
        return {'FINISHED'}


class UnmarkObject(bpy.types.Operator):
    """Unmark the selected object"""
    bl_idname = "wm.unmark_object"
    bl_label = "Unmark"
    bl_options = {'REGISTER', 'UNDO'}
    
    object_name: bpy.props.StringProperty()
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        if self.object_name:
            obj = context.scene.objects.get(self.object_name)
            if obj:
                obj.batch_render_type = 'NONE'
                update_object_display(obj)
                self.report({'INFO'}, f"'{obj.name}' unmarked")
        else:
            obj = context.active_object
            obj.batch_render_type = 'NONE'
            update_object_display(obj)
            self.report({'INFO'}, f"'{obj.name}' unmarked")
        
        return {'FINISHED'}


class ClearAllMarks(bpy.types.Operator):
    """Clear all marks in scene"""
    bl_idname = "wm.clear_all_marks"
    bl_label = "Clear All Marks"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        count = 0
        for obj in context.scene.objects:
            if obj.batch_render_type != 'NONE':
                obj.batch_render_type = 'NONE'
                update_object_display(obj)
                count += 1
        
        self.report({'INFO'}, f"Cleared {count} marks")
        return {'FINISHED'}


# ✅ NIEUW (mapping wordt gebouwd!)
class SubmitToFlamenco(bpy.types.Operator):
    """Submit marked objects to Flamenco"""
    bl_idname = "wm.batch_marks_to_flamenco"
    bl_label = "Submit to Flamenco"
    
    def execute(self, context):
        scene = context.scene
        
        # Valideer inputs
        front_objs = [obj for obj in scene.objects if obj.batch_render_type == 'FRONT']
        back_objs = [obj for obj in scene.objects if obj.batch_render_type == 'BACK']
        
        if not front_objs and not back_objs:
            self.report({'ERROR'}, "No objects marked as Front or Back")
            return {'CANCELLED'}
        
        if not scene.batch_material_library:
            self.report({'ERROR'}, "Material library not set")
            return {'CANCELLED'}
        
        if not scene.batch_output_directory:
            self.report({'ERROR'}, "Output directory not set")
            return {'CANCELLED'}
        
        if not bpy.data.is_saved:
            self.report({'ERROR'}, "Please save your Blender file first")
            return {'CANCELLED'}
        
        # ✅ BUILD MAPPING (dit was weg!)
        mapping = {}
        
        for obj in front_objs:
            mapping[obj.name] = scene.batch_front_material
            print(f"[DEBUG] Mapped {obj.name} → {scene.batch_front_material}")
        
        for obj in back_objs:
            mapping[obj.name] = scene.batch_back_material
            print(f"[DEBUG] Mapped {obj.name} → {scene.batch_back_material}")
        
        print(f"[DEBUG] Final mapping: {mapping}")
        
        if not mapping:
            self.report({'ERROR'}, "Mapping is empty")
            return {'CANCELLED'}
        
        # Get blend file path
        blend_file = bpy.data.filepath
        material_library = scene.batch_material_library
        
        # Create output path
        output_dir = Path(scene.batch_output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create job
        task = {
            "name": "render_marked_objects",
            "type": "material_batch",
            "settings": {
                "blend_file": str(Path(blend_file).resolve()),
                "material_library": str(Path(material_library).resolve()),
                "object_material_mapping": json.dumps(mapping),  # ✅ MAPPING HIER!
                "output_directory": str(output_dir.resolve()),
            }
        }
        
        job = {
            "name": f"Batch Render - {len(front_objs)} Front, {len(back_objs)} Back",
            "job_type": "material_batch",
            "tasks": [task]
        }
        
        # Submit to Flamenco
        try:
            import requests
            
            manager_url = scene.flamenco_manager_url.rstrip('/')
            response = requests.post(
                f"{manager_url}/api/v3/jobs",
                json=job,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 201:
                job_data = response.json()
                job_id = job_data.get('id', 'unknown')
                job_url = f"{manager_url}/ui/jobs/{job_id}"
                
                print(f"\n✓ Job submitted successfully!")
                print(f"  Job ID: {job_id}")
                print(f"  Front objects: {len(front_objs)}")
                print(f"  Back objects: {len(back_objs)}")
                print(f"  Mapping: {mapping}\n")
                
                self.report({'INFO'}, f"Job {job_id} submitted ({len(front_objs)}F + {len(back_objs)}B)")
                
                if scene.batch_open_ui_after_submit:
                    import webbrowser
                    webbrowser.open(job_url)
                
                return {'FINISHED'}
            else:
                error_msg = response.text[:200]
                print(f"✗ Job submission failed: {response.status_code}")
                print(f"  Response: {error_msg}")
                self.report({'ERROR'}, f"Failed ({response.status_code}): {error_msg}")
                return {'CANCELLED'}
        
        except requests.exceptions.ConnectionError:
            msg = f"Cannot connect to Flamenco at {manager_url}"
            print(f"✗ {msg}")
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        except ImportError:
            self.report({'ERROR'}, "requests library not installed")
            return {'CANCELLED'}
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}



def add_object_context_menu(self, context):
    """Add to right-click context menu"""
    layout = self.layout
    layout.separator()
    
    if context.active_object:
        obj = context.active_object
        
        layout.label(text="Batch Render", icon='RENDER_RESULT')
        
        if obj.batch_render_type == 'FRONT':
            layout.operator("wm.mark_object_front", text="Front (Red)", icon='CHECKMARK', depress=True)
        else:
            layout.operator("wm.mark_object_front", text="Mark as Front (Red)")

        if obj.batch_render_type == 'BACK':
            layout.operator("wm.mark_object_back", text="Back (Blue)", icon='CHECKMARK', depress=True)
        else:
            layout.operator("wm.mark_object_back", text="Mark as Back (Blue)")

        
        if obj.batch_render_type != 'NONE':
            layout.operator("wm.unmark_object", text="Unmark")


def register():
    """Register operators"""
    bpy.utils.register_class(MarkObjectFront)
    bpy.utils.register_class(MarkObjectBack)
    bpy.utils.register_class(UnmarkObject)
    bpy.utils.register_class(ClearAllMarks)
    bpy.utils.register_class(SubmitToFlamenco)


def unregister():
    """Unregister operators"""
    bpy.utils.unregister_class(MarkObjectFront)
    bpy.utils.unregister_class(MarkObjectBack)
    bpy.utils.unregister_class(UnmarkObject)
    bpy.utils.unregister_class(ClearAllMarks)
    bpy.utils.unregister_class(SubmitToFlamenco)
