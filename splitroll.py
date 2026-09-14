import bmesh

from . import split3


# ============================================================
# SELEÇÃO
# ============================================================

def get_selected_quad_faces(bm):

    faces = [
        face
        for face in bm.faces
        if face.select
    ]

    if len(faces) < 2:
        print("ROLL ERRO: Selecione pelo menos 2 quads.")
        return None

    for face in faces:

        if len(face.verts) not in (4, 5):

            print(
                f"ROLL ERRO: Face {face.index} "
                f"possui {len(face.verts)} lados."
            )

            print(
                "ROLL ERRO: Apenas quads e pentágonos nas pontas são permitidos."
            )

            return None

    return faces


def validate_chain_face_types(chain):
    """Permite pentágonos somente nas duas extremidades."""

    for index, face in enumerate(chain):
        is_endpoint = index == 0 or index == len(chain) - 1
        vert_count = len(face.verts)

        if is_endpoint and vert_count in (4, 5):
            continue

        if not is_endpoint and vert_count == 4:
            continue

        print(
            f"ROLL ERRO: Face {face.index} com {vert_count} lados "
            "não é válida nesta posição."
        )
        return False

    return True


# ============================================================
# VIZINHANÇA
# ============================================================

def get_selected_neighbors(face, selected_set):

    neighbors = []

    for edge in face.edges:

        for linked_face in edge.link_faces:

            if (
                linked_face is not face
                and linked_face in selected_set
                and linked_face not in neighbors
            ):
                neighbors.append(linked_face)

    return neighbors


def get_shared_edge(face_a, face_b):

    for edge in face_a.edges:

        if face_b in edge.link_faces:
            return edge

    return None


def find_edge_between(v1, v2):

    for edge in v1.link_edges:

        if v2 in edge.verts:
            return edge

    return None


def get_outer_choice_verts(
    chain,
    shared_edge,
    context
):
    """Retorna os dois cantos externos usados pelos botões do Roll."""

    outer_verts = [
        vert for vert in chain[0].verts
        if vert not in shared_edge.verts
    ]

    if len(outer_verts) == 2:
        return outer_verts

    if len(outer_verts) != 3:
        return None

    first_positions = [
        split3.get_vert_screen_position(context, vert)
        for vert in chain[0].verts
    ]
    last_positions = [
        split3.get_vert_screen_position(context, vert)
        for vert in chain[-1].verts
    ]
    outer_positions = {
        vert: split3.get_vert_screen_position(context, vert)
        for vert in outer_verts
    }

    if (
        any(pos is None for pos in first_positions)
        or any(pos is None for pos in last_positions)
        or any(pos is None for pos in outer_positions.values())
    ):
        return None

    first_x = sum(pos.x for pos in first_positions) / len(first_positions)
    first_y = sum(pos.y for pos in first_positions) / len(first_positions)
    last_x = sum(pos.x for pos in last_positions) / len(last_positions)
    last_y = sum(pos.y for pos in last_positions) / len(last_positions)

    if abs(last_x - first_x) >= abs(last_y - first_y):
        ordered = sorted(
            outer_verts,
            key=lambda vert: outer_positions[vert].y
        )
        return [ordered[-1], ordered[0]]

    ordered = sorted(
        outer_verts,
        key=lambda vert: outer_positions[vert].x
    )
    return [ordered[0], ordered[-1]]


# ============================================================
# CONFIGURAÇÃO VISUAL DO PAINEL
# ============================================================

