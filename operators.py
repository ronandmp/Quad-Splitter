import bpy
import bmesh

from bpy.props import EnumProperty, IntProperty

from . import topology
from . import split3
from . import splitroll

class MESH_OT_split_quad(bpy.types.Operator):
    bl_idname = "mesh.split_quad"
    bl_label = "Split Quad"
    bl_description = "Split selected quad"

    direction: EnumProperty(
        name="Direction",
        items=[
            ('HORIZONTAL', "Horizontal", ""),
            ('VERTICAL', "Vertical", ""),
        ],
        default='HORIZONTAL'
    )

    start_index: IntProperty(
        name="Start Index",
        default=-1,
        min=-1
    )

    def execute(self, context):

        obj = context.active_object

        # Verifica objeto
        if obj is None or obj.type != 'MESH':
            print("ERRO: Nenhuma malha válida selecionada.")
            self.report({'ERROR'}, "Selecione uma malha.")
            return {'CANCELLED'}

        # Verifica Edit Mode
        if context.mode != 'EDIT_MESH':
            print("ERRO: Não está em Edit Mode.")
            self.report({'ERROR'}, "Entre no Edit Mode.")
            return {'CANCELLED'}

        # BMesh
        bm = bmesh.from_edit_mesh(obj.data)

        # Faces selecionadas
        selected_faces = [
            face for face in bm.faces
            if face.select
        ]

        # Exatamente uma face
        if len(selected_faces) != 1:
            print(
                f"ERRO: {len(selected_faces)} faces selecionadas."
            )

            self.report(
                {'WARNING'},
                "Selecione exatamente 1 face."
            )

            return {'CANCELLED'}

        face = selected_faces[0]

        # Split H/V trabalha com Quad ou N-gon.
        if len(face.verts) < 4:
            print(
                f"ERRO: Face possui {len(face.verts)} vértices."
            )

            self.report(
                {'WARNING'},
                "A face precisa ser um Quad ou N-gon."
            )

            return {'CANCELLED'}

        print("OK: Quad válido!")
        print("Direção:", self.direction)

        # Envia para topology.py
        result = topology.split_quad(
            bm,
            face,
            self.direction,
            context,
            self.start_index
        )

        if not result:
            print("ERRO: topology.py não conseguiu processar.")
            return {'CANCELLED'}

        # Atualiza a malha
        bmesh.update_edit_mesh(obj.data)

        print("OK: topology.py processou o quad.")

        return {'FINISHED'}

