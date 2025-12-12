bl_info = {
    "name": "Octane Studio Creative Lighting",
    "author": "TrevisCloud",
    "version": (1, 3, 2),
    "blender": (4, 5, 2),
    "location": "View3D > N-Panel > Octane Studio",
    "description": "Professional Lighting, Atmosphere, Bokeh, and Environment Tools.",
    "category": "Lighting",
}

import bpy
import math
import random
from mathutils import Vector, Color

# ------------------------------------------------------------------------
#   CONSTANTS & UTILS
# ------------------------------------------------------------------------

COLLECTION_NAME = "Octane_Studio_Setup"
BOKEH_COLLECTION_NAME = "Octane_Bokeh_Elements"

OFFSETS = {
    'LOW_KEY': {'KEY': Vector((-2, -2, 2)), 'FILL': Vector((2, -3, 1)), 'RIM': Vector((1, 2, 2))},
    'BUTTERFLY': {'KEY': Vector((0, -2, 2.5)), 'FILL': Vector((0, -2, 0.5)), 'RIM': Vector((-1.5, 1.5, 1.5))},
    'SPLIT': {'KEY': Vector((-2.5, 0, 0)), 'FILL': Vector((2.5, -1, 1)), 'RIM': Vector((0, 2, 2))}
}

def get_or_create_collection(name=COLLECTION_NAME):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

def get_lighting_target(context):
    props = context.scene.octane_studio_props
    if props.target_object: return props.target_object
    if "Studio_Target_Null" in bpy.data.objects: return bpy.data.objects["Studio_Target_Null"]
    
    obj = context.active_object
    if not obj or "Studio_" in obj.name or obj.type == 'LIGHT' or obj.type == 'CAMERA':
        if bpy.ops.object.select_all.poll(): bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,1.6))
        obj = context.active_object
        obj.name = "Studio_Target_Null"
        col = get_or_create_collection()
        if obj.users_collection:
             for c in obj.users_collection: c.objects.unlink(obj)
        col.objects.link(obj)
    return obj

def get_camera_focus_target(context):
    props = context.scene.octane_studio_props
    if props.camera_target: return props.camera_target
    return get_lighting_target(context)

def get_portrait_cam():
    return bpy.data.objects.get("Portrait_Cam")

def find_light_object(role):
    col = bpy.data.collections.get(COLLECTION_NAME)
    if not col: return None
    for obj in col.objects:
        if obj.get("studio_role") == role: return obj
    return None

# ------------------------------------------------------------------------
#   LIVE UPDATES
# ------------------------------------------------------------------------

def update_light_node(context, role, settings):
    obj = find_light_object(role)
    if not obj: return

    is_hidden = not settings.enabled
    obj.hide_viewport = is_hidden
    obj.hide_render = is_hidden

    if hasattr(obj, 'octane') and hasattr(obj.octane, 'camera_visibility'):
        obj.octane.camera_visibility = settings.visible_in_camera

    if obj.type == 'LIGHT' and obj.data.type == 'AREA':
        obj.data.size = settings.size
        obj.data.size_y = settings.size

    target = get_lighting_target(context)
    props = context.scene.octane_studio_props
    if target and "studio_style" in obj:
        style = obj["studio_style"]
        if style in OFFSETS and role in OFFSETS[style]:
            base_vec = OFFSETS[style][role].copy()
            if props.group_rotation != 0:
                cos_a = math.cos(props.group_rotation)
                sin_a = math.sin(props.group_rotation)
                x = base_vec.x * cos_a - base_vec.y * sin_a
                y = base_vec.x * sin_a + base_vec.y * cos_a
                base_vec.x = x
                base_vec.y = y
            position = base_vec * settings.distance
            position.z += settings.height
            obj.location = target.location + position

    if not obj.data.use_nodes: return
    nt = obj.data.node_tree
    
    tex_emit = None
    for node in nt.nodes:
        if node.bl_idname == 'OctaneTextureEmission':
            tex_emit = node; break
            
    if tex_emit:
        if 'Power' in tex_emit.inputs: tex_emit.inputs['Power'].default_value = settings.power
        elif len(tex_emit.inputs) > 1: tex_emit.inputs[1].default_value = settings.power

        if len(tex_emit.inputs) > 0 and tex_emit.inputs[0].is_linked:
            source_node = tex_emit.inputs[0].links[0].from_node
            if source_node.bl_idname == 'OctaneRGBColor':
                try: source_node.a_value = Color(settings.color)
                except: pass

