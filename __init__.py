
bl_info = {
    'name': 'Load SWC neuron',
    'author': 'Christopher M. Bruns',
    'version': (1, 0, 0),
    'blender': (2, 76, 0),
    'location': 'File > Import > SWC Neuron',
    'description': 'Import SWC Neuron Structures',
    'license': 'MIT',
    'category': 'Import'
}

__author__ = bl_info['author']
__license__ = bl_info['license']
__version__ = ".".join([str(s) for s in bl_info['version']])


import os

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty


class SwcNeuronImporter(bpy.types.Operator, ImportHelper):
    "Loads SWC format neuron structures"

    bl_label = 'Import SWC Neuron structures'
    bl_idname = 'import_mesh.swcneuron'
    filename_ext = '.swc'
    filter_glob = StringProperty(
            default="*.swc",
            options={'HIDDEN'})
    
    def _neuron_name(self):
        return os.path.splitext(os.path.basename(self.filepath))[0]
    
    def execute(self, context):
        self.load_swc_file(self.filepath)
        swc_name = self._neuron_name()
        # print (swc_name)
        bpy.ops.object.empty_add()
        root = bpy.context.object
        root.name = swc_name
        # root.location = self.first_node['xyz']
        skeleton = self.create_skeleton()
        skeleton.parent = root
        self.create_node_spheres()
        return {'FINISHED'}
        
    def load_swc_file(self, filename):
        self.nodes = dict()
        self.first_node = None
        self.index_from_id = dict()
        self.vertices = list()
        with open(self.filepath, 'r') as fh:
            node_count = 0
            for line in fh:
                if line.startswith('#'):
                    continue # skip comments
                fields = line.split() # split on all runs of whitespace, including tabs
                if len(fields) < 7:
                    continue # not enough fields
                id = int(fields[0])
                type_ = int(fields[1])
                xyz = [float(x) for x in fields[2:5]]
                radius = float(fields[5])
                parent_id = int(fields[6])
                self.nodes[id] = {
                        'id': id,
                        'type': type_, 
                        'xyz': xyz, 
                        'radius': radius,
                        'parent_id': parent_id
                }
                if self.first_node is None:
                    self.first_node = self.nodes[id]
                self.vertices.append(xyz)
                self.index_from_id[id] = node_count
                node_count += 1
            print( "%s SWC nodes read" % node_count )
        self.edges = list()
        for id, data in self.nodes.items():
            if data['parent_id'] not in self.index_from_id:
                continue # no parent
            v1 = self.index_from_id[id]
            v2 = self.index_from_id[data['parent_id']]
            self.edges.append( (v1, v2) )
        return self.nodes
    
    def create_node_spheres(self):
        for id, v in self.nodes.items():
            r = v['radius']
            xyz = v['xyz']
            bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                    radius=r,
                    location=xyz)            
    
    def create_skeleton(self):
        "Skeletal model of neuron, using only mesh vertices and edges"
        if len(self.nodes) <= 0:
            return
        # skeleton made of line segments
        skeleton_name = self._neuron_name() + ' skeleton'
        mesh = bpy.data.meshes.new(skeleton_name + ' mesh')
        mesh.from_pydata(self.vertices, self.edges, [])
        mesh.update()
        skeleton = bpy.data.objects.new(skeleton_name, mesh)
        bpy.context.scene.objects.link(skeleton)
        return skeleton


def register():
    bpy.utils.register_class(SwcNeuronImporter)
    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(SwcNeuronImporter)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

def menu_func_import(self, context):
    self.layout.operator(SwcNeuronImporter.bl_idname, text="SWC Neuron (.swc)")

if __name__ == "__main__":
    register()