class MESH_OT_split_3(bpy.types.Operator):
    bl_idname = "mesh.split_3"
    bl_label = "Split 3"
    bl_description = "Create a three-way quad split"

    corner: EnumProperty(
        name="Corner",
        items=[
            ('TOP_LEFT', "Top Left", ""),
            ('TOP_RIGHT', "Top Right", ""),
            ('BOTTOM_LEFT', "Bottom Left", ""),
            ('BOTTOM_RIGHT', "Bottom Right", ""),
        ],
        default='TOP_LEFT'
    )

    start_index: IntProperty(
        name="Start Index",
        default=-1,
        min=-1
    )

    mode: EnumProperty(
        name="Mode",
        items=(
            (
                'THREE_QUADS',
                '3 Quads',
                'Add one midpoint and create three quads'
            ),
            (
                'TRIANGLE',
                '2 Quads + Triangle',
                'Use existing boundary vertices without adding a midpoint'
            ),
        ),
        default='THREE_QUADS'
    )


    def execute(self, context):

        obj = context.active_object

        # Verifica objeto
        if obj is None or obj.type != 'MESH':
            print("SPLIT 3 ERRO: Nenhuma malha válida.")
            self.report({'ERROR'}, "Selecione uma malha.")
            return {'CANCELLED'}

        # Verifica Edit Mode
        if context.mode != 'EDIT_MESH':
            print("SPLIT 3 ERRO: Não está em Edit Mode.")
            self.report({'ERROR'}, "Entre no Edit Mode.")
            return {'CANCELLED'}

        # BMesh
        bm = bmesh.from_edit_mesh(obj.data)

        # Faces selecionadas
        selected_faces = [
            face for face in bm.faces
            if face.select
        ]

        # Exatamente uma face
        if len(selected_faces) != 1:

            print(
                f"SPLIT 3 ERRO: "
                f"{len(selected_faces)} faces selecionadas."
            )

            self.report(
                {'WARNING'},
                "Selecione exatamente 1 face."
            )

            return {'CANCELLED'}

        face = selected_faces[0]

        vert_count = len(face.verts)

        # Split 3 trabalha somente com 4, 5 ou 6 vértices.
        if vert_count < 4 or vert_count > 6:

            print(
                f"SPLIT 3 ERRO: "
                f"Face possui {len(face.verts)} vértices."
            )

            self.report(
                {'WARNING'},
                "O Split 3 aceita faces com 4, 5 ou 6 vértices."
            )

            return {'CANCELLED'}


        print("==============================")
        print("SPLIT 3")
        print("Canto:", self.corner)
        print("==============================")


        # Quad mantém o algoritmo visual já aprovado.
        if vert_count == 4:
            result = split3.execute_split3(
                bm,
                face,
                self.corner,
                context
            )

        elif vert_count == 5:
            result = split3.execute_split3_pentagon(
                bm,
                face,
                self.corner,
                self.mode,
                context
            )

        # Hexágono usa os dois padrões alternados.
        else:
            result = split3.execute_split3_ngon(
                bm,
                face,
                self.start_index
            )


        if not result:
            print("SPLIT 3 ERRO: operação cancelada.")
            return {'CANCELLED'}


        # Atualiza malha
        bmesh.update_edit_mesh(obj.data)

        print("SPLIT 3: operação concluída.")

        return {'FINISHED'}

###
class MESH_OT_split_roll(bpy.types.Operator):
    bl_idname = "mesh.split_roll"
    bl_label = "Split Roll"
    bl_description = "Split a straight chain with optional pentagons at its ends"

    side: EnumProperty(
        name="Side",
        items=(
            ('SIDE_A', 'Side A', ''),
            ('SIDE_B', 'Side B', ''),
        ),
        default='SIDE_A'
    )

    def execute(self, context):

        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report(
                {'ERROR'},
                "Selecione uma malha."
            )
            return {'CANCELLED'}

        if context.mode != 'EDIT_MESH':
            self.report(
                {'ERROR'},
                "Entre no Edit Mode."
            )
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(
            obj.data
        )

        result = splitroll.execute_split_roll(
            bm,
            context,
            self.side
        )

        if not result:

            self.report(
                {'WARNING'},
                "Split Roll cancelado."
            )

            return {'CANCELLED'}

        bmesh.update_edit_mesh(
            obj.data
        )

        return {'FINISHED'}
###

classes = (
    MESH_OT_split_quad,
    MESH_OT_split_3,
    MESH_OT_split_roll,
)


def get_start_corner_from_side(
    first_face,
    second_face,
    side
):
    """
    Escolhe um dos dois cantos externos
    da primeira face.

    Não usa Viewport.
    Usa apenas a topologia.
    """

    shared_edge = get_shared_edge(
        first_face,
        second_face
    )


    if shared_edge is None:

        print(
            "ROLL ERRO: "
            "Aresta compartilhada inicial "
            "não encontrada."
        )

        return None


    # Os dois vértices que NÃO estão
    # na aresta compartilhada são
    # os dois possíveis cantos iniciais.

    outer_verts = [
        vert
        for vert in first_face.verts
        if vert not in shared_edge.verts
    ]


    if len(outer_verts) != 2:

        print(
            "ROLL ERRO: "
            "Não foi possível identificar "
            "os dois lados da primeira face."
        )

        return None


    if side == 'SIDE_A':

        return outer_verts[0]


    if side == 'SIDE_B':

        return outer_verts[1]


    print(
        "ROLL ERRO: "
        "Side desconhecido."
    )

    return None


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
