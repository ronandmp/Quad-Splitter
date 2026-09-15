bl_info = {
    "name": "Quad Splitter",
    "author": "Ronan",
    "version": (3, 5, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar",
    "description": "Tools for creating topology transitions in quads and n-gons",
    "category": "Mesh",
}

from . import operators
from . import ui

modules = (
    operators,
    ui,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
