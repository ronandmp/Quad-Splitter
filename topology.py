import bmesh

from bpy_extras import view3d_utils


def get_edge_screen_direction(context, edge):
    """
    Retorna quanto a aresta é horizontal na tela.

    1.0 = totalmente horizontal
    0.0 = totalmente vertical
    """

    obj = context.active_object
    area = context.area

    if area is None or area.type != 'VIEW_3D':
        return None

    # Região principal da Viewport
    region = None

    for r in area.regions:
        if r.type == 'WINDOW':
            region = r
            break

    if region is None:
        return None

    rv3d = context.space_data.region_3d

    # Coordenadas locais -> mundo
    p1_world = obj.matrix_world @ edge.verts[0].co
    p2_world = obj.matrix_world @ edge.verts[1].co

    # Mundo -> tela
    p1 = view3d_utils.location_3d_to_region_2d(
        region,
        rv3d,
        p1_world
    )

    p2 = view3d_utils.location_3d_to_region_2d(
        region,
        rv3d,
        p2_world
    )

    if p1 is None or p2 is None:
        return None

    dx = abs(p2.x - p1.x)
    dy = abs(p2.y - p1.y)

    total = dx + dy

    if total == 0:
        return 0.5

    return dx / total


def _split_quad_legacy(bm, face, direction, context):

    print("=== TOPOLOGY.PY ===")

    if len(face.verts) != 4:
        print("ERRO: Face não é quad.")
        return False

    edges = list(face.edges)

    # Os dois pares possíveis de arestas opostas
    pair_a = (
        edges[0],
        edges[2]
    )

    pair_b = (
        edges[1],
        edges[3]
    )

    # Mede orientação dos pares na tela
    score_a = (
        get_edge_screen_direction(context, pair_a[0]) +
        get_edge_screen_direction(context, pair_a[1])
    ) / 2

    score_b = (
        get_edge_screen_direction(context, pair_b[0]) +
        get_edge_screen_direction(context, pair_b[1])
    ) / 2

    print("Pair A:", score_a)
    print("Pair B:", score_b)

    # Para criar uma linha VERTICAL,
    # precisamos cortar as arestas mais HORIZONTAIS.
    if direction == 'VERTICAL':

        if score_a > score_b:
            edge_a, edge_b = pair_a
        else:
            edge_a, edge_b = pair_b

    # Para criar uma linha HORIZONTAL,
    # cortamos as arestas mais VERTICAIS.
    else:

        if score_a < score_b:
            edge_a, edge_b = pair_a
        else:
            edge_a, edge_b = pair_b

    # Divide as duas arestas
    _, new_vert_a = bmesh.utils.edge_split(
        edge_a,
        edge_a.verts[0],
        0.5
    )

    _, new_vert_b = bmesh.utils.edge_split(
        edge_b,
        edge_b.verts[0],
        0.5
    )

    # Conecta os novos vértices
    try:

        bmesh.ops.connect_verts(
            bm,
            verts=[
                new_vert_a,
                new_vert_b
            ]
        )

    except Exception as e:

        print("ERRO ao conectar vértices:")
        print(e)

        return False

    print(
        f"OK: Quad dividido - {direction}"
    )

    print("===================")

    return True


def _connect_cut(bm, cut_verts):
    if cut_verts[0] is cut_verts[1]:
        print("ERRO: Os pontos do corte são iguais.")
        return False

    try:
        result = bmesh.ops.connect_verts(
            bm,
            verts=cut_verts
        )
    except Exception as error:
        print("ERRO ao conectar o corte:")
        print(error)
        return False

    if not result.get('edges'):
        print("ERRO: Nenhuma aresta foi criada.")
        return False

    return True


def _split_ngon_by_index(bm, face, start_index):
    """Corta um N-gon usando somente a ordem cíclica da borda."""

    loops = list(face.loops)
    vert_count = len(loops)
    start_index %= vert_count
    start_vert = loops[start_index].vert

    opposite_index = (
        start_index + vert_count // 2
    ) % vert_count
    opposite_vert = loops[opposite_index].vert
    cut_verts = [start_vert, opposite_vert]

    print(
        "N-GON:",
        start_vert.index,
        "→",
        opposite_vert.index
    )

    return _connect_cut(bm, cut_verts)


def split_quad(
    bm,
    face,
    direction,
    context,
    start_index=-1
):
    """Entrada comum do Split H/V para quads e N-gons."""

    if len(face.verts) == 4:
        return _split_quad_legacy(
            bm,
            face,
            direction,
            context
        )

    if start_index < 0:
        start_index = (
            0 if direction == 'HORIZONTAL' else 1
        )

    return _split_ngon_by_index(
        bm,
        face,
        start_index
    )
