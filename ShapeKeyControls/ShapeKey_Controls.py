# Shape Key Controls
# Copyright (C) 2023 VGmove
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
	"name" : "Shape Key Controls",
	"description" : "Additional control for Shape Key",
	"author" : "VGmove",
	"version" : (1, 0, 0),
	"blender" : (2, 80, 00),
	"location" : "Properties > Object Data Properties > ShapeKey Controls",
	"category" : "Object"
}

import bpy
from bpy.types import Panel, Operator, PropertyGroup

class Properties(PropertyGroup):
	bpy.types.Scene.mirror_by_topo = bpy.props.BoolProperty( name="Mirror by Topology",
								 description="Mirror shapekey by topology",
								 default = False )

	bpy.types.Scene.remove_original = bpy.props.BoolProperty( name="Remove Original Key",
								  description="Combine shapekey remove originals",
								  default = True)

class PROPERTIES_PT_Panel(Panel):
	bl_label = "Shape Keys Controls"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "data"

	@classmethod
	def poll(cls, context):
		if context.active_object != None:
			if bpy.context.object.mode == "OBJECT" or bpy.context.object.mode == "EDIT":
				if bpy.context.object.active_shape_key != None:
					if len(bpy.context.object.data.shape_keys.key_blocks) >= 2:
						return context.active_object.type == 'MESH'

	def draw(self, context):
		layout = self.layout

		box = layout.box()
		row = box.row()
		row.prop(context.scene, "mirror_by_topo", text='Mirror by Topology')
		row.enabled = False if bpy.context.object.mode != "OBJECT" else True
		row = box.row(align=True)
		row.operator("shapekey.mirror_selected", text='Mirror Selected')
		row.enabled = False if bpy.context.object.mode != "OBJECT" else True
		row = box.row(align=True)
		row.operator("shapekey.mirror_l_to_r", text='L to R')
		row.enabled = False if bpy.context.object.mode != "OBJECT" else True
		row.operator("shapekey.mirror_all", text='Mirror All')
		row.enabled = False if bpy.context.object.mode != "OBJECT" else True
		row.operator("shapekey.mirror_r_to_l", text='R to L')
		row.enabled = False if bpy.context.object.mode != "OBJECT" else True

		box = layout.box()
		row = box.row()
		row.prop(context.scene, "remove_original", text='Remove Original Key')
		row.enabled = False if bpy.context.object.mode != "OBJECT" else True
		row = box.row(align=True)
		row.operator("shapekey.merge", text='Merge Shapekey')
		row.enabled = False if bpy.context.object.mode != "OBJECT" else True
		row.operator("shapekey.apply_basis", text='Apply as Basis')

		row = layout.row(align=True)
		row.label(text="Rename:")
		row.operator("shapekey.addend_l", text="Add  _L")
		row.operator("shapekey.addend_merge", text="Add  +")
		row.operator("shapekey.addend_r", text="Add  _R")
		
		row = layout.row(align=True)
		row.label(text="Reset Vertex:")
		row.operator("shapekey.reset_selected_vertex", text='Selected')
		row.operator("shapekey.reset_all_vertex", text='All')

class MirrorSelected(Operator):
	bl_idname = "shapekey.mirror_selected"
	bl_label = "Mirror Selected"
	bl_description = "Mirror selected shape key with the name ending on '_R' or '_L'"

	def execute(self, context):
		key = bpy.context.object.active_shape_key
		key_index = bpy.context.object.active_shape_key_index
		list_key = bpy.context.object.data.shape_keys.key_blocks
		if key.name.endswith("_R") or key.name.endswith("_L"):
			end = ("L") if key.name[-1] == ("R") else ("R")
			new_name = key.name[:-1] + end
			if not new_name in list_key:
				bpy.ops.object.shape_key_clear()
				key.value = 1.0
				bpy.ops.object.shape_key_add(from_mix=True)
				if bpy.context.scene.mirror_by_topo == True:
					bpy.ops.object.shape_key_mirror(use_topology=True)
				else:
					bpy.ops.object.shape_key_mirror(use_topology=False)
				bpy.context.object.active_shape_key.name = new_name
				bpy.ops.object.shape_key_clear()
				for i in range((len(list_key) - (key_index + 1))-1):
					bpy.ops.object.shape_key_move(type='UP')
				if key.name.endswith('_R'):
					bpy.ops.object.shape_key_move(type='UP')
			else:
				self.report({'INFO'}, "This shape key already exists")
		else:
			self.report({'INFO'}, "Shape key name does not end with '_R' or '_L'")
		return {'FINISHED'}