def get_roll_visual_config(bm, context):
    """Detecta a orientação visual sem alterar a lógica do corte."""

    selected_faces = [
        face for face in bm.faces
        if face.select and len(face.verts) in (4, 5)
    ]

    if len(selected_faces) < 2:
        return None

    selected_set = set(selected_faces)
    neighbor_map = {
        face: get_selected_neighbors(face, selected_set)
        for face in selected_faces
    }
    endpoints = [
        face for face in selected_faces
        if len(neighbor_map[face]) == 1
    ]

    if len(endpoints) != 2:
        return None

    chain = []
    previous = None
    current = endpoints[0]

    while current is not None:
        chain.append(current)
        next_faces = [
            face for face in neighbor_map[current]
            if face is not previous
        ]

        if not next_faces:
            break

        if len(next_faces) != 1:
            return None

        previous, current = current, next_faces[0]

        if current in chain:
            return None

    if len(chain) != len(selected_faces):
        return None

    if chain[0].index > chain[-1].index:
        chain.reverse()

    if not validate_chain_face_types(chain):
        return None

    first_shared = get_shared_edge(chain[0], chain[1])

    if first_shared is None:
        return None

    outer_verts = get_outer_choice_verts(
        chain,
        first_shared,
        context
    )

    if outer_verts is None:
        return None

    first_positions = [
        split3.get_vert_screen_position(context, vert)
        for vert in chain[0].verts
    ]
    last_positions = [
        split3.get_vert_screen_position(context, vert)
        for vert in chain[-1].verts
    ]
    outer_positions = {
        vert: split3.get_vert_screen_position(context, vert)
        for vert in outer_verts
    }

    if (
        any(pos is None for pos in first_positions)
        or any(pos is None for pos in last_positions)
        or any(pos is None for pos in outer_positions.values())
    ):
        return None

    first_x = sum(pos.x for pos in first_positions) / len(first_positions)
    first_y = sum(pos.y for pos in first_positions) / len(first_positions)
    last_x = sum(pos.x for pos in last_positions) / len(last_positions)
    last_y = sum(pos.y for pos in last_positions) / len(last_positions)

    side_by_vert = {
        outer_verts[0]: 'SIDE_A',
        outer_verts[1]: 'SIDE_B'
    }

    if abs(last_x - first_x) >= abs(last_y - first_y):
        ordered = sorted(
            outer_verts,
            key=lambda vert: outer_positions[vert].y,
            reverse=True
        )

        return (
            ('roll_horizontal_top', side_by_vert[ordered[0]]),
            ('roll_horizontal_bottom', side_by_vert[ordered[1]]),
        )

    ordered = sorted(
        outer_verts,
        key=lambda vert: outer_positions[vert].x
    )

    return (
        ('roll_vertical_left', side_by_vert[ordered[0]]),
        ('roll_vertical_right', side_by_vert[ordered[1]]),
    )


# ============================================================
# CONSTRUIR CADEIA
# ============================================================

def build_face_chain(selected_faces):

    selected_set = set(selected_faces)

    neighbor_map = {}
    endpoints = []

    for face in selected_faces:

        neighbors = get_selected_neighbors(
            face,
            selected_set
        )

        neighbor_map[face] = neighbors

        count = len(neighbors)

        print(
            f"Face {face.index} "
            f"→ {count} vizinho(s)"
        )

        if count == 1:

            endpoints.append(face)

        elif count == 2:

            pass

        else:

            print(
                f"ROLL ERRO: Face {face.index} "
                f"possui {count} vizinhos."
            )

            return None


    if len(endpoints) != 2:

        print(
            "ROLL ERRO: "
            f"Foram encontradas "
            f"{len(endpoints)} extremidades."
        )

        return None


    chain = []

    previous = None
    current = endpoints[0]


    while current is not None:

        chain.append(current)

        next_faces = [
            face
            for face in neighbor_map[current]
            if face is not previous
        ]


        if len(next_faces) == 0:
            break


        if len(next_faces) > 1:

            print(
                "ROLL ERRO: Caminho ambíguo."
            )

            return None


        next_face = next_faces[0]

        previous = current
        current = next_face


        if current in chain:

            print(
                "ROLL ERRO: Loop detectado."
            )

            return None


    if len(chain) != len(selected_faces):

        print(
            "ROLL ERRO: "
            "A seleção não forma "
            "uma única cadeia."
        )

        return None


    return chain


# ============================================================
# CURVA / RETA
# ============================================================

def are_edges_opposite_in_quad(
    face,
    edge_a,
    edge_b
):

    verts_a = set(edge_a.verts)
    verts_b = set(edge_b.verts)

    shared = verts_a.intersection(
        verts_b
    )

    return len(shared) == 0