def update_all_lights(self, context):
    if not context or not context.scene: return
    try:
        props = context.scene.octane_studio_props
        update_light_node(context, 'KEY', props.key_light)
        update_light_node(context, 'FILL', props.fill_light)
        update_light_node(context, 'RIM', props.rim_light)
    except: pass

def update_atmosphere(self, context):
    """Updates the fog density/color if it exists."""
    col = bpy.data.collections.get(COLLECTION_NAME)
    if not col: return
    atmos = col.objects.get("Octane_Atmosphere")
    if not atmos: return
    
    mat = atmos.active_material
    if not mat or not mat.use_nodes: return
    
    vol_node = None
    for n in mat.node_tree.nodes:
        if n.bl_idname == 'OctaneVolumeMedium':
            vol_node = n
            break
            
    if vol_node:
        props = context.scene.octane_studio_props.creative
        if 'Density' in vol_node.inputs:
            vol_node.inputs['Density'].default_value = props.atmos_density
        elif len(vol_node.inputs) > 0:
             vol_node.inputs[0].default_value = props.atmos_density

def update_backdrop_material(self, context):
    col = bpy.data.collections.get(COLLECTION_NAME)
    if not col: return
    bd_obj = None
    for obj in col.objects:
        if obj.name.startswith("Backdrop"): bd_obj = obj; break
    if not bd_obj or not bd_obj.active_material: return
    
    mat = bd_obj.active_material
    if not mat.use_nodes: return
    
    diff_node = None
    rgb_node = None
    for node in mat.node_tree.nodes:
        if node.bl_idname == 'OctaneDiffuseMaterial': diff_node = node
        if node.bl_idname == 'OctaneRGBColor': rgb_node = node
            
    props = context.scene.octane_studio_props
    if rgb_node:
        try: rgb_node.a_value = Color(props.backdrop_color)
        except: pass
    if diff_node:
        if 'Roughness' in diff_node.inputs: diff_node.inputs['Roughness'].default_value = props.backdrop_roughness
        elif len(diff_node.inputs) > 4: diff_node.inputs[4].default_value = props.backdrop_roughness

def update_camera_transform(self, context):
    cam_obj = get_portrait_cam()
    props = context.scene.octane_studio_props
    if not cam_obj: return
    target = get_camera_focus_target(context)
    if not target: return

    if props.camera_locked:
        dist, angle, height = props.camera_dist, props.camera_orbit, props.camera_height
        v_off = props.camera_vertical_offset
        x = target.location.x + (dist * math.sin(angle))
        y = target.location.y - (dist * math.cos(angle))
        z = target.location.z + height + v_off
        cam_obj.location = (x, y, z)

        const = None
        for c in cam_obj.constraints:
            if c.type == 'TRACK_TO': const = c; break
        if not const: const = cam_obj.constraints.new('TRACK_TO')

        helper = bpy.data.objects.get("Camera_Look_Point")
        if not helper:
            helper = bpy.data.objects.new("Camera_Look_Point", None)
            get_or_create_collection().objects.link(helper)
        helper.location = (target.location.x, target.location.y, target.location.z + v_off)
        const.target = helper
        const.track_axis, const.up_axis = 'TRACK_NEGATIVE_Z', 'UP_Y'
        const.mute = False
        
        # Stability: Force dependency graph update to prevent lag/glitching
        if context.view_layer: context.view_layer.update()
        
    else:
        for c in cam_obj.constraints:
            if c.type == 'TRACK_TO': c.mute = True

    # Camera Display & DOF Settings
    cam_data = cam_obj.data

    # Show/Hide Limits (viewport frustum display)
    cam_data.show_limits = props.camera_show_limits

    # Enable DOF and handle autofocus toggle
    cam_data.dof.use_dof = True
    if props.camera_autofocus:
        # Autofocus on target object
        target = get_camera_focus_target(context)
        cam_data.dof.focus_object = target
    else:
        # Manual focus distance
        cam_data.dof.focus_object = None
        cam_data.dof.focus_distance = props.camera_focus_distance 

