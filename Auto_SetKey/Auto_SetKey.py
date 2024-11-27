# Auto SetKey
# Copyright (C) 2024 VGmove
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
	"name" : "Auto SetKey",
	"description" : "Automatically set keys for repeating types of actions",
	"author" : "VGmove",
	"version" : (1, 0, 0),
	"blender" : (4, 1, 00),
	"location" : "Dope Sheet > Edit > SetKey",
	"category" : "Animation"
}

import os
import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       EnumProperty,
                       PointerProperty,
                       FloatVectorProperty,
                       )
from bpy.types import (Menu,
                       Panel,
                       Operator,
                       PropertyGroup,
                       )

# Scene Properties
class SETKEY_Properties(PropertyGroup):
	blend_blink : FloatProperty(
		name="Blend:",
		description="Blend of blinks",
		default = 0.9,
		min = 0.5,
		max = 1
	)
	duration_blink : IntProperty(
		name="Duration:",
		description="Step length in frames",
		default = 12,
		min = 2,
		max = 100
	)
	count_blink : IntProperty(
		name="Count:",
		description="Number of blinks",
		default = 2,
		min = 1,
		max = 100
	)
	duration_fade : IntProperty(
		name="Duration:",
		description="Step length in frames",
		default = 12,
		min = 3,
		max = 100
	)
	color_blink : FloatVectorProperty(
		name="Color",
		description="Color object blinks",
		subtype = "COLOR",
		default = (1.0,0.0,0.0,1.0),
		size = 4,
		min = 0, 
		max = 1
	)													
	toggle_type : EnumProperty(
		items= (
			("1", "Show", "Set keys for show an object"),
			("2", "In/Out", "FadeIn / FadeOut"),
			("3", "Hide", "Set keys for hide an object")
		),
		default = "2"
	)
	duration_pause : IntProperty(
		name="Duration:",
		description="Step length in frames",
		default = 24,
		min = 5,
		max = 50
	)
	move_cursor : BoolProperty(
		name="Move Timeline Cursor",
		description="Move Timeline Cursor to end new keyframe",
		default = True
	)
	single_user : BoolProperty(
		name="Make Single User",
		description="Make single user for materials",
		default = True
	)