def validate_roll_path(chain):

    if len(chain) == 2:

        print(
            "ROLL: 2 quads → "
            "nenhum intermediário."
        )

        return True


    for i in range(
        1,
        len(chain) - 1
    ):

        previous_face = chain[i - 1]
        current_face = chain[i]
        next_face = chain[i + 1]


        entry_edge = get_shared_edge(
            current_face,
            previous_face
        )

        exit_edge = get_shared_edge(
            current_face,
            next_face
        )


        if (
            entry_edge is None
            or exit_edge is None
        ):

            print(
                "ROLL ERRO: "
                "Aresta compartilhada não encontrada."
            )

            return False


        if not are_edges_opposite_in_quad(
            current_face,
            entry_edge,
            exit_edge
        ):

            print(
                f"Face {current_face.index} "
                "→ TURN ❌"
            )

            print("")
            print("SPLIT ROLL CANCELADO")
            print("Curva detectada na sequência.")

            return False


        print(
            f"Face {current_face.index} "
            "→ STRAIGHT ✅"
        )


    return True


# ============================================================
# ORDENAR PELO QUAD ATIVO
# ============================================================

def orient_chain_from_active(
    bm,
    chain
):
    """
    Orienta a cadeia de forma determinística.

    A face ativa e a ordem de seleção
    NÃO interferem no Split Roll.
    """

    if len(chain) < 2:
        return chain

    # Sempre começa pela extremidade
    # com menor índice de face.
    if chain[0].index > chain[-1].index:
        chain = list(reversed(chain))

    return chain

    active_face = bm.faces.active


    if active_face is None:

        print(
            "ROLL ERRO: "
            "Nenhuma face ativa."
        )

        return None


    if active_face is chain[0]:

        return chain


    if active_face is chain[-1]:

        chain.reverse()

        return chain


    print(
        "ROLL ERRO: "
        "A face ativa precisa ser "
        "uma das extremidades."
    )

    print(
        "Selecione por último "
        "o quad onde o Roll deve começar."
    )

    return None


# ============================================================
# TRACE SIDE
# ============================================================

def find_connected_vert_in_edge(
    face,
    source_vert,
    target_edge
):

    for candidate in target_edge.verts:

        edge = find_edge_between(
            source_vert,
            candidate
        )

        if (
            edge is not None
            and face in edge.link_faces
        ):
            return candidate

    return None


def calculate_end_corner(
    chain,
    start_corner
):

    # Primeira aresta compartilhada
    first_shared = get_shared_edge(
        chain[0],
        chain[1]
    )


    # O canto inicial NÃO pode estar
    # sobre a aresta compartilhada.

    if start_corner in first_shared.verts:

        print("")
        print(
            "ROLL ERRO: "
            "Esse canto não é compatível "
            "com a direção da cadeia."
        )

        return None


    # Descobre qual ponta da aresta
    # compartilhada pertence ao mesmo
    # lado do canto inicial.

    side_vert = find_connected_vert_in_edge(
        chain[0],
        start_corner,
        first_shared
    )


    if side_vert is None:

        print(
            "ROLL ERRO: "
            "Não foi possível determinar "
            "o lado inicial."
        )

        return None


    # Percorre todos os intermediários
    # seguindo a mesma lateral da faixa.

    for i in range(
        1,
        len(chain) - 1
    ):

        face = chain[i]

        exit_edge = get_shared_edge(
            face,
            chain[i + 1]
        )


        next_side = find_connected_vert_in_edge(
            face,
            side_vert,
            exit_edge
        )


        if next_side is None:

            print(
                "ROLL ERRO: "
                "Não foi possível seguir "
                "a lateral da cadeia."
            )

            return None


        side_vert = next_side


    # No último quad,
    # encontra o canto ligado
    # ao mesmo lado.

    end_face = chain[-1]

    entry_edge = get_shared_edge(
        end_face,
        chain[-2]
    )


    for vert in end_face.verts:

        if vert in entry_edge.verts:
            continue

        edge = find_edge_between(
            side_vert,
            vert
        )

        if (
            edge is not None
            and end_face in edge.link_faces
        ):
            return vert


    print(
        "ROLL ERRO: "
        "Não foi possível determinar "
        "o canto final."
    )

    return None