# ------------------------------------------------------------------------
#   DATA CLASSES
# ------------------------------------------------------------------------

class LightSettings(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="Enable", default=True, update=update_all_lights)
    expanded: bpy.props.BoolProperty(name="Expanded", default=True)
    power: bpy.props.FloatProperty(name="Power", default=10.0, min=0.0, soft_max=500.0, update=update_all_lights)
    color: bpy.props.FloatVectorProperty(name="RGB", subtype='COLOR', default=(1,1,1), min=0.0, max=1.0, update=update_all_lights)
    distance: bpy.props.FloatProperty(name="Distance", default=1.0, min=0.1, max=10.0, update=update_all_lights)
    height: bpy.props.FloatProperty(name="Height", default=0.0, min=-5.0, max=5.0, update=update_all_lights)
    size: bpy.props.FloatProperty(name="Size", default=1.0, min=0.1, max=10.0, update=update_all_lights)
    visible_in_camera: bpy.props.BoolProperty(name="Visible in Camera", default=False, update=update_all_lights)

class CreativeSettings(bpy.types.PropertyGroup):
    # Atmosphere
    atmos_density: bpy.props.FloatProperty(name="Density", default=0.05, min=0.0, max=1.0, step=0.5, precision=3, update=update_atmosphere)
    
    # Bokeh
    bokeh_count: bpy.props.IntProperty(name="Count", default=20, min=1, max=100)
    bokeh_size_min: bpy.props.FloatProperty(name="Min Size", default=0.1)
    bokeh_size_max: bpy.props.FloatProperty(name="Max Size", default=0.5)
    bokeh_dist: bpy.props.FloatProperty(name="Distance Behind", default=4.0)
    bokeh_spread: bpy.props.FloatProperty(name="Spread Width", default=5.0)
    bokeh_power: bpy.props.FloatProperty(name="Emission Power", default=50.0)
    bokeh_base_color: bpy.props.FloatVectorProperty(name="Base Color", subtype='COLOR', default=(1, 0.5, 0.2))

class OctaneStudioProperties(bpy.types.PropertyGroup):
    ui_tab: bpy.props.EnumProperty(
        items=[('CREATE', "Create", ""), ('CONTROL', "Control", ""), ('CREATIVE', "Creative", ""), ('TOOLS', "Tools", "")],
        default='CREATE'
    )
    setup_type: bpy.props.EnumProperty(items=[('LOW_KEY', "Low Key", ""), ('BUTTERFLY', "Butterfly", ""), ('SPLIT', "Side/Split", "")], default='LOW_KEY')
    target_object: bpy.props.PointerProperty(type=bpy.types.Object, name="Light Target")
    use_fill: bpy.props.BoolProperty(name="Fill Light", default=True)
    use_rim: bpy.props.BoolProperty(name="Rim Light", default=True)
    group_rotation: bpy.props.FloatProperty(name="Group Rotation", default=0.0, min=-math.pi, max=math.pi, subtype='ANGLE', update=update_all_lights)

    key_light: bpy.props.PointerProperty(type=LightSettings)
    fill_light: bpy.props.PointerProperty(type=LightSettings)
    rim_light: bpy.props.PointerProperty(type=LightSettings)
    
    creative: bpy.props.PointerProperty(type=CreativeSettings)

    camera_target: bpy.props.PointerProperty(type=bpy.types.Object, name="Focus Target", update=update_camera_transform)
    camera_locked: bpy.props.BoolProperty(name="Lock to Target", default=True, update=update_camera_transform)
    
    # Updated Sensitivity Settings (Step=1 means 0.01 in UI usually, Precision=3 for better float display)
    camera_dist: bpy.props.FloatProperty(name="Distance", default=5.0, min=0.5, max=20.0, step=1, precision=3, update=update_camera_transform)
    camera_height: bpy.props.FloatProperty(name="Height", default=0.0, min=-5.0, max=5.0, step=1, precision=3, update=update_camera_transform)
    camera_orbit: bpy.props.FloatProperty(name="Orbit", default=0.0, min=-math.pi, max=math.pi, subtype='ANGLE', update=update_camera_transform)
    camera_vertical_offset: bpy.props.FloatProperty(name="Tripod Height", default=0.0, min=-5.0, max=5.0, step=1, precision=3, update=update_camera_transform)

    # Camera Display & DOF
    camera_show_limits: bpy.props.BoolProperty(name="Show Limits", default=True, update=update_camera_transform, description="Show camera frustum limits in viewport")
    camera_autofocus: bpy.props.BoolProperty(name="Autofocus", default=False, update=update_camera_transform, description="Enable autofocus (focus on target object)")
    camera_focus_distance: bpy.props.FloatProperty(name="Focus Distance", default=5.0, min=0.1, max=100.0, step=10, precision=2, update=update_camera_transform, description="Manual focus distance for DOF")
    
    backdrop_color: bpy.props.FloatVectorProperty(name="Color", subtype='COLOR', default=(0.1, 0.1, 0.1), update=update_backdrop_material)
    backdrop_roughness: bpy.props.FloatProperty(name="Roughness", default=0.5, update=update_backdrop_material)