#Operators
class SETKEY_Blink(Operator):
	bl_idname = "action.setkey_blink"
	bl_label = "Set Key Blink"
	bl_description = "Auto set key for blink"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		# Get Materials
		materials = []
		for object in bpy.context.selected_objects:
			material = object.active_material
			if material and material.use_nodes:
				if context.scene.property.single_user and material.users > 1:
					user_count = sum(p.active_material == material for p in bpy.context.selected_objects)
					if material.users != user_count:
						object.active_material = object.active_material.copy()
						if object.active_material.node_tree.animation_data:
							action_material = object.active_material.node_tree.animation_data.action
							action_material = action_material.copy()
				if not object.active_material in materials:
					materials.append(object.active_material)
			else: continue
		
		for material in materials:
			# Create variable
			material_nodes = material.node_tree.nodes
			links = material.node_tree.links

			# Check available OUTPUT_MATERIAL
			material_output = None
			for node in material_nodes:
				if node.type == "OUTPUT_MATERIAL":
					material_output = node
					break
			if material_output is None:
				material_output = material_nodes.new("ShaderNodeOutputMaterial")

			# Check available group
			group_node = None
			groups = [node for node in material_nodes if node.type == "GROUP"]
			for group in groups:
				if "SetKey_Blink" in group.node_tree.name:
					group_node = group
					self.set_key(context, group_node)
					break
			if group_node is None:
				group_node = self.create_group(context, material_output, material_nodes, links)
				self.set_key(context, group_node)
		
		if context.scene.property.move_cursor:
			curent_frame = bpy.context.scene.frame_current
			context.scene.frame_set(curent_frame + (context.scene.property.duration_blink * (context.scene.property.count_blink * 2)))
		
		return {"FINISHED"}

	def create_group(self, context, material_output, material_nodes, links):
		# Create nodes (input \ output) in group
		group = bpy.data.node_groups.new("SetKey_Blink", "ShaderNodeTree")
		group_input : bpy.types.ShaderNodeGroup = group.nodes.new("NodeGroupInput")
		group_input.location = (0, 0)
		group_output : bpy.types.ShaderNodeGroup = group.nodes.new("NodeGroupOutput")
		group_output.location = (900, 0)
		
		mix_shader = group.nodes.new("ShaderNodeMixShader")
		mix_shader.location = (600,100)
		
		diffuse_shader = group.nodes.new("ShaderNodeBsdfDiffuse")
		diffuse_shader.location = (300, -100)
		
		group.interface.new_socket(name="Shader", description="Shader Input", in_out ="INPUT", socket_type="NodeSocketShader")
		group.interface.new_socket(name="Color", description="Color Input", in_out ="INPUT", socket_type="NodeSocketColor")
		group.interface.new_socket(name="Value", description="Color float factor", in_out ="INPUT", socket_type="NodeSocketFloat")
		group.interface.new_socket(name="Shader", description="Shader Output", in_out ="OUTPUT", socket_type="NodeSocketShader")
		
		group.interface.items_tree[2].default_value = (1, 0, 0, 1)
		group.interface.items_tree[3].default_value = 0
		group.interface.items_tree[3].min_value  = 0
		group.interface.items_tree[3].max_value  = 1

		group.links.new(diffuse_shader.outputs[0], mix_shader.inputs[2])
		group.links.new(group_input.outputs[0], mix_shader.inputs[1])
		group.links.new(group_input.outputs[1], diffuse_shader.inputs[0])
		group.links.new(group_input.outputs[2], mix_shader.inputs[0])
		group.links.new(mix_shader.outputs[0], group_output.inputs[0])
		
		# Create group node
		group_node = material_nodes.new("ShaderNodeGroup")
		group_node.node_tree = group
		group_node.location = material_output.location
		material_output.location.x = material_output.location.x + 300
		
		if material_output.inputs["Surface"].links:
			links.new(material_output.inputs["Surface"].links[0].from_node.outputs[0], group_node.inputs[0])
			links.new(group_node.outputs["Shader"], material_output.inputs["Surface"])
		else:
			links.new(group_node.outputs["Shader"], material_output.inputs["Surface"])
		return group_node

	def set_key(self, context, group_node):
		curent_frame = bpy.context.scene.frame_current
		value = group_node.inputs[2]
		value.default_value = 0
		color = group_node.inputs["Color"]
		color.default_value = context.scene.property.color_blink
		
		for i in range((context.scene.property.count_blink * 2) + 1):
			value.keyframe_insert("default_value", frame = curent_frame)
			color.keyframe_insert("default_value", frame = curent_frame)
			curent_frame = curent_frame + context.scene.property.duration_blink
			value.default_value = not value.default_value
			value.default_value = max(min(value.default_value, context.scene.property.blend_blink), 0)
		return {"FINISHED"}