# ============================================================
# CONFIGURAÇÃO SPLIT 3
# ============================================================

def get_split3_config(
    face,
    corner_vert,
    shared_edge
):

    verts = list(face.verts)

    index = verts.index(
        corner_vert
    )


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


    edge_AB = find_edge_between(
        A,
        B
    )

    edge_BC = find_edge_between(
        B,
        C
    )


    if shared_edge is edge_AB:

        shared_slot = 'AB'
        other_edge = edge_BC

    elif shared_edge is edge_BC:

        shared_slot = 'BC'
        other_edge = edge_AB

    else:

        return None


    return {
        'D': D,
        'A': A,
        'B': B,
        'C': C,

        'shared_slot': shared_slot,

        'shared_edge': shared_edge,
        'other_edge': other_edge,

        'center': face.calc_center_median().copy(),

        'normal': face.normal.copy(),

        'material_index': face.material_index,

        'smooth': face.smooth,
    }


# ============================================================
# CRIAR FACES SPLIT 3
# ============================================================

def create_split3_faces(
    bm,
    config,
    shared_mid,
    other_mid
):

    D = config['D']
    A = config['A']
    B = config['B']
    C = config['C']


    if config['shared_slot'] == 'AB':

        E = shared_mid
        F = other_mid

    else:

        E = other_mid
        F = shared_mid


    G = bm.verts.new(
        config['center']
    )


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

        print(
            "ROLL ERRO ao criar Split 3:"
        )

        print(error)

        return False


    new_faces = (
        quad_1,
        quad_2,
        quad_3
    )


    for new_face in new_faces:

        new_face.normal_update()


        if (
            new_face.normal.dot(
                config['normal']
            ) < 0
        ):
            new_face.normal_flip()


        new_face.material_index = (
            config['material_index']
        )

        new_face.smooth = (
            config['smooth']
        )

        new_face.select = True


    return True


# ============================================================
# START SPLIT
# ============================================================

def execute_start_split(
    bm,
    face,
    config
):

    shared_edge = config[
        'shared_edge'
    ]

    other_edge = config[
        'other_edge'
    ]


    bm.faces.remove(
        face
    )


    # Shared midpoint
    _, shared_mid = bmesh.utils.edge_split(
        shared_edge,
        shared_edge.verts[0],
        0.5
    )


    # Outro braço do Split 3
    _, other_mid = bmesh.utils.edge_split(
        other_edge,
        other_edge.verts[0],
        0.5
    )


    result = create_split3_faces(
        bm,
        config,
        shared_mid,
        other_mid
    )


    if not result:
        return None


    return shared_mid


# ============================================================
# MIDDLE SIMPLE SPLIT
# ============================================================

def execute_middle_split(
    bm,
    face,
    entry_mid,
    exit_edge
):

    _, exit_mid = bmesh.utils.edge_split(
        exit_edge,
        exit_edge.verts[0],
        0.5
    )


    try:

        bmesh.ops.connect_verts(
            bm,
            verts=[
                entry_mid,
                exit_mid
            ]
        )


    except Exception as error:

        print(
            "ROLL ERRO no corte intermediário:"
        )

        print(error)

        return None


    return exit_mid


# ============================================================
# END SPLIT
# ============================================================

def execute_end_split(
    bm,
    face,
    config,
    entry_mid
):

    other_edge = config[
        'other_edge'
    ]


    # Remove a face que agora possui
    # 5 vértices por causa do midpoint
    # vindo do quad anterior.

    bm.faces.remove(
        face
    )


    _, other_mid = bmesh.utils.edge_split(
        other_edge,
        other_edge.verts[0],
        0.5
    )


    result = create_split3_faces(
        bm,
        config,
        entry_mid,
        other_mid
    )


    return result


# ============================================================
# EXECUTE SPLIT ROLL
# ============================================================

