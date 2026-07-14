import math
import heapq

# ==========================================
# 1. RAYCASTING (Visão Física)
# ==========================================
def raycast_clear_line(grid, start, end):
    """
    Verifica se há paredes (1) na linha reta entre start e end.
    """
    dist = math.hypot(end[0] - start[0], end[1] - start[1])
    if dist == 0: return True
    
    dx = (end[1] - start[1]) / dist
    dy = (end[0] - start[0]) / dist
    
    step_size = 0.5 
    current_dist = 0.0
    
    while current_dist < dist:
        current_dist += step_size
        check_y = start[0] + dy * current_dist
        check_x = start[1] + dx * current_dist
        
        grid_y, grid_x = int(round(check_y)), int(round(check_x))
        
        # Se bater na parede, visão bloqueada
        if grid[grid_y][grid_x] == 1:
            return False
            
    return True

# ==========================================
# 2. FOV (Campo de Visão)
# ==========================================
def is_player_in_fov(enemy_pos, player_pos, enemy_facing_angle, fov_angle, max_dist, grid):
    """
    Verifica se o jogador está visível integrando Distância + Ângulo + Raycasting.
    """
    dist = math.hypot(player_pos[0] - enemy_pos[0], player_pos[1] - enemy_pos[1])
    
    # 1. Checa a distância máxima
    if dist > max_dist:
        return False
        
    # 2. Checa o ângulo do cone de visão
    # math.atan2 retorna o ângulo em radianos, convertemos para graus
    angle_to_player = math.degrees(math.atan2(player_pos[0] - enemy_pos[0], player_pos[1] - enemy_pos[1]))
    
    # Normaliza a diferença de ângulo para ficar entre -180 e 180
    angle_diff = (angle_to_player - enemy_facing_angle) % 360
    if angle_diff > 180:
        angle_diff -= 360
        
    if abs(angle_diff) > (fov_angle / 2):
        return False
        
    # 3. Se passou pela distância e pelo ângulo, faz o Raycasting
    return raycast_clear_line(grid, enemy_pos, player_pos)

# ==========================================
# 3. A* (Busca de Caminho)
# ==========================================
def a_star(grid, start, end):
    """
    Encontra o caminho mais curto desviando de obstáculos.
    """
    rows, cols = len(grid), len(grid[0])
    open_set = []
    heapq.heappush(open_set, (0, start))
    
    came_from = {}
    g_score = {start: 0}
    
    # Movimentos: Cima, Baixo, Esquerda, Direita
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    while open_set:
        _, current = heapq.heappop(open_set)
        
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
                    f_score = tentative_g_score + h_score
                    
                    heapq.heappush(open_set, (f_score, neighbor))
                    
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

    inimigo_pos = (2, 3)
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