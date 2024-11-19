import bpy
import os
import json
from datetime import datetime

# Define the base export folder path
base_export_folder = "C:/Users/soubr/OneDrive/Documents/NSI/Projet2/exports"

# Generate a timestamp for the export folder
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
export_folder = os.path.join(base_export_folder, f"export-{timestamp}")

# Ensure the export folder and its assets subfolder exist
assets_folder = os.path.join(export_folder, "assets")
if not os.path.exists(assets_folder):
    os.makedirs(assets_folder)

def save_texture_as_jpg_with_render(image, export_path):
    """
    Saves the texture image as a JPG file in the specified path.
    """
    if image:
        bpy.context.scene.render.image_settings.file_format = 'JPEG' 
        image.save_render(filepath=export_path)
        print(f"Saved texture as {export_path}")
        return os.path.relpath(export_path, export_folder).replace("\\", "/")
    return None

def export_object(obj):
    """
    Exports the given object and gathers its metadata.
    """
    # Create a folder for the object within the assets folder
    object_folder = os.path.join(assets_folder, obj.name)
    if not os.path.exists(object_folder):
        os.makedirs(object_folder)

    # Export the texture if available
    texture_path = None
    for mat in obj.data.materials:
        if mat and mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    texture_path = os.path.join(object_folder, "texture.jpg")
                    texture_path = save_texture_as_jpg_with_render(node.image, texture_path)
                    break
            if texture_path:
                break

    # Export the model as FBX
    model_path = os.path.join(object_folder, "model.fbx")
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    bpy.ops.export_scene.fbx(
        filepath=model_path,
        use_selection=True,  
        embed_textures=False,
        path_mode='AUTO'
    )
    model_path = os.path.relpath(model_path, export_folder).replace("\\", "/")
    print(f"Exported {obj.name} to {model_path} with texture {texture_path if texture_path else 'None'}")

    # Collect metadata
    metadata = {
        "model_path": model_path,
        "texture_path": texture_path if texture_path else None,
        "position": [obj.location.x, obj.location.y, obj.location.z],
        "size": [obj.dimensions.x, obj.dimensions.y, obj.dimensions.z],
        "orientation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
        "name": obj.name
    }
    return metadata

def export_all():
    """
    Exports all mesh objects in the scene and generates metadata.
    """
    metadata_list = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            metadata = export_object(obj)
            metadata_list.append(metadata)

    # Save metadata to data.json
    data_file = os.path.join(export_folder, "data.json")
    with open(data_file, "w") as json_file:
        json.dump(metadata_list, json_file, indent=2)
    print(f"Saved metadata to {data_file}")

# Execute the export process
export_all()