def execute_split_roll(
    bm,
    context,
    side='SIDE_A'
):

    print("")
    print("================================")
    print("        SPLIT ROLL REAL")
    print("================================")


    # --------------------------------------------------------
    # SELEÇÃO
    # --------------------------------------------------------

    selected_faces = get_selected_quad_faces(
        bm
    )


    if selected_faces is None:
        return False


    chain = build_face_chain(
        selected_faces
    )


    if chain is None:
        return False

    if not validate_chain_face_types(chain):
        return False


    # --------------------------------------------------------
    # FACE ATIVA DEFINE O INÍCIO
    # --------------------------------------------------------

    chain = orient_chain_from_active(
        bm,
        chain
    )


    if chain is None:
        return False


    # --------------------------------------------------------
    # VALIDAR CURVAS
    # --------------------------------------------------------

    if not validate_roll_path(
        chain
    ):
        return False


    print("")
    print(
        "START:",
        chain[0].index
    )

    print(
        "END:",
        chain[-1].index
    )

    first_shared = get_shared_edge(
        chain[0],
        chain[1]
    )

    if first_shared is None:
        print(
            "ROLL ERRO: "
            "Aresta inicial compartilhada "
            "não encontrada."
        )
        return False


    outer_verts = get_outer_choice_verts(
        chain,
        first_shared,
        context
    )

    if outer_verts is None:
        print(
            "ROLL ERRO: "
            "Não foi possível encontrar "
            "os dois vértices externos."
        )
        return False


    if side == 'SIDE_A':
        start_corner = outer_verts[0]
    elif side == 'SIDE_B':
        start_corner = outer_verts[1]
    else:
        print("ROLL ERRO: orientação desconhecida.")
        return False

    end_corner = calculate_end_corner(
        chain,
        start_corner
    )

    if end_corner is None:
        return False

    print(
        "Canto final automático:",
        end_corner.index
    )

    print(
        "Canto inicial automático:",
        start_corner.index
    )




    # --------------------------------------------------------
    # CONFIGURAÇÕES DOS EXTREMOS
    # --------------------------------------------------------

    first_shared = get_shared_edge(
        chain[0],
        chain[1]
    )


    last_shared = get_shared_edge(
        chain[-1],
        chain[-2]
    )


    if len(chain[0].verts) == 5:
        start_config = get_pentagon_endpoint_config(
            chain[0],
            start_corner,
            first_shared
        )
    else:
        start_config = get_split3_config(
            chain[0],
            start_corner,
            first_shared
        )


    if start_config is None:

        print(
            "ROLL ERRO: "
            "Canto inicial incompatível."
        )

        return False


    if len(chain[-1].verts) == 5:
        end_config = get_pentagon_endpoint_config(
            chain[-1],
            end_corner,
            last_shared
        )
    else:
        end_config = get_split3_config(
            chain[-1],
            end_corner,
            last_shared
        )


    if end_config is None:

        print(
            "ROLL ERRO: "
            "Canto final incompatível."
        )

        return False


    # --------------------------------------------------------
    # PASSAR A FACA
    # --------------------------------------------------------

    print("")
    print("🔪 START SPLIT 3")


    if len(chain[0].verts) == 5:
        current_mid = execute_start_split_pentagon(
            bm,
            chain[0],
            start_config
        )
    else:
        current_mid = execute_start_split(
            bm,
            chain[0],
            start_config
        )


    if current_mid is None:
        return False


    # --------------------------------------------------------
    # INTERMEDIÁRIOS
    # --------------------------------------------------------

    for i in range(
        1,
        len(chain) - 1
    ):

        current_face = chain[i]

        next_face = chain[i + 1]


        exit_edge = get_shared_edge(
            current_face,
            next_face
        )


        if exit_edge is None:

            print(
                "ROLL ERRO: "
                "Aresta de saída perdida."
            )

            return False


        print(
            "🔪 SIMPLE SPLIT:",
            current_face.index
        )


        current_mid = execute_middle_split(
            bm,
            current_face,
            current_mid,
            exit_edge
        )


        if current_mid is None:
            return False


    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print("🔪 END SPLIT 3")


    # A divisão anterior já adicionou o entry_mid à ponta.
    # Uma ponta originalmente pentagonal agora possui 6 vértices.
    if 'corner' in end_config:
        result = execute_end_split_pentagon(
            bm,
            chain[-1],
            end_config,
            current_mid
        )
    else:
        result = execute_end_split(
            bm,
            chain[-1],
            end_config,
            current_mid
        )


    if not result:
        return False


    # --------------------------------------------------------
    # UPDATE INDEX
    # --------------------------------------------------------

    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()


    print("")
    print("--------------------------------")
    print("SPLIT ROLL CONCLUÍDO 🔥")
    print("--------------------------------")
    print("")


    return True


