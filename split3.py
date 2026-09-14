import bmesh

from bpy_extras import view3d_utils


# ============================================================
# SCREEN POSITION
# ============================================================

def get_vert_screen_position(context, vert):
    """
    Converte a posição 3D de um vértice
    para posição 2D na Viewport.
    """

    obj = context.active_object
    area = context.area

    if area is None or area.type != 'VIEW_3D':
        return None

    region = None

    for r in area.regions:
        if r.type == 'WINDOW':
            region = r
            break

    if region is None:
        return None

    rv3d = context.space_data.region_3d

    world_pos = obj.matrix_world @ vert.co

    screen_pos = view3d_utils.location_3d_to_region_2d(
        region,
        rv3d,
        world_pos
    )

    return screen_pos


# ============================================================
# FIND VISUAL CORNER
# ============================================================

def find_corner_vertex(face, corner, context):
    """
    Descobre qual vértice corresponde ao
    canto visual escolhido:

    TOP_LEFT
    TOP_RIGHT
    BOTTOM_LEFT
    BOTTOM_RIGHT
    """

    screen_verts = []

    for vert in face.verts:

        pos = get_vert_screen_position(
            context,
            vert
        )

        if pos is None:

            print(
                "SPLIT 3 ERRO: "
                "Não foi possível projetar vértice."
            )

            return None

        screen_verts.append(
            (
                vert,
                pos.x,
                pos.y
            )
        )


    # Centro visual
    center_x = sum(
        item[1]
        for item in screen_verts
    ) / len(screen_verts)

    center_y = sum(
        item[2]
        for item in screen_verts
    ) / len(screen_verts)


    # Direção desejada
    if corner == 'TOP_LEFT':

        target_x = -1
        target_y = 1


    elif corner == 'TOP_RIGHT':

        target_x = 1
        target_y = 1


    elif corner == 'BOTTOM_LEFT':

        target_x = -1
        target_y = -1


    elif corner == 'BOTTOM_RIGHT':

        target_x = 1
        target_y = -1


    else:

        print(
            "SPLIT 3 ERRO: "
            "Canto desconhecido."
        )

        return None


    # Escolher melhor vértice
    best_vert = None
    best_score = None


    for vert, x, y in screen_verts:

        dx = x - center_x
        dy = y - center_y

        score = (
            dx * target_x
            +
            dy * target_y
        )


        if (
            best_score is None
            or score > best_score
        ):
            best_score = score
            best_vert = vert


    return best_vert


# ============================================================
# FIND EDGE
# ============================================================

def find_edge_between(v1, v2):
    """
    Procura a aresta existente entre dois vértices.
    """

    for edge in v1.link_edges:

        if v2 in edge.verts:
            return edge

    return None


# ============================================================
# SPLIT 3
# ============================================================