class SETKEY_Transparent(Operator):
	bl_idname = "action.setkey_transparent"
	bl_label = "Set Key Transparent"
	bl_description = "Auto set key for transparency"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		# Get Materials
		materials = []
		for object in bpy.context.selected_objects:
			material = object.active_material
			if material and material.use_nodes:
				if context.scene.property.single_user and material.users > 1:
					user_count = sum(p.active_material == material for p in bpy.context.selected_objects)
					if material.users != user_count:
						object.active_material = object.active_material.copy()
						if object.active_material.node_tree.animation_data:
							action_material = object.active_material.node_tree.animation_data.action
							action_material = action_material.copy()
				if not object.active_material in materials:
					materials.append(object.active_material)
			else: continue
		
		for material in materials:
			# Create variable
			material_nodes = material.node_tree.nodes
			links = material.node_tree.links
			
			# Material parameters
			material.blend_method = "HASHED"
			material.use_backface_culling = True

			# Check available OUTPUT_MATERIAL
			material_output = None
			for node in material_nodes:
				if node.type == "OUTPUT_MATERIAL":
					material_output = node
					break
			if material_output is None:
				material_output = material_nodes.new("ShaderNodeOutputMaterial")
			
			# Check available group
			group_node = None
			groups = [node for node in material_nodes if node.type == "GROUP"]
			for group in groups:
				if "SetKey_Transparent" in group.node_tree.name:
					group_node = group
					self.set_key(context, group_node)
					break
			if group_node is None:
				group_node = self.create_group(context, material_output, material_nodes, links)
				self.set_key(context, group_node)
				
		if context.scene.property.move_cursor:
			curent_frame = bpy.context.scene.frame_current
			if context.scene.property.toggle_type == "2":
				context.scene.frame_set(curent_frame + (context.scene.property.duration_fade * 5))
			else:
				context.scene.frame_set(curent_frame + context.scene.property.duration_fade )
			
		return {"FINISHED"}
	
	def create_group(self, context, material_output, material_nodes, links):
		# Create nodes (input \ output) in group
		group = bpy.data.node_groups.new("SetKey_Transparent", "ShaderNodeTree")
		group_input : bpy.types.ShaderNodeGroup = group.nodes.new("NodeGroupInput")
		group_input.location = (0, 0)
		group_output : bpy.types.ShaderNodeGroup = group.nodes.new("NodeGroupOutput")
		group_output.location = (900, 0)
		
		mix_shader = group.nodes.new("ShaderNodeMixShader")
		mix_shader.location = (600,100)
		
		transparent_shader = group.nodes.new("ShaderNodeBsdfTransparent")
		transparent_shader.location = (300, -100)
		transparent_shader.inputs["Color"].default_value = (1, 1, 1, 0)

		group.interface.new_socket(name="Shader", description="Shader Input", in_out ="INPUT", socket_type="NodeSocketShader")
		group.interface.new_socket(name="Value", description="Transparency float factor", in_out ="INPUT", socket_type="NodeSocketFloat")
		group.interface.new_socket(name="Shader", description="Shader Output", in_out ="OUTPUT", socket_type="NodeSocketShader")

		group.interface.items_tree[2].default_value = 0
		group.interface.items_tree[2].min_value  = 0
		group.interface.items_tree[2].max_value  = 1

		group.links.new(transparent_shader.outputs[0], mix_shader.inputs[2])
		group.links.new(group_input.outputs[0], mix_shader.inputs[1])
		group.links.new(group_input.outputs[1], mix_shader.inputs[0])
		group.links.new(mix_shader.outputs[0], group_output.inputs[0])

		# Create group node
		group_node = material_nodes.new("ShaderNodeGroup")
		group_node.node_tree = group
		group_node.location = material_output.location
		material_output.location.x = material_output.location.x + 300

		if material_output.inputs["Surface"].links:
			links.new(material_output.inputs["Surface"].links[0].from_node.outputs[0], group_node.inputs[0])
			links.new(group_node.outputs["Shader"], material_output.inputs["Surface"])
		else:
			links.new(group_node.outputs["Shader"], material_output.inputs["Surface"])
		return group_node

	def set_key(self, context, group_node):
		curent_frame = bpy.context.scene.frame_current
		value = group_node.inputs[1]
		
		if context.scene.property.toggle_type == "1":
			value.default_value = 1
			range_value = 2
		elif context.scene.property.toggle_type == "2":
			value.default_value = 1
			range_value = 4
		elif context.scene.property.toggle_type == "3":
			value.default_value = 0
			range_value = 2
			
		for i in range(range_value):
			if i == 2:
				curent_frame += context.scene.property.duration_fade * 2
				value.default_value = 0
			value.keyframe_insert("default_value", frame = curent_frame)
			curent_frame += context.scene.property.duration_fade
			value.default_value = not value.default_value
		return {"FINISHED"}

class SETKEY_Transparent_Hide(SETKEY_Transparent):
	bl_idname = "action.setkey_transparent_hide"
	bl_label = "Transparent Hide"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		context.scene.property.toggle_type = "3"
		SETKEY_Transparent.execute(self, context)
		return {'FINISHED'}

class SETKEY_Transparent_InOut(SETKEY_Transparent):
	bl_idname = "action.setkey_transparent_inout"
	bl_label = "Transparent In/Out"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		context.scene.property.toggle_type = "2"
		SETKEY_Transparent.execute(self, context)
		return {'FINISHED'}

class SETKEY_Transparent_Show(SETKEY_Transparent):
	bl_idname = "action.setkey_transparent_show"
	bl_label = "Transparent Show"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		context.scene.property.toggle_type = "1"
		SETKEY_Transparent.execute(self, context)
		return {'FINISHED'}

# Pause
class SETKEY_Marker(Operator):
	bl_idname = "action.setkey_marker"
	bl_label = "Set Marker Pause"
	bl_description = "Set marker for pause"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		curent_frame = bpy.context.scene.frame_current
		context.scene.timeline_markers.new('P', frame=curent_frame)
		return {'FINISHED'}

