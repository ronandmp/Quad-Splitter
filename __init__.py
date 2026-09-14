bl_info = {
    "name": "Quad Splitter",
    "author": "Ronan",
    "version": (3, 4, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar",
    "description": "Ferramentas para criar transições de topologia em quads",
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