# ------------------------------------------------------------------------
#   OPERATORS
# ------------------------------------------------------------------------

class OCTANESTUDIO_OT_AddAtmosphere(bpy.types.Operator):
    bl_idname = "octanestudio.add_atmosphere"
    bl_label = "Add Atmosphere"
    
    def execute(self, context):
        col = get_or_create_collection()
        if col.objects.get("Octane_Atmosphere"): return {'FINISHED'} 
            
        bpy.ops.mesh.primitive_cube_add(size=20, location=(0,0,2))
        obj = context.active_object
        obj.name = "Octane_Atmosphere"
        obj.display_type = 'WIRE'
        
        if obj.users_collection:
            for c in obj.users_collection: c.objects.unlink(obj)
        col.objects.link(obj)
        
        mat = bpy.data.materials.new("Octane_Fog_Mat")
        mat.use_nodes = True
        obj.active_material = mat
        nt = mat.node_tree; nt.nodes.clear()
        
        out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (400,0)
        uni = nt.nodes.new('OctaneUniversalMaterial'); uni.location = (200,0)
        nt.links.new(uni.outputs[0], out.inputs['Surface'])
        
        trans_col = nt.nodes.new('OctaneRGBColor')
        trans_col.a_value = Color((1,1,1))
        nt.links.new(trans_col.outputs[0], uni.inputs['Transmission'])
        
        albedo_col = nt.nodes.new('OctaneRGBColor')
        albedo_col.a_value = Color((0,0,0))
        nt.links.new(albedo_col.outputs[0], uni.inputs['Albedo'])
        
        vol = nt.nodes.new('OctaneVolumeMedium') 
        if 'Density' in vol.inputs:
            vol.inputs['Density'].default_value = context.scene.octane_studio_props.creative.atmos_density
        elif len(vol.inputs) > 0:
            vol.inputs[0].default_value = context.scene.octane_studio_props.creative.atmos_density
            
        if 'Medium' in uni.inputs: nt.links.new(vol.outputs[0], uni.inputs['Medium'])
        return {'FINISHED'}

class OCTANESTUDIO_OT_CreateBokeh(bpy.types.Operator):
    bl_idname = "octanestudio.create_bokeh"
    bl_label = "Generate Bokeh"
    def execute(self, context):
        props = context.scene.octane_studio_props.creative
        col = get_or_create_collection(BOKEH_COLLECTION_NAME)
        for obj in list(col.objects): bpy.data.objects.remove(obj, do_unlink=True)
        target = get_lighting_target(context)
        
        mat = bpy.data.materials.new("Bokeh_Light_Mat")
        mat.use_nodes = True
        nt = mat.node_tree; nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        diff = nt.nodes.new('OctaneDiffuseMaterial')
        emit = nt.nodes.new('OctaneTextureEmission')
        rgb = nt.nodes.new('OctaneRGBColor')
        rgb.a_value = Color(props.bokeh_base_color)
        emit.inputs['Power'].default_value = props.bokeh_power
        nt.links.new(rgb.outputs[0], emit.inputs[0])
        
        emit_socket = None
        for s in diff.inputs:
            if s.identifier == 'Emission': emit_socket = s; break
        if not emit_socket and len(diff.inputs) > 17: emit_socket = diff.inputs[17]
        if emit_socket: nt.links.new(emit.outputs[0], emit_socket)
        nt.links.new(diff.outputs[0], out.inputs['Surface'])
        
        for i in range(props.bokeh_count):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8)
            obj = context.active_object
            x = (random.random() - 0.5) * props.bokeh_spread * 2
            y = target.location.y + props.bokeh_dist + (random.random() * 2.0)
            z = target.location.z + (random.random() - 0.5) * 3.0
            obj.location = (x, y, z)
            s = props.bokeh_size_min + random.random() * (props.bokeh_size_max - props.bokeh_size_min)
            obj.scale = (s,s,s)
            obj.active_material = mat

            # Apply smooth shading
            for poly in obj.data.polygons:
                poly.use_smooth = True

            if obj.users_collection:
                for c in obj.users_collection: c.objects.unlink(obj)
            col.objects.link(obj)
        return {'FINISHED'}

