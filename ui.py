import bpy
import bmesh
import os
import bpy.utils.previews

from . import splitroll


preview_collections = {}


class VIEW3D_PT_quad_splitter(bpy.types.Panel):
    bl_label = "Quad Splitter"
    bl_idname = "VIEW3D_PT_quad_splitter"

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Quad Splitter"


    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'EDIT_MESH'
            and context.active_object is not None
            and context.active_object.type == 'MESH'
        )


    def draw(self, context):
        layout = self.layout

        selected_face = None
        bm = None
        obj = context.active_object

        if obj is not None and context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(obj.data)
            selected_faces = [
                face for face in bm.faces
                if face.select
            ]

            if len(selected_faces) == 1:
                selected_face = selected_faces[0]

        # =========================
        # SPLIT BÁSICO
        # =========================

        if (
            selected_face is not None
            and len(selected_face.verts) > 4
        ):
            vert_count = len(selected_face.verts)
            option_count = (
                vert_count // 2
                if vert_count % 2 == 0
                else vert_count
            )

            layout.label(
                text=f"N-gon: {vert_count} vértices"
            )

            row = None

            for index in range(option_count):
                if index % 5 == 0:
                    row = layout.row(align=True)

                op = row.operator(
                    "mesh.split_quad",
                    text=str(index + 1)
                )
                op.start_index = index

        else:
            row = layout.row(align=True)

            op = row.operator(
                "mesh.split_quad",
                text="Split H"
            )
            op.direction = 'HORIZONTAL'

            op = row.operator(
                "mesh.split_quad",
                text="Split V"
            )
            op.direction = 'VERTICAL'


        layout.separator()


        # =========================
        # SPLIT 3
        # =========================

        layout.label(text="Split 3")

        icons = preview_collections.get("main")

        def split3_icon(name):
            if icons is None or name not in icons:
                return 0

            return icons[name].icon_id


        split3_vert_count = (
            len(selected_face.verts)
            if selected_face is not None
            else 4
        )

        if split3_vert_count == 4:
            # Quatro cantos alinhados
            row = layout.row(align=True)
            row.scale_y = 2.1

            op = row.operator(
                "mesh.split_3",
                text="",
                icon_value=split3_icon("split3_top_left")
            )
            op.corner = 'TOP_LEFT'

            op = row.operator(
                "mesh.split_3",
                text="",
                icon_value=split3_icon("split3_top_right")
            )
            op.corner = 'TOP_RIGHT'

            op = row.operator(
                "mesh.split_3",
                text="",
                icon_value=split3_icon("split3_bottom_left")
            )
            op.corner = 'BOTTOM_LEFT'

            op = row.operator(
                "mesh.split_3",
                text="",
                icon_value=split3_icon("split3_bottom_right")
            )
            op.corner = 'BOTTOM_RIGHT'

        elif split3_vert_count == 5:
            corner_buttons = (
                ('split3_top_left', 'TOP_LEFT'),
                ('split3_top_right', 'TOP_RIGHT'),
                ('split3_bottom_left', 'BOTTOM_LEFT'),
                ('split3_bottom_right', 'BOTTOM_RIGHT'),
            )

            box = layout.box()
            box.label(text="3 Quads")
            box.label(
                text="Adds one midpoint",
                icon='INFO'
            )
            row = box.row(align=True)
            row.scale_y = 2.1

            for icon_name, corner in corner_buttons:
                op = row.operator(
                    "mesh.split_3",
                    text="",
                    icon_value=split3_icon(icon_name)
                )
                op.corner = corner
                op.mode = 'THREE_QUADS'

            box = layout.box()
            box.label(text="2 Quads + Triangle")
            box.label(
                text="Uses existing vertices",
                icon='INFO'
            )
            row = box.row(align=True)
            row.scale_y = 2.1

            for icon_name, corner in corner_buttons:
                op = row.operator(
                    "mesh.split_3",
                    text="",
                    icon_value=split3_icon(icon_name)
                )
                op.corner = corner
                op.mode = 'TRIANGLE'

        elif split3_vert_count == 6:
            row = layout.row(align=True)

            for index in range(2):
                op = row.operator(
                    "mesh.split_3",
                    text=f"Padrão {index + 1}"
                )
                op.start_index = index

        else:
            row = layout.row()
            row.enabled = False
            row.label(text="Disponível para 4, 5 ou 6 vértices")

        layout.separator()

        # =========================
        # SPLIT ROLL
        # =========================

        layout.separator()

        layout.label(text="Split Roll")

        roll_buttons = (
            splitroll.get_roll_visual_config(bm, context)
            if bm is not None
            else None
        )

        if roll_buttons is None:
            roll_buttons = (
                ('roll_horizontal_top', 'SIDE_A'),
                ('roll_horizontal_bottom', 'SIDE_B'),
            )

        # operator() mantém o desenho do ícone no tamanho padrão.
        # O cartão usa template_icon para exibir a arte em escala real,
        # mantendo o comando imediatamente abaixo dela.
        row = layout.row(align=True)

        for icon_name, side in roll_buttons:
            card = row.box()
            column = card.column(align=True)
            icon_value = split3_icon(icon_name)

            if icon_value:
                column.template_icon(
                    icon_value=icon_value,
                    scale=3.2
                )

            op = column.operator(
                "mesh.split_roll",
                text="Cortar"
            )
            op.side = side





classes = (
    VIEW3D_PT_quad_splitter,
)


def register():
    icons = bpy.utils.previews.new()
    icons_dir = os.path.join(
        os.path.dirname(__file__),
        "icons"
    )

    for name in (
        "split3_top_left",
        "split3_top_right",
        "split3_bottom_left",
        "split3_bottom_right",
        "roll_horizontal_top",
        "roll_horizontal_bottom",
        "roll_vertical_left",
        "roll_vertical_right",
    ):
        icons.load(
            name,
            os.path.join(icons_dir, name + ".png"),
            'IMAGE'
        )

    preview_collections["main"] = icons

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    for icons in preview_collections.values():
        bpy.utils.previews.remove(icons)

    preview_collections.clear()
