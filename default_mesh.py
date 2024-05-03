import blendertoolbox as bt

'''
RENDER A MESH STEP-BY-STEP:
1. run "python default_mesh.py" in terminal, then terminate the code when it starts rendering. This step outputs a "test.blend"
2. open "test.blend" with your blender software
3. in blender UI, adjust:
    - "mesh_location", "mesh_rotation", "mesh_scale" of the mesh
4. type in the adjusted mesh parameters from UI to "default_mesh.py"
5. run "python default_mesh.py" again (wait a couple minutes) to output your final image
'''

arguments = {
  "output_path": "hair_mesh.png",
  "image_resolution": [720, 720], # recommend >1080 for paper figures
  "number_of_samples": 100, # recommend >200 for paper figures
  "mesh_path": "mesh.obj", # either .ply or .obj
  "mesh_position": (-0.75, 0, 0.44), # UI: click mesh > Transform > Location
  "mesh_rotation": (103, 1, 256), # UI: click mesh > Transform > Rotation
  "mesh_scale": (0.86,0.86,0.86), # UI: click mesh > Transform > Scale
  "shading": "smooth", # either "flat" or "smooth"
  "subdivision_iteration": 0, # integer
  "mesh_RGB": [144.0/255, 210.0/255, 236.0/255], # mesh RGB
  "light_angle": (6, -30, -155) # UI: click Sun > Transform > Rotation
}
bt.render_mesh_default(arguments)