def execute_split3(bm, face, corner, context):

    print("")
    print("================================")
    print("          SPLIT 3 REAL")
    print("================================")

    if len(face.verts) != 4:

        print("SPLIT 3 ERRO: Face não é Quad.")

        return False


    # --------------------------------------------------------
    # ENCONTRAR CANTO ESCOLHIDO
    # --------------------------------------------------------

    corner_vert = find_corner_vertex(
        face,
        corner,
        context
    )


    if corner_vert is None:

        print(
            "SPLIT 3 ERRO: "
            "Não foi possível encontrar o canto."
        )

        return False


    print(
        "Canto escolhido:",
        corner,
        "| Vert:",
        corner_vert.index
    )


    # --------------------------------------------------------
    # ORGANIZAR OS 4 VÉRTICES
    # --------------------------------------------------------

    verts = list(face.verts)

    try:

        index = verts.index(
            corner_vert
        )

    except ValueError:

        print(
            "SPLIT 3 ERRO: "
            "Vértice não pertence à face."
        )

        return False


    # Ordem ao redor do Quad:
    #
    # D = canto escolhido
    # A = vizinho 1
    # B = vértice oposto
    # C = vizinho 2
    #
    #
    # A -------- B
    # |          |
    # |          |
    # D -------- C
    #

    D = verts[index]

    A = verts[
        (index + 1) % 4
    ]

    B = verts[
        (index + 2) % 4
    ]

    C = verts[
        (index + 3) % 4
    ]


    print("D:", D.index)
    print("A:", A.index)
    print("B:", B.index)
    print("C:", C.index)


    # --------------------------------------------------------
    # LOCALIZAR AS DUAS ARESTAS QUE SERÃO DIVIDIDAS
    # --------------------------------------------------------

    edge_AB = find_edge_between(
        A,
        B
    )

    edge_BC = find_edge_between(
        B,
        C
    )


    if edge_AB is None:

        print(
            "SPLIT 3 ERRO: "
            "Aresta A-B não encontrada."
        )

        return False


    if edge_BC is None:

        print(
            "SPLIT 3 ERRO: "
            "Aresta B-C não encontrada."
        )

        return False


    #
    # --------------------------------------------------------
    # GUARDAR PROPRIEDADES DA FACE
    # --------------------------------------------------------

    material_index = face.material_index
    smooth = face.smooth

    # Guarda a normal original antes de remover a face
    original_normal = face.normal.copy()


    # Centro da face
    center = face.calc_center_median().copy()
    #


    # --------------------------------------------------------
    # REMOVER APENAS A FACE ORIGINAL
    # --------------------------------------------------------

    bm.faces.remove(face)


    # --------------------------------------------------------
    # DIVIDIR ARESTA A-B
    # --------------------------------------------------------

    _, E = bmesh.utils.edge_split(
        edge_AB,
        A,
        0.5
    )


    # --------------------------------------------------------
    # DIVIDIR ARESTA B-C
    # --------------------------------------------------------

    _, F = bmesh.utils.edge_split(
        edge_BC,
        B,
        0.5
    )


    print(
        "Novo E:",
        E.index
    )

    print(
        "Novo F:",
        F.index
    )


    # --------------------------------------------------------
    # CRIAR VÉRTICE CENTRAL G
    # --------------------------------------------------------

    G = bm.verts.new(
        center
    )


    print(
        "Novo G criado no centro."
    )


    # --------------------------------------------------------
    # CRIAR OS 3 QUADS
    # --------------------------------------------------------

    try:

        quad_1 = bm.faces.new(
            (
                D,
                A,
                E,
                G
            )
        )


        quad_2 = bm.faces.new(
            (
                E,
                B,
                F,
                G
            )
        )


        quad_3 = bm.faces.new(
            (
                D,
                G,
                F,
                C
            )
        )


    except Exception as error:

        print("")
        print("SPLIT 3 ERRO ao criar faces:")
        print(error)

        return False


    # --------------------------------------------------------
    # RESTAURAR PROPRIEDADES
    # --------------------------------------------------------

    #
    new_faces = (
        quad_1,
        quad_2,
        quad_3
    )


    for new_face in new_faces:

        # Atualiza a normal da nova face
        new_face.normal_update()

        # Se estiver invertida em relação à face original,
        # corrige a orientação
        if new_face.normal.dot(original_normal) < 0:
            new_face.normal_flip()

        # Restaura propriedades
        new_face.material_index = material_index
        new_face.smooth = smooth

        new_face.select = True
    #


    # --------------------------------------------------------
    # ATUALIZAR ÍNDICES
    # --------------------------------------------------------

    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()


    print("")
    print("--------------------------------")
    print("SPLIT 3 CONCLUÍDO")
    print("3 QUADS CRIADOS")
    print("--------------------------------")
    print("")


    return True


# ============================================================
# SPLIT 3 — N-GON DE 5 OU 6 VÉRTICES
# ============================================================