class OCTANESTUDIO_OT_StudioBlack(bpy.types.Operator):
    bl_idname = "octanestudio.studio_black"
    bl_label = "Set Studio Black"

    def execute(self, context):
        world = context.scene.world
        if not world:
            world = bpy.data.worlds.new("StudioWorld")
            context.scene.world = world
        world.use_nodes = True
        nt = world.node_tree
        
        bg = nt.nodes.new('ShaderNodeBackground')
        bg.inputs[0].default_value = (0,0,0,1)
        bg.inputs[1].default_value = 0
        
        out = nt.nodes.get('World Output')
        if not out: out = nt.nodes.new('ShaderNodeOutputWorld')
        nt.links.new(bg.outputs[0], out.inputs[0])
        return {'FINISHED'}

class OCTANESTUDIO_OT_SetAspectRatio(bpy.types.Operator):
    bl_idname = "octanestudio.set_aspect_ratio"
    bl_label = "Set Aspect Ratio"
    ratio: bpy.props.EnumProperty(items=[('SQUARE',"Square",""),('PORTRAIT',"Portrait",""),('LANDSCAPE',"Landscape",""),('CINEMATIC',"Film","")])
    def execute(self, context):
        r = context.scene.render
        if self.ratio == 'SQUARE': r.resolution_x, r.resolution_y = 1080, 1080
        elif self.ratio == 'PORTRAIT': r.resolution_x, r.resolution_y = 1080, 1350
        elif self.ratio == 'LANDSCAPE': r.resolution_x, r.resolution_y = 1920, 1080
        elif self.ratio == 'CINEMATIC': r.resolution_x, r.resolution_y = 1920, 817
        return {'FINISHED'}

class OCTANESTUDIO_OT_Generate(bpy.types.Operator):
    bl_idname = "octanestudio.generate"
    bl_label = "Create Setup"
    def execute(self, context):
        create_full_setup(context)
        context.scene.octane_studio_props.ui_tab = 'CONTROL'
        return {'FINISHED'}

class OCTANESTUDIO_OT_Clear(bpy.types.Operator):
    bl_idname = "octanestudio.clear"
    bl_label = "Clear All"
    @classmethod
    def poll(cls, context): return bpy.data.collections.get(COLLECTION_NAME) is not None
    def execute(self, context):
        # Clear main studio collection
        col = bpy.data.collections.get(COLLECTION_NAME)
        if col:
            for obj in list(col.objects): bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(col)

        # Clear bokeh collection
        bokeh_col = bpy.data.collections.get(BOKEH_COLLECTION_NAME)
        if bokeh_col:
            for obj in list(bokeh_col.objects): bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(bokeh_col)

        # Clear target null
        if "Studio_Target_Null" in bpy.data.objects:
            t = bpy.data.objects["Studio_Target_Null"]
            if t.users <= 1: bpy.data.objects.remove(t)

        # Clear camera look point helper
        if "Camera_Look_Point" in bpy.data.objects:
            helper = bpy.data.objects["Camera_Look_Point"]
            if helper.users <= 1: bpy.data.objects.remove(helper)

        return {'FINISHED'}

class OCTANESTUDIO_OT_AddCamera(bpy.types.Operator):
    bl_idname = "octanestudio.add_camera"
    bl_label = "Add Portrait Cam"
    def execute(self, context):
        if get_portrait_cam(): return {'CANCELLED'}
        target = get_camera_focus_target(context)
        if target.location.z < 0.5: target.location.z = 1.6 
        cam_data = bpy.data.cameras.new("Portrait_Cam")
        cam_data.lens = 85
        cam_obj = bpy.data.objects.new("Portrait_Cam", cam_data)
        get_or_create_collection().objects.link(cam_obj)
        props = context.scene.octane_studio_props
        props.camera_locked = True
        props.camera_dist = 3.5 
        props.camera_height = -0.4
        context.scene.camera = cam_obj
        update_camera_transform(self, context)
        return {'FINISHED'}

