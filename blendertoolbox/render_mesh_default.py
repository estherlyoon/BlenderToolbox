import os, bpy
import bmesh
import numpy as np
from mathutils import Vector, kdtree
import time

from . blenderInit import blenderInit
from . readMesh import readMesh
from . readNumpyMesh import readNumpyMesh
from . subdivision import subdivision
from . setMat_plastic import setMat_plastic
from . invisibleGround import invisibleGround
from . setCamera import setCamera
from . setLight_sun import setLight_sun
from . setLight_ambient import setLight_ambient
from . shadowThreshold import shadowThreshold
from . renderImage import renderImage

class colorObj(object):
    def __init__(self, RGBA, \
    H = 0.5, S = 1.0, V = 1.0,\
    B = 0.0, C = 0.0):
        self.H = H # hue
        self.S = S # saturation
        self.V = V # value
        self.RGBA = RGBA
        self.B = B # birghtness
        self.C = C # contrast

def merge_close_vertices(obj, threshold=0.01):
    """
    Merge vertices that are closer than the specified threshold.

    Parameters:
    obj (bpy.types.Object): The mesh object to work on.
    threshold (float): The distance within which to merge vertices.
    """

    if obj.type != 'MESH':
        raise ValueError("Provided object is not a mesh")

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    # Build KDTree
    kd = kdtree.KDTree(len(bm.verts))
    for i, v in enumerate(bm.verts):
        kd.insert(v.co, i)
    kd.balance()

    # Collect groups of close vertices
    merge_groups = []
    processed = set()
    for v in bm.verts:
        if v.index not in processed:
            close_indices = set(idx for co, idx, dist in kd.find_range(v.co, threshold) if idx != v.index)
            close_indices.add(v.index)
            processed.update(close_indices)
            if len(close_indices) > 1:
                merge_groups.append([bm.verts[i] for i in close_indices])

    # Merge groups of vertices
    for group in merge_groups:
        if all(v.is_valid for v in group):
            # Calculate center point of the group
            center = sum((v.co for v in group), Vector()) / len(group)
            # print("merging nPoint:", len(group))
            bmesh.ops.pointmerge(bm, verts=group, merge_co=center)

    bm.normal_update()
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

def set_hair_shader(obj):
    bpy.context.view_layer.objects.active = obj

    mat = bpy.data.materials.new(name="HairMaterial")
    mat.use_nodes = True
    for node in mat.node_tree.nodes:
        if node.type != 'OUTPUT_MATERIAL':
            mat.node_tree.nodes.remove(node)
        else:
            print("not removing output material node")

    shader_node = mat.node_tree.nodes.new('ShaderNodeBsdfHairPrincipled')

    output_node = mat.node_tree.nodes.get('Material Output')
    mat.node_tree.links.new(shader_node.outputs['BSDF'], output_node.inputs['Surface'])

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def print_elapsed(start, msg):
    end = time.time()
    elapsed_time = end - start
    print(msg, ":", elapsed_time)

def render_mesh_default(args):
  ## initialize blender
  imgRes_x = args["image_resolution"][0]
  imgRes_y = args["image_resolution"][1]
  numSamples = args["number_of_samples"]
  exposure = 1.5 
  use_GPU = True
  blenderInit(imgRes_x, imgRes_y, numSamples, exposure, use_GPU)

  ## read mesh
  location = args["mesh_position"]
  rotation = args["mesh_rotation"]
  scale = args["mesh_scale"]
  head_path = args["head_path"]
  head_mesh = readMesh(head_path, args["head_position"], args["head_rotation"], args["head_scale"])

  if "mesh_path" in args:
    meshPath = args["mesh_path"]
    mesh = readMesh(meshPath, location, rotation, scale)
  elif "mesh_path" not in args and "vertices" in args and "faces" in args:
    V = args["vertices"]
    F = args["faces"]
    mesh = readNumpyMesh(V,F,location,rotation,scale)
  else:
    raise ValueError("one should provide either [mesh_path] or [verticesfaces] in the args")   

  start = time.time()
  # Set shading to smooth
  # mesh.data.use_auto_smooth = True
  # # Set the angle threshold for auto-smooth
  # mesh.data.auto_smooth_angle = 60.0
  #
  # head_mesh.data.use_auto_smooth = True
  # head_mesh.data.auto_smooth_angle = 60.0
  #
  bpy.ops.object.shade_smooth() 
  print_elapsed(start, "Smooth")

  ## Merging
  start = time.time()
  # merge_close_vertices(mesh, 0.005)
  print_elapsed(start, "Merge")

  ## Hair shader
  start = time.time()
  set_hair_shader(mesh)
  print_elapsed(start, "Shade")

  ## subdivision
  start = time.time()
  subdivision(mesh, level = args["subdivision_iteration"])
  subdivision(head_mesh, level = args["subdivision_iteration"])
  print_elapsed(start, "Subdivision")

  ## set invisible plane (shadow catcher)
  # invisibleGround(shadowBrightness=0.9)

  ## set camera 
  start = time.time()
  camLocation = (3, 0, 2)
  lookAtLocation = (0,0,0.5)
  focalLength = 45 # (UI: click camera > Object Data > Focal Length)
  cam = setCamera(camLocation, lookAtLocation, focalLength)

  ## set light
  lightAngle = args["light_angle"]
  strength = 2
  shadowSoftness = 0.3
  sun = setLight_sun(lightAngle, strength, shadowSoftness)

  ## default render as plastic
  RGB = args["mesh_RGB"]
  RGBA = (RGB[0], RGB[1], RGB[2], 1)
  meshColor = colorObj(RGBA, 0.5, 1.0, 1.0, 0.0, 2.0)
  setMat_plastic(head_mesh, meshColor)

  ## set ambient light
  setLight_ambient(color=(0.1,0.1,0.1,1)) 

  ## set gray shadow to completely white with a threshold (optional but recommended)
  shadowThreshold(alphaThreshold = 0.05, interpolationMode = 'CARDINAL')

  print_elapsed(start, "Set camera, light, and shadow")

  ## save blender file so that you can adjust parameters in the UI
  start = time.time()
  bpy.ops.wm.save_mainfile(filepath=os.getcwd() + '/test.blend')
  print_elapsed(start, "Save blender file")

  ## save rendering
  start = time.time()
  renderImage(args["output_path"], cam)
  print_elapsed(start, "Render image")