def execute_split3_pentagon(
    bm,
    face,
    corner,
    mode,
    context
):
    """Executa uma das duas soluções do Split 3 em pentágonos."""

    if len(face.verts) != 5:
        print("SPLIT 3 PENTÁGONO ERRO: face não possui 5 vértices.")
        return False

    corner_vert = find_corner_vertex(
        face,
        corner,
        context
    )

    if corner_vert is None:
        print("SPLIT 3 PENTÁGONO ERRO: canto não encontrado.")
        return False

    boundary = list(face.verts)
    corner_index = boundary.index(corner_vert)

    # Solução sem novos pontos na borda.
    if mode == 'TRIANGLE':
        return execute_split3_ngon(
            bm,
            face,
            corner_index
        )

    if mode != 'THREE_QUADS':
        print("SPLIT 3 PENTÁGONO ERRO: modo desconhecido.")
        return False

    original_center = face.calc_center_median().copy()

    # O canto mais distante representa o canto oposto
    # do quad original antes de receber o quinto vértice.
    opposite_vert = max(
        (
            vert for vert in boundary
            if vert is not corner_vert
        ),
        key=lambda vert: (
            vert.co - corner_vert.co
        ).length_squared
    )

    opposite_index = boundary.index(opposite_vert)
    forward_steps = (
        opposite_index - corner_index
    ) % 5

    # Um caminho possui 2 arestas e o outro possui 3.
    # O caminho maior já contém o quinto vértice;
    # dividimos a aresta junto ao oposto no caminho menor.
    if forward_steps == 2:
        split_loop_index = (
            opposite_index - 1
        ) % 5

    elif forward_steps == 3:
        split_loop_index = opposite_index

    else:
        print(
            "SPLIT 3 PENTÁGONO ERRO: "
            "não foi possível identificar o lado oposto."
        )
        return False

    split_edge = list(face.loops)[split_loop_index].edge

    bmesh.utils.edge_split(
        split_edge,
        split_edge.verts[0],
        0.5
    )

    prepared_boundary = list(face.verts)
    prepared_corner_index = prepared_boundary.index(
        corner_vert
    )

    print(
        "SPLIT 3 PENTÁGONO: "
        "um ponto médio adicionado para criar 3 quads."
    )

    return execute_split3_ngon(
        bm,
        face,
        prepared_corner_index,
        center_override=original_center
    )


def execute_split3_ngon(
    bm,
    face,
    option_index,
    center_override=None
):
    """
    Divide um pentágono ou hexágono em 3 faces.

    Pentágono: usa somente vértices existentes (2 quads + 1 triângulo).
    Hexágono: usa 3 vértices alternados sem criar pontos na borda.
    """

    vert_count = len(face.verts)

    if vert_count not in (5, 6):
        print("SPLIT 3 N-GON ERRO: esperado 5 ou 6 vértices.")
        return False

    material_index = face.material_index
    smooth = face.smooth
    original_normal = face.normal.copy()
    center = (
        center_override.copy()
        if center_override is not None
        else face.calc_center_median().copy()
    )
    boundary = list(face.verts)

    if vert_count == 5:
        start_index = option_index % 5

        print(
            "SPLIT 3 PENTÁGONO: padrão",
            start_index + 1,
            "— sem novos vértices na borda."
        )

    else:
        start_index = option_index % 2

        print(
            "SPLIT 3 HEXÁGONO: padrão",
            start_index + 1
        )

    ordered = [
        boundary[(start_index + offset) % vert_count]
        for offset in range(vert_count)
    ]

    spoke_a = ordered[0]
    middle_a = ordered[1]
    spoke_b = ordered[2]
    middle_b = ordered[3]
    spoke_c = ordered[4]

    bm.faces.remove(face)
    center_vert = bm.verts.new(center)

    try:
        first_face = bm.faces.new((
            spoke_a,
            middle_a,
            spoke_b,
            center_vert
        ))

        second_face = bm.faces.new((
            spoke_b,
            middle_b,
            spoke_c,
            center_vert
        ))

        if vert_count == 5:
            third_face = bm.faces.new((
                spoke_c,
                spoke_a,
                center_vert
            ))

        else:
            middle_c = ordered[5]
            third_face = bm.faces.new((
                spoke_c,
                middle_c,
                spoke_a,
                center_vert
            ))

        new_faces = (
            first_face,
            second_face,
            third_face
        )

    except Exception as error:
        print("SPLIT 3 N-GON ERRO ao criar faces:")
        print(error)
        return False

    for new_face in new_faces:
        new_face.normal_update()

        if new_face.normal.dot(original_normal) < 0:
            new_face.normal_flip()

        new_face.material_index = material_index
        new_face.smooth = smooth
        new_face.select = True

    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()

    if vert_count == 5:
        print("SPLIT 3 PENTÁGONO CONCLUÍDO: 2 quads + 1 triângulo.")
    else:
        print("SPLIT 3 HEXÁGONO CONCLUÍDO: 3 quads.")

    return True