class SETKEY_Marker_Save(Operator):
	bl_idname = "action.setkey_marker_save"
	bl_label = "Save Marker"
	bl_description = "Save markers to file in output render directory"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		markers = self.get_markers(context)
		self.save_markers(context, markers)
		return {'FINISHED'}

	def get_markers(self, context):
		markers = []
		for marker in bpy.context.scene.timeline_markers:
			if marker.name == "P" and marker.frame not in markers:
				markers.extend([marker.frame])
		markers = sorted(markers)
		return markers
	
	def save_markers(self, context, markers):
		output_path = bpy.context.scene.render.filepath
		abs_output_path = bpy.path.abspath(output_path)
		
		if abs_output_path[-1] != '\\':
			abs_output_path = abs_output_path.rpartition('\\')[0] 
			abs_output_path = abs_output_path + "\\"
		
		dir_check = os.path.dirname(abs_output_path)
		os.makedirs(dir_check, exist_ok=True)
		
		with open(abs_output_path + "pauses.txt", "w") as f:
			for marker in markers:
				f.write(f"{marker} ")
		return {'FINISHED'}

class SETKEY_Pause(Operator):
	bl_idname = "action.setkey_pause"
	bl_label = "Create Pause"
	bl_description = "Create pause on selected sequence"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		active_strip = bpy.context.scene.sequence_editor.active_strip
		if len(bpy.context.selected_sequences) == 1 and active_strip.type == "IMAGE":
			active_strip_path = bpy.path.abspath(active_strip.directory)
			markers = self.get_markers(context, active_strip_path)
			if markers:
				self.create_pause(context, markers, active_strip, active_strip_path)
		return {"FINISHED"}

	def get_markers(self, context, active_strip_path):
		markers = []
		pause_file = active_strip_path + "pauses.txt"
		if os.path.exists(pause_file):
			with open(pause_file) as f:
				for marker in f.readline().split():
					if marker.isdigit():
						markers.append(int(marker))
			return markers

	def create_pause(self, context, markers, active_strip, active_strip_path):
		step = 0
		start_frame = active_strip.frame_final_start
		active_strip_length = active_strip.frame_final_end
		duration_pause = context.scene.property.duration_pause
		for marker in markers:
			end_strip = bpy.context.selected_sequences[-1]
			marker_offset = marker + start_frame + step # -set_start_frame if start not 0 frame			
			if marker_offset in range(end_strip.frame_final_start, end_strip.frame_final_end + 1):
				next_strip = end_strip.split(marker_offset, "SOFT")
				if next_strip is None:
					next_strip = end_strip

				next_strip.frame_start += duration_pause
				if marker == markers[-1] and marker_offset == end_strip.frame_final_end - duration_pause:
					next_strip.frame_start -= duration_pause
				
				sequence_image = next_strip.strip_elem_from_frame(marker_offset + duration_pause).filename
				image = active_strip_path + sequence_image
				sequences = bpy.context.scene.sequence_editor.sequences
				image_strip = sequences.new_image("Image", image, active_strip.channel, marker_offset)
				image_strip.select = False
				image_strip.frame_final_duration = duration_pause
				image_strip.color_tag = "COLOR_05"
				
				step += context.scene.property.duration_pause
		bpy.context.scene.frame_end = active_strip_length + step - 1
		bpy.context.scene.frame_start = start_frame
		return {'FINISHED'}

# Draw UI TimeLine
class SETKEY_panel:
	bl_space_type = "DOPESHEET_EDITOR"
	bl_region_type = "UI"
	bl_category = "Action"
	bl_options = {"DEFAULT_CLOSED"}

class SETKEY_PT_panel(SETKEY_panel, Panel):
	bl_idname = "SETKEY_PT_panel"
	bl_label = "Auto SetKey"

	@classmethod
	def poll(self,context):
		return context.active_object is not None

	def draw(self, context):
		layout = self.layout

class SETKEY_PT_subpanel_1(SETKEY_panel, Panel):
	bl_parent_id = "SETKEY_PT_panel"
	bl_label = "Blink"

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.prop(context.scene.property, "color_blink")
		col = layout.column(align=True)
		col.prop(context.scene.property, "blend_blink")
		col.prop(context.scene.property, "duration_blink")
		col.prop(context.scene.property, "count_blink")
		col.separator()
		row = col.row()
		row.label(text="Set Keys:")
		row.scale_x = 15
		row.operator(SETKEY_Blink.bl_idname, text="", icon="KEYFRAME_HLT")

class SETKEY_PT_subpanel_2(SETKEY_panel, Panel):
	bl_parent_id = "SETKEY_PT_panel"
	bl_label = "Transparent"

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		row = col.row()
		row.alignment = "RIGHT"
		row.prop(context.scene.property, "toggle_type", expand=True)
		col.prop(context.scene.property, "duration_fade")
		col.separator()
		row = col.row()
		row.label(text="Set Keys:")
		row.scale_x = 15
		row.operator(SETKEY_Transparent.bl_idname, text="", icon="KEYFRAME_HLT")

class SETKEY_PT_subpanel_3(SETKEY_panel, Panel):
	bl_parent_id = "SETKEY_PT_panel"
	bl_label = "Pause"

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		row = col.row()
		row.alignment = "LEFT"
		row.label(text="Save Markers:")
		row = col.row()
		row.operator(SETKEY_Marker_Save.bl_idname, text="Save", icon="FILE")
		col.separator()
		row = col.row()
		row.label(text="Set Marker:")
		row.scale_x = 15
		row.operator(SETKEY_Marker.bl_idname, text="", icon="MARKER_HLT")

class SETKEY_PT_subpanel_4(SETKEY_panel, Panel):
	bl_parent_id = "SETKEY_PT_panel"
	bl_label = "Settings"

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.alignment = "LEFT"
		col.prop(context.scene.property, "move_cursor")
		col.prop(context.scene.property, "single_user")

class SETKEY_MT_menu(Menu):
	bl_idname = "SETKEY_MT_menu"
	bl_label = "Auto SetKey"

	def draw(self, context):
		layout = self.layout
		layout.separator()
		layout.menu(SETKEY_MT_submenu.bl_idname)

class SETKEY_MT_submenu(Menu):
	bl_idname = "SETKEY_MT_submenu"
	bl_label = "Auto SetKey"

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def draw(self, context):
		layout = self.layout
		layout.operator(SETKEY_Blink.bl_idname, icon="KEYFRAME_HLT")
		layout.separator()
		layout.operator(SETKEY_Transparent_Show.bl_idname, icon="HIDE_OFF")
		layout.operator(SETKEY_Transparent_InOut.bl_idname, icon="SMOOTHCURVE")
		layout.operator(SETKEY_Transparent_Hide.bl_idname, icon="HIDE_ON")
		layout.separator()
		layout.operator(SETKEY_Marker.bl_idname, icon="MARKER_HLT")

# Draw UI Sequencer
class SETKEY_panel_se:
	bl_space_type = "SEQUENCE_EDITOR"
	bl_region_type = "UI"
	bl_category = "Tool"
	bl_options = {"DEFAULT_CLOSED"}

class SETKEY_PT_panel_se(SETKEY_panel_se, Panel):
	bl_idname = "SETKEY_PT_panel_se"
	bl_label = "Auto SetKey"

	@classmethod
	def poll(self,context):
		return context.active_object is not None

	def draw(self, context):
		layout = self.layout

class SETKEY_PT_subpanel_se_1(SETKEY_panel_se, Panel):
	bl_parent_id = "SETKEY_PT_panel_se"
	bl_label = "Pause"

	def draw(self, context):
		layout = self.layout
		col = layout.column(align=True)
		col.prop(context.scene.property, "duration_pause")
		col = layout.column()
		row = col.row()
		row.label(text="Create Pauses:")
		row.scale_x = 15
		row.operator(SETKEY_Pause.bl_idname, text="", icon="CENTER_ONLY")

classes = (
	SETKEY_Properties,
	SETKEY_Blink,
	SETKEY_Transparent_Show,
	SETKEY_Transparent_InOut,
	SETKEY_Transparent_Hide,
	SETKEY_Transparent,
	SETKEY_Marker_Save,
	SETKEY_Marker,
	SETKEY_Pause,
	SETKEY_PT_panel,
	SETKEY_PT_subpanel_1,
	SETKEY_PT_subpanel_2,
	SETKEY_PT_subpanel_3,
	SETKEY_PT_subpanel_4,
	SETKEY_MT_menu,
	SETKEY_MT_submenu,
	SETKEY_PT_panel_se,
	SETKEY_PT_subpanel_se_1
)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.Scene.property = PointerProperty(type = SETKEY_Properties)
	bpy.types.DOPESHEET_MT_context_menu.append(SETKEY_MT_menu.draw)

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	
	del bpy.types.Scene.property
	bpy.types.DOPESHEET_MT_context_menu.remove(SETKEY_MT_menu.draw)

if __name__ == "__main__" :
	register()