class OCTANESTUDIO_OT_AddBackdrop(bpy.types.Operator):
    bl_idname = "octanestudio.add_backdrop"
    bl_label = "Add Backdrop"
    def execute(self, context):
        col = get_or_create_collection()
        target = get_lighting_target(context)
        for obj in col.objects:
            if obj.name.startswith("Backdrop"): return {'CANCELLED'}
        bpy.ops.mesh.primitive_plane_add(size=10, location=(target.location.x, target.location.y+3, 0))
        bd = context.active_object
        bd.name = "Backdrop"
        bd.rotation_euler = (math.radians(90), 0, 0)
        if bd.users_collection:
            for c in bd.users_collection: c.objects.unlink(bd)
        col.objects.link(bd)
        mat = bpy.data.materials.new(name="Backdrop_Mat")
        mat.use_nodes = True
        bd.active_material = mat
        nt = mat.node_tree; nt.nodes.clear()
        out_node = nt.nodes.new('ShaderNodeOutputMaterial'); out_node.location = (400,0)
        diff_node = nt.nodes.new('OctaneDiffuseMaterial'); diff_node.location = (200,0)
        rgb_node = nt.nodes.new('OctaneRGBColor'); rgb_node.location = (0, 0)
        props = context.scene.octane_studio_props
        rgb_node.a_value = Color(props.backdrop_color)
        nt.links.new(rgb_node.outputs[0], diff_node.inputs[0])
        nt.links.new(diff_node.outputs[0], out_node.inputs['Surface'])
        return {'FINISHED'}

class OCTANESTUDIO_OT_ResetValues(bpy.types.Operator):
    bl_idname = "octanestudio.reset_values"
    bl_label = "Reset Values"
    def execute(self, context):
        p = context.scene.octane_studio_props
        p.key_light.power = 10.0; p.key_light.color = (1,1,1)
        p.fill_light.power = 10.0; p.rim_light.power = 10.0
        update_all_lights(self, context)
        return {'FINISHED'}

# ------------------------------------------------------------------------
#   MAIN CREATION
# ------------------------------------------------------------------------

def create_full_setup(context):
    props = context.scene.octane_studio_props
    col = get_or_create_collection()
    for obj in list(col.objects): 
        if "Atmosphere" not in obj.name: # Don't delete atmosphere if regenerating lights
            bpy.data.objects.remove(obj, do_unlink=True)
    
    target = get_lighting_target(context) 
    style = props.setup_type
    
    def build_light(role, settings):
        if role not in OFFSETS[style]: return
        base_vec = OFFSETS[style][role].copy()
        if props.group_rotation != 0:
            cos_a = math.cos(props.group_rotation); sin_a = math.sin(props.group_rotation)
            x = base_vec.x * cos_a - base_vec.y * sin_a
            y = base_vec.x * sin_a + base_vec.y * cos_a
            base_vec.x = x; base_vec.y = y
        position = base_vec * settings.distance
        position.z += settings.height
        loc = target.location + position
        
        lname = f"{role}_{style}"
        ldata = bpy.data.lights.new(name=lname, type='AREA')
        ldata.shape = 'RECTANGLE'
        ldata.size = settings.size; ldata.use_nodes = True
        nt = ldata.node_tree; nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputLight'); out.location=(600,0)
        diff = nt.nodes.new('OctaneDiffuseMaterial'); diff.location=(400,0)
        emit = nt.nodes.new('OctaneTextureEmission'); emit.location=(200,0)
        col_node = nt.nodes.new('OctaneRGBColor'); col_node.location=(0,0)
        try: col_node.a_value = Color(settings.color)
        except: pass
        if len(emit.inputs)>0: nt.links.new(col_node.outputs[0], emit.inputs[0])
        emit_socket = None
        for s in diff.inputs:
            if s.identifier == 'Emission': emit_socket=s; break
        if not emit_socket and len(diff.inputs)>17: emit_socket=diff.inputs[17]
        if emit_socket: nt.links.new(emit.outputs[0], emit_socket)
        nt.links.new(diff.outputs[0], out.inputs['Surface'])
        if 'Power' in emit.inputs: emit.inputs['Power'].default_value = settings.power
        
        lobj = bpy.data.objects.new(name=lname, object_data=ldata)
        col.objects.link(lobj)
        context.view_layer.objects.active = lobj  # Set as active to prevent Octane handler errors
        lobj.location = loc
        lobj["studio_role"] = role; lobj["studio_style"] = style
        if hasattr(lobj, 'octane'):
            lobj.octane.camera_visibility = settings.visible_in_camera
        
        const = lobj.constraints.new('TRACK_TO')
        const.target = target; const.track_axis = 'TRACK_NEGATIVE_Z'; const.up_axis = 'UP_Y'
        
        # Stability: Force update
        if bpy.context.view_layer: bpy.context.view_layer.update()

    build_light('KEY', props.key_light)
    if props.use_fill: build_light('FILL', props.fill_light)
    if props.use_rim: build_light('RIM', props.rim_light)