# ============================================================
# EXTREMIDADE PENTAGONAL
# ============================================================

def get_pentagon_endpoint_config(
    face,
    corner_vert,
    shared_edge
):
    if len(face.verts) != 5:
        return None

    if corner_vert in shared_edge.verts:
        return None

    return {
        'corner': corner_vert,
        'shared_edge': shared_edge,
        'center': face.calc_center_median().copy(),
        'normal': face.normal.copy(),
        'material_index': face.material_index,
        'smooth': face.smooth,
    }


def create_pentagon_endpoint_faces(
    bm,
    face,
    config,
    shared_mid
):
    """Liga vértices existentes e aceita triângulos ou N-gons."""

    boundary = list(face.verts)
    corner = config['corner']

    if corner not in boundary or shared_mid not in boundary:
        print("ROLL ERRO: pontos da ponta pentagonal fora da borda.")
        return False

    corner_index = boundary.index(corner)
    shared_index = boundary.index(shared_mid)
    required = {corner_index, shared_index}
    best_index = None
    best_score = None
    vert_count = len(boundary)

    # Escolhe o terceiro vértice que distribui as três faces
    # da maneira mais equilibrada possível.
    for candidate_index in range(vert_count):
        if candidate_index in required:
            continue

        indices = sorted((
            corner_index,
            shared_index,
            candidate_index
        ))
        gaps = (
            indices[1] - indices[0],
            indices[2] - indices[1],
            vert_count - indices[2] + indices[0]
        )
        score = (
            max(gaps),
            sum(abs(gap - 2) for gap in gaps)
        )

        if best_score is None or score < best_score:
            best_score = score
            best_index = candidate_index

    if best_index is None:
        print("ROLL ERRO: terceiro vértice da ponta não encontrado.")
        return False

    spoke_indices = sorted((
        corner_index,
        shared_index,
        best_index
    ))

    bm.faces.remove(face)
    center_vert = bm.verts.new(config['center'])
    new_faces = []

    try:
        for index in range(3):
            start = spoke_indices[index]
            end = spoke_indices[(index + 1) % 3]
            face_verts = [boundary[start]]
            cursor = (start + 1) % vert_count

            while cursor != end:
                face_verts.append(boundary[cursor])
                cursor = (cursor + 1) % vert_count

            face_verts.append(boundary[end])
            face_verts.append(center_vert)
            new_faces.append(
                bm.faces.new(tuple(face_verts))
            )

    except Exception as error:
        print("ROLL ERRO ao criar ponta pentagonal:")
        print(error)
        return False

    for new_face in new_faces:
        new_face.normal_update()

        if new_face.normal.dot(config['normal']) < 0:
            new_face.normal_flip()

        new_face.material_index = config['material_index']
        new_face.smooth = config['smooth']
        new_face.select = True

    return True


def execute_start_split_pentagon(
    bm,
    face,
    config
):
    shared_edge = config['shared_edge']

    _, shared_mid = bmesh.utils.edge_split(
        shared_edge,
        shared_edge.verts[0],
        0.5
    )

    if not create_pentagon_endpoint_faces(
        bm,
        face,
        config,
        shared_mid
    ):
        return None

    return shared_mid


def execute_end_split_pentagon(
    bm,
    face,
    config,
    entry_mid
):
    return create_pentagon_endpoint_faces(
        bm,
        face,
        config,
        entry_mid
    )