class Mirror_LtoR(Operator):
	bl_idname = "shapekey.mirror_l_to_r"
	bl_label = "ShapeKey Mirror L to R" 
	bl_description = "Mirror all shapekeys with the name ending on '_L'"

	def execute(self, context):
		order = 0
		list_key = bpy.context.object.data.shape_keys.key_blocks
		for num, key in enumerate(list_key):
			if key.name.endswith('_L'):
				new_name = key.name[:-1] + ("R")
				if not new_name in list_key:
					bpy.ops.object.shape_key_clear()
					key.value = 1.0
					bpy.ops.object.shape_key_add(from_mix=True)
					if bpy.context.scene.mirror_by_topo == True:
						bpy.ops.object.shape_key_mirror(use_topology=True)
					else:
						bpy.ops.object.shape_key_mirror(use_topology=False)
					bpy.context.object.active_shape_key.name = new_name
					bpy.ops.object.shape_key_clear()
					for i in range((len(list_key) - (num + order + 1))-1):
						bpy.ops.object.shape_key_move(type='UP')
					order += 1
		return {'FINISHED'}

class Mirror_All(Operator):
	bl_idname = "shapekey.mirror_all"
	bl_label = "ShapeKey Mirror All" 
	bl_description = "Mirror all shapekeys with the name ending on '_R' and '_L'"

	def execute(self, context):
		order = 0
		list_key = bpy.context.object.data.shape_keys.key_blocks
		for num, key in enumerate(list_key):
			if key.name.endswith('_L') or key.name.endswith('_R'):
				end = ("L") if key.name[-1] == ("R") else ("R")
				new_name = key.name[:-1] + (end)
				if not new_name in list_key:
					bpy.ops.object.shape_key_clear()
					key.value = 1.0
					bpy.ops.object.shape_key_add(from_mix=True)
					if bpy.context.scene.mirror_by_topo == True:
						bpy.ops.object.shape_key_mirror(use_topology=True)
					else:
						bpy.ops.object.shape_key_mirror(use_topology=False)
					bpy.context.object.active_shape_key.name = new_name
					bpy.ops.object.shape_key_clear() 
					for i in range((len(list_key) - (num + order + 1))-1):
						bpy.ops.object.shape_key_move(type='UP')
					if key.name.endswith('_R'):
						bpy.ops.object.shape_key_move(type='UP')
					order += 1
		return {'FINISHED'}

class Mirror_RtoL(Operator):
	bl_idname = "shapekey.mirror_r_to_l"
	bl_label = "ShapeKey Mirror R to L" 
	bl_description = "Mirror all shapekeys with the name ending on '_R'"
	
	def execute(self, context):
		order = 0
		list_key = bpy.context.object.data.shape_keys.key_blocks
		for num, key in enumerate(list_key):
			if key.name.endswith('_R'):
				new_name = key.name[:-1] + ("L")
				if not new_name in list_key:
					bpy.ops.object.shape_key_clear()
					key.value = 1.0
					bpy.ops.object.shape_key_add(from_mix=True)
					if bpy.context.scene.mirror_by_topo == True:
						bpy.ops.object.shape_key_mirror(use_topology=True)
					else:
						bpy.ops.object.shape_key_mirror(use_topology=False)
					bpy.context.object.active_shape_key.name = new_name
					bpy.ops.object.shape_key_clear()
					for i in range((len(list_key) - (num + order + 1))-1):
						bpy.ops.object.shape_key_move(type='UP')
					if key.name.endswith('_R'):
						bpy.ops.object.shape_key_move(type='UP')
					order += 1
		return {'FINISHED'}		

class Merge(Operator):
	bl_idname = "shapekey.merge"
	bl_label = "Merge Shapekey" 
	bl_description = "Combine shapekeys with the name ending on '+'"

	def execute(self, context):          
		list_key = bpy.context.object.data.shape_keys.key_blocks
		key_united = [x for x in list_key[1:] if x.name.endswith('+')]
		if len(key_united) >= 2:
			bpy.ops.object.shape_key_clear()
			for key in key_united:
				key.value = 1
			bpy.context.object.active_shape_key_index = 0
			bpy.ops.object.shape_key_add(from_mix=True)
			new_name = "Combined " + ' + '.join(e.name[:-1] for e in key_united)
			bpy.context.object.active_shape_key.name = new_name
			for key in key_united:
				if bpy.context.scene.remove_original == True:
					bpy.context.object.active_shape_key_index = list_key.keys().index(key.name)
					bpy.ops.object.shape_key_remove(all=False)
				else:
					key.name = key.name[:-1]
			bpy.ops.object.shape_key_clear()
		else:
			self.report({'INFO'}, "No shape keys with ending on '+' for combine")
		return {'FINISHED'}

