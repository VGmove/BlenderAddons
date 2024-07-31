# Objects Render
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

import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       EnumProperty,
                       PointerProperty,
					   FloatVectorProperty,
                       )
from bpy.types import (Panel,
                       Operator,
                       PropertyGroup,
                       )

# Scene Properties
class Propertys(PropertyGroup):
	length_blink : IntProperty(
		name="Length:",
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
		name="Duration Fade:",
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
																
	toggle_view : EnumProperty(
		items= (
			("1", "Show", "Set keys for show an object"),    
			("2", "Hide", "Set keys for hide an object")
		),
		name = "radio buttons",
		default = "2"
	)

#Operators
class SETKEY_Blink(Operator):
	bl_idname = "wm.setkey_blink"
	bl_label = "SetKey Blink"
	bl_description = "Auto set key for blink"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		# Get Materials
		selected_objects = [obj for obj in bpy.context.selected_objects]
		materials = []
		for object in selected_objects:
			material = object.active_material
			if material and material.use_nodes and not material in materials:
				materials.append(material)
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

		curent_frame = bpy.context.scene.frame_current
		context.scene.frame_set(curent_frame + (context.scene.property.length_blink * (context.scene.property.count_blink * 2)))
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
			curent_frame = curent_frame + context.scene.property.length_blink
			value.default_value = not value.default_value
		return {"FINISHED"}

class SETKEY_Transparent(Operator):
	bl_idname = "wm.setkey_transparent"
	bl_label = "SetKey Transparent"
	bl_description = "Auto set key for transparency"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		# Get Materials
		selected_objects = [obj for obj in bpy.context.selected_objects]
		materials = []
		for object in selected_objects:
			material = object.active_material
			if material and material.use_nodes and not material in materials:
				materials.append(material)
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
		
		curent_frame = bpy.context.scene.frame_current
		context.scene.frame_set(curent_frame + context.scene.property.duration_fade)

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

		if context.scene.property.toggle_view == "1":
			value.default_value = 1
		elif context.scene.property.toggle_view == "2":
			value.default_value = 0
			
		for i in range(2):
			value.keyframe_insert("default_value", frame = curent_frame)
			curent_frame = curent_frame + context.scene.property.duration_fade
			value.default_value = not value.default_value
			print(value.default_value)
		return {"FINISHED"}
	
# Draw UI
class MAINPANEL_panel:
	bl_space_type = "DOPESHEET_EDITOR"
	bl_region_type = "UI"
	bl_category = "Edit"
	bl_options = {"DEFAULT_CLOSED"}

class PANEL_PT_panel(MAINPANEL_panel, Panel):
	bl_idname = "PANEL_PT_panel"
	bl_label = "Auto SetKey"

	@classmethod
	def poll(self,context):
		return context.object is not None

	def draw(self, context):
		layout = self.layout

class SUBPANEL_PT_panel_1(MAINPANEL_panel, Panel):
	bl_parent_id = "PANEL_PT_panel"
	bl_label = "Blink"

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.prop(context.scene.property, "color_blink")
		col = layout.column(align=True)
		col.prop(context.scene.property, "length_blink")
		col.prop(context.scene.property, "count_blink")
		col.separator()
		row = col.row()
		row.label(text="Set keys:")
		row.scale_x = 15
		row.operator("wm.setkey_blink", text="", icon="REC")


class SUBPANEL_PT_panel_2(MAINPANEL_panel, Panel):
	bl_parent_id = "PANEL_PT_panel"
	bl_label = "Transparent"

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		row = col.row()
		row.alignment = "RIGHT"
		row.prop(context.scene.property, "toggle_view", icon = "PLUGIN", expand=True)
		col.prop(context.scene.property, "duration_fade")
		col.separator()
		row = col.row()
		row.label(text="Set keys:")
		row.scale_x = 15
		row.operator("wm.setkey_transparent", text="", icon="REC")

classes = (
	Propertys,
	SETKEY_Blink,
	SETKEY_Transparent,
	PANEL_PT_panel,
	SUBPANEL_PT_panel_1,
	SUBPANEL_PT_panel_2
)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.Scene.property = PointerProperty(type=Propertys)

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	
	del bpy.types.Scene.property

if __name__ == "__main__" :
	register()