import math
import heapq

# ==========================================
# 1. RAYCASTING (Visão Física)
# ==========================================
def raycast_clear_line(grid, start, end):
    """
    Verifica se há paredes (1) na linha reta entre start e end.

    Anda em passos de 1 tile (o maior dos dois eixos define a quantidade de
    passos, como um DDA) em vez de amostrar a cada 0.5 de distância euclidiana:
    pra uma diagonal de 8 tiles isso é 8 passos ao invés de ~23, e ainda cobre
    toda célula no caminho (sem furos), o que a amostragem antiga não garantia
    para distâncias curtas.
    """
    y0, x0 = start
    y1, x1 = end

    passos = max(abs(y1 - y0), abs(x1 - x0))
    if passos == 0:
        return True

    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    passo_y = (y1 - y0) / passos
    passo_x = (x1 - x0) / passos

    y, x = float(y0), float(x0)
    for _ in range(passos):
        y += passo_y
        x += passo_x
        gy, gx = int(round(y)), int(round(x))

        if not (0 <= gy < rows and 0 <= gx < cols):
            return False
        if grid[gy][gx] == 1:
            return False

    return True

# ==========================================
# 2. FOV (Campo de Visão)
# ==========================================
def is_player_in_fov(enemy_pos, player_pos, enemy_facing_angle, fov_angle, max_dist, grid, ignora_paredes=False):
    """
    Verifica se o jogador está visível integrando Distância + Ângulo + Raycasting.

    Os testes mais baratos vêm primeiro pra sair cedo sem gastar trig nem
    percorrer o grid: distância ao quadrado (sem sqrt) e, só se o campo de
    visão não for 360, o ângulo do cone. O raycast (o mais caro) só roda se
    os dois anteriores já passaram.
    """
    dy = player_pos[0] - enemy_pos[0]
    dx = player_pos[1] - enemy_pos[1]

    dist_quadrado = dy * dy + dx * dx
    if dist_quadrado > max_dist * max_dist:
        return False

    if fov_angle < 360:
        # math.atan2 retorna o ângulo em radianos, convertemos para graus
        angle_to_player = math.degrees(math.atan2(dy, dx))

        # Normaliza a diferença de ângulo para ficar entre -180 e 180
        angle_diff = (angle_to_player - enemy_facing_angle) % 360
        if angle_diff > 180:
            angle_diff -= 360

        if abs(angle_diff) > (fov_angle / 2):
            return False

    if ignora_paredes:
        return True
    # Se passou pela distância e pelo ângulo, faz o Raycasting
    return raycast_clear_line(grid, enemy_pos, player_pos)

# ==========================================
# 3. A* (Busca de Caminho)
# ==========================================
def a_star(grid, start, end):
    """
    Encontra o caminho mais curto desviando de obstáculos.

    A heurística de Manhattan pura empata sempre que dois vizinhos estão a
    igual distância do alvo, e o heapq então desempata comparando as tuplas
    (linha, coluna) — o que sistematicamente prioriza reduzir a linha antes
    da coluna. Resultado visual: o caminho sobe todo pra depois andar todo
    pro lado, em vez de alternar como uma escadinha na direção da reta
    start->end. Corrigido com um termo de desempate por distância à reta
    (cross-track): entre vizinhos empatados, prefere o mais alinhado com a
    linha reta até o objetivo.
    """
    rows, cols = len(grid), len(grid[0])
    if start == end:
        return []

    open_set = []
    contador = 0  # desempate estável do heap; barato e evita comparar tuplas de coordenadas à toa
    heapq.heappush(open_set, (0, contador, start))

    came_from = {}
    g_score = {start: 0}

    # Movimentos: Cima, Baixo, Esquerda, Direita
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    dy_total = end[0] - start[0]
    dx_total = end[1] - start[1]

    while open_set:
        _, _, current = heapq.heappop(open_set)

        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for dy, dx in directions:
            neighbor = (current[0] + dy, current[1] + dx)

            # Verifica se está dentro do mapa e se não é parede
            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols:
                if grid[neighbor[0]][neighbor[1]] == 1:
                    continue

                tentative_g_score = g_score[current] + 1

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score

                    # Heurística de Manhattan (distância em grid)
                    h_score = abs(neighbor[0] - end[0]) + abs(neighbor[1] - end[1])

                    # Desempate: distância do vizinho até a reta start->end.
                    # Peso pequeno (não pode superar o custo de 1 passo) só
                    # pra guiar empates, não pra mudar o caminho mais curto.
                    cross = abs((neighbor[0] - start[0]) * dx_total - (neighbor[1] - start[1]) * dy_total)
                    f_score = tentative_g_score + h_score + cross * 0.001

                    contador += 1
                    heapq.heappush(open_set, (f_score, contador, neighbor))

    return [] # Retorna lista vazia se não achar caminho

# ==========================================
# AMBIENTE DE TESTE (Simulação no Terminal)
# ==========================================
def print_test_scenario(grid, enemy, player, path=[]):
    print("\nLegenda: [E] Inimigo | [P] Jogador | [█] Parede | [*] Caminho A* | [.] Chão")
    print("-" * 50)
    for y in range(len(grid)):
        row_str = ""
        for x in range(len(grid[0])):
            if (y, x) == enemy:
                row_str += " E "
            elif (y, x) == player:
                row_str += " P "
            elif (y, x) in path:
                row_str += " * "
            elif grid[y][x] == 1:
                row_str += " █ "
            else:
                row_str += " . "
        print(row_str)
    print("-" * 50)

if __name__ == "__main__":
    # Matriz do mapa: 0 = Livre, 1 = Parede
    mapa = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0]
    ]

    inimigo_pos = (2, 2)
    jogador_pos = (0, 6) # Escondido atrás da parede superior direita
    inimigo_olhando_para = 45 # graus (diagonal inferior direita)
    angulo_visao = 90
    distancia_max = 6

    print("\n=== INICIANDO TESTE DAS IAs ===")

    # 1. Testa FOV e Raycasting integrados
    visivel = is_player_in_fov(inimigo_pos, jogador_pos, inimigo_olhando_para, angulo_visao, distancia_max, mapa)

    if visivel:
        print("\n[!] ALERTA: Jogador entrou no FOV e está com linha de visão limpa!")
        print("Ação do Inimigo: ATACAR")
        print_test_scenario(mapa, inimigo_pos, jogador_pos)
    else:
        print("\n[?] Jogador não está visível (Fora do FOV, muito longe ou bloqueado por parede).")
        print("Ação do Inimigo: ACIONAR A* PARA BUSCA/PERSEGUIÇÃO")

        # 2. Testa o A*
        caminho = a_star(mapa, inimigo_pos, jogador_pos)

        if caminho:
            print(f"\nCaminho calculado com sucesso! Passos: {len(caminho)}")
            print_test_scenario(mapa, inimigo_pos, jogador_pos, caminho)
        else:
            print("\nNenhum caminho encontrado. Jogador inalcançável.")