class ApplyBasis(Operator):
	bl_idname = "shapekey.apply_basis"
	bl_label = "Apply as Basis"
	bl_description = "Apply selected shapekey as base"

	def execute(self, context):            
		list_key = bpy.context.object.data.shape_keys.key_blocks
		apply_key = bpy.context.object.active_shape_key
		bpy.ops.object.shape_key_clear()
		apply_key.value = 1
		bpy.ops.object.shape_key_add(from_mix=True)
		for basis in list_key[:1]:
			bpy.context.object.active_shape_key.name = basis.name + ("*")
		for a_key in list_key[1:-1]:
			if not apply_key.name == a_key.name:
				bpy.ops.object.shape_key_clear()
				apply_key.value = 1
				a_key.value = 1
				bpy.ops.object.shape_key_add(from_mix=True)
				bpy.context.object.active_shape_key.name = a_key.name + ("*")
				bpy.ops.object.shape_key_clear()
		for remove in range(len(list_key)-len(list_key)//2):
			bpy.context.object.active_shape_key_index = 0
			bpy.ops.object.shape_key_remove(all=False)
		for rename in list_key:
			rename.name = rename.name[:-1]  
		return {'FINISHED'}

class AddEnd_L(Operator):
	bl_idname = "shapekey.addend_l"
	bl_label = "AddEnd _L"
	bl_description = "Add the ending '_L' to the name"

	def execute(self, context):
		key = bpy.context.object.active_shape_key
		list_key = bpy.context.object.data.shape_keys.key_blocks
		if key.name.endswith("_R") or key.name.endswith("_L"):
			new_name = key.name[0:-2] + "_L"
		else:
			new_name = key.name + "_L"
		
		if not new_name in list_key:
			bpy.context.object.active_shape_key.name = new_name
		else:
			self.report({'INFO'}, "This name already exists")
			
		return {'FINISHED'}

class AddEnd_Merge(Operator):
	bl_idname = "shapekey.addend_merge"
	bl_label = "AddEnd Merge"
	bl_description = "Add the ending '+' to the name for merge"

	def execute(self, context):
		key = bpy.context.object.active_shape_key
		list_key = bpy.context.object.data.shape_keys.key_blocks
		if key.name.endswith("+"):
			new_name = key.name[0:-1]
		else:
			new_name = key.name + "+"
		
		if not new_name in list_key:
			bpy.context.object.active_shape_key.name = new_name
		else:
			self.report({'INFO'}, "This name already exists")
			
		return {'FINISHED'}	

class AddEnd_R(Operator):
	bl_idname = "shapekey.addend_r"
	bl_label = "AddEnd _R"
	bl_description = "Add the ending '_R' to the name"

	def execute(self, context):
		key = bpy.context.object.active_shape_key
		list_key = bpy.context.object.data.shape_keys.key_blocks
		if key.name.endswith("_R") or key.name.endswith("_L"):
			new_name = key.name[0:-2] + "_R"
		else:
			new_name = key.name + "_R"
		
		if not new_name in list_key:
			bpy.context.object.active_shape_key.name = new_name
		else:
			self.report({'INFO'}, "This name already exists")
			
		return {'FINISHED'}

class ResetSelectedVertex(Operator):
	bl_idname = "shapekey.reset_selected_vertex"
	bl_label = "Reset Selected Vertex"
	bl_description = "Reset selected vertex in <Edit Mode>"

	def execute(self, context):
		if bpy.context.object.mode == "EDIT":
			for basis in bpy.context.object.data.shape_keys.key_blocks[:1]:
				bpy.ops.mesh.blend_from_shape(shape=basis.name, blend=1, add=False)
				bpy.ops.mesh.normals_make_consistent(inside=False)
		return {'FINISHED'}

class ResetAllVertex(Operator):
	bl_idname = "shapekey.reset_all_vertex"
	bl_label = "Reset All Vertex"
	bl_description = "Reset all vertex in <Edit Mode>"

	def execute(self, context):
		if bpy.context.object.mode == "EDIT":
			for basis in bpy.context.object.data.shape_keys.key_blocks[:1]:
				bpy.ops.mesh.select_all(action='DESELECT')
				bpy.ops.mesh.select_all(action='INVERT')
				bpy.ops.mesh.blend_from_shape(shape=basis.name, blend=1, add=False)
				bpy.ops.mesh.normals_make_consistent(inside=False)
				bpy.ops.mesh.select_all(action='DESELECT')
		return {'FINISHED'}

classes = [	PROPERTIES_PT_Panel,
		Properties,
		MirrorSelected,
		Mirror_LtoR,
		Mirror_All,
		Mirror_RtoL,
		Merge,
		ApplyBasis,
		AddEnd_L,
		AddEnd_Merge,
		AddEnd_R,
		ResetSelectedVertex,
		ResetAllVertex,
	]

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

if __name__ == "__main__":
	register()