# ------------------------------------------------------------------------
#   UI
# ------------------------------------------------------------------------

class VIEW3D_PT_OctaneStudio(bpy.types.Panel):
    bl_label = "Octane Studio"
    bl_idname = "VIEW3D_PT_OctaneStudio"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = "Octane Studio"

    def draw(self, context):
        layout = self.layout
        props = context.scene.octane_studio_props
        
        row = layout.row(align=True)
        row.prop_enum(props, "ui_tab", 'CREATE', icon='SCENE')
        row.prop_enum(props, "ui_tab", 'CONTROL', icon='MOD_CLOTH')
        row.prop_enum(props, "ui_tab", 'CREATIVE', icon='PARTICLES')
        row.prop_enum(props, "ui_tab", 'TOOLS', icon='TOOL_SETTINGS')
        layout.separator()

        if props.ui_tab == 'CREATE':
            box = layout.box()
            box.label(text="Setup Configuration", icon='PREFERENCES')
            box.prop(props, "target_object", icon='OBJECT_DATA')
            box.prop(props, "setup_type", text="Style")
            row = box.row()
            row.prop(props, "use_fill"); row.prop(props, "use_rim")
            box.separator()
            row = box.row(); row.scale_y = 1.5
            row.operator("octanestudio.generate", icon='PLAY', text="Create Lighting")
            if OCTANESTUDIO_OT_Clear.poll(context): row.operator("octanestudio.clear", icon='TRASH', text="Clear")

        elif props.ui_tab == 'CONTROL':
            def draw_lp(layout, title, sp):
                box = layout.box(); row = box.row()
                row.prop(sp, "expanded", icon="TRIA_DOWN" if sp.expanded else "TRIA_RIGHT", icon_only=True, emboss=False)
                row.prop(sp, "enabled", text=title, icon='LIGHT')
                if sp.expanded:
                    col = box.column(align=True); col.enabled = sp.enabled
                    col.prop(sp, "power"); col.prop(sp, "distance"); col.prop(sp, "height"); col.prop(sp, "size", text="Softness")
                    col.separator(); col.prop(sp, "visible_in_camera", text="Show in Camera", icon='CAMERA_DATA')
                    col.separator(); col.prop(sp, "color", text="Color")
            box = layout.box(); box.label(text="Group Controls", icon='ORIENTATION_GIMBAL')
            box.prop(props, "group_rotation", text="Rotate All", slider=True); layout.separator()
            draw_lp(layout, "Key Light", props.key_light)
            if props.use_fill: draw_lp(layout, "Fill Light", props.fill_light)
            if props.use_rim: draw_lp(layout, "Rim Light", props.rim_light)

        elif props.ui_tab == 'CREATIVE':
            box = layout.box()
            box.label(text="Atmosphere / Fog", icon='WORLD')
            row = box.row()
            row.operator("octanestudio.add_atmosphere", text="Add Fog Volume", icon='VOLUME_DATA')
            col = box.column(); col.prop(props.creative, "atmos_density", slider=True)
            
            box = layout.box()
            box.label(text="Bokeh Generator", icon='PARTICLES')
            grid = box.grid_flow(columns=2, align=True)
            grid.prop(props.creative, "bokeh_count")
            grid.prop(props.creative, "bokeh_power")
            grid.prop(props.creative, "bokeh_size_min")
            grid.prop(props.creative, "bokeh_size_max")
            box.prop(props.creative, "bokeh_dist")
            box.prop(props.creative, "bokeh_spread")
            box.prop(props.creative, "bokeh_base_color")
            row = box.row(); row.scale_y = 1.5
            row.operator("octanestudio.create_bokeh", text="Generate Bokeh Elements", icon='SHADING_RENDERED')

        elif props.ui_tab == 'TOOLS':
            box = layout.box(); box.label(text="Format & Ratio", icon='RENDER_RESULT')
            grid = box.grid_flow(columns=2, align=True)
            grid.operator("octanestudio.set_aspect_ratio", text="Square (1:1)", icon='FILE_IMAGE').ratio='SQUARE'
            grid.operator("octanestudio.set_aspect_ratio", text="Portrait (4:5)", icon='IMAGE_BACKGROUND').ratio='PORTRAIT'
            grid.operator("octanestudio.set_aspect_ratio", text="Landscape (16:9)", icon='IMAGE_DATA').ratio='LANDSCAPE'
            grid.operator("octanestudio.set_aspect_ratio", text="Film (2.35:1)", icon='CAMERA_DATA').ratio='CINEMATIC'

            cam = get_portrait_cam()
            box = layout.box(); box.label(text="Camera & DOF", icon='CAMERA_DATA')
            if not cam: box.operator("octanestudio.add_camera", icon='ADD', text="Add Portrait Cam")
            else:
                row = box.row(); row.prop(props, "camera_locked", text="Lock to Target", toggle=True, icon='CONSTRAINT')
                col = box.column(align=True); col.enabled = props.camera_locked
                col.prop(props, "camera_dist"); col.prop(props, "camera_height", text="Height (Orbital)"); col.prop(props, "camera_orbit")
                col.separator(); col.label(text="Tripod Adjustment", icon='EMPTY_SINGLE_ARROW')
                col.prop(props, "camera_vertical_offset", text="Vertical Shift", slider=True)
                col.separator(); col.label(text="Display & Focus", icon='CAMERA_DATA')
                col.prop(props, "camera_show_limits", text="Show Limits")
                col.prop(props, "camera_autofocus", text="Autofocus", toggle=True)
                focus_col = col.column()
                focus_col.enabled = not props.camera_autofocus
                focus_col.prop(props, "camera_focus_distance", text="Focus Distance")

            box = layout.box(); box.label(text="Environment / Backdrop", icon='SCENE_DATA')
            col = box.column(align=True)
            has_backdrop = False; c = bpy.data.collections.get(COLLECTION_NAME)
            if c:
                for o in c.objects: 
                    if o.name.startswith("Backdrop"): has_backdrop = True; break
            if has_backdrop:
                col.label(text="Backdrop Settings:"); col.prop(props, "backdrop_color"); col.prop(props, "backdrop_roughness")
            else: col.operator("octanestudio.add_backdrop", icon='MESH_PLANE')
            # RESTORED FEATURE
            box.operator("octanestudio.studio_black", icon='WORLD', text="Set Studio Black")
            
            box = layout.box(); box.operator("octanestudio.reset_values", icon='FILE_REFRESH', text="Reset Lights")

# ------------------------------------------------------------------------
#   REGISTRATION
# ------------------------------------------------------------------------

classes = (LightSettings, CreativeSettings, OctaneStudioProperties, OCTANESTUDIO_OT_SetAspectRatio, 
           OCTANESTUDIO_OT_Generate, OCTANESTUDIO_OT_Clear, OCTANESTUDIO_OT_AddCamera, 
           OCTANESTUDIO_OT_AddBackdrop, OCTANESTUDIO_OT_AddAtmosphere, OCTANESTUDIO_OT_CreateBokeh, 
           OCTANESTUDIO_OT_StudioBlack, OCTANESTUDIO_OT_ResetValues, VIEW3D_PT_OctaneStudio)

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.octane_studio_props = bpy.props.PointerProperty(type=OctaneStudioProperties)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
    del bpy.types.Scene.octane_studio_props

if __name__ == "__main__":
    register()
    