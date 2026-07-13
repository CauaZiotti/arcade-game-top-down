import arcade
import math
import random
from ia import ia_system  as ia

TAMANHO_TILE = 40
ALTURA_TELA = 600

# ==========================================
# Funções de Tradução (Pixels <-> Matriz)
# ==========================================
def pixel_para_grid(x, y):
    #Converte coordenada da tela para linha e coluna da matriz 
    coluna = int(x // TAMANHO_TILE)
    linha = int((ALTURA_TELA - y) // TAMANHO_TILE)
    return linha, coluna

def grid_para_pixel(linha, coluna):
    #Converte linha e coluna da matriz para o centro do Tile na tela 
    x = (coluna * TAMANHO_TILE) + (TAMANHO_TILE / 2)
    y = ALTURA_TELA - (linha * TAMANHO_TILE) - (TAMANHO_TILE / 2)
    return x, y

class Jogador(arcade.SpriteSolidColor):
    def __init__(self, largura, altura, cor):
        super().__init__(largura, altura, cor)
        self.velocidade = 300

    def update(self, delta_time: float = 1/60, *args, **kwargs):
        # A movimentação baseada em change_x e change_y é processada aqui
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time

class InimigoBase(arcade.SpriteCircle):
    def __init__(self, raio, cor, velocidade, raio_visao, angulo_visao):
        super().__init__(raio, cor)
        self.velocidade = velocidade
        self.estado = "patrulha" 

        #parametros de IA
        self.raio_visao = raio_visao #dist máx em blocos 
        self.angulo_visao = angulo_visao #ângulo de cone de visão em graus
        self.angulo_olhar = 0 #ondeo inimigo está olhando no momento

        self.caminho_atual = []
        self.tempo_espera_patrulha = 0

    def update_ia(self, mapa, jogador_x, jogador_y):
        # Descobre onde está o player e o inimigo
        minha_pos_grid = pixel_para_grid(self.center_x, self.center_y)
        jogador_pos_grid = pixel_para_grid(jogador_x, jogador_y)

        # 1. CORREÇÃO: O sinal de menos (-) voltou para o change_y para alinhar Pixels e Matriz
        if self.change_x != 0 or self.change_y != 0:
            self.angulo_olhar = math.degrees(math.atan2(-self.change_y, self.change_x)) 

        # Junta fov e raycasting pra ver se o player está visível
        jogador_visivel = ia.is_player_in_fov(
            minha_pos_grid, 
            jogador_pos_grid, 
            self.angulo_olhar, 
            self.angulo_visao, 
            self.raio_visao, 
            mapa
        )

        # Máquina de estados para controle 
        if jogador_visivel:
            self.estado = "perseguicao"
            self.tempo_espera_patrulha = 0
        else:
            self.estado = "patrulha"
        
        # Integra A*, só persegue se o estado permitir
        if self.estado == "perseguicao":
            caminho = ia.a_star(mapa, minha_pos_grid, jogador_pos_grid)

            self.caminho_atual = caminho # Guarda o caminho atual para debug ou uso futuro

            # 2. CORREÇÃO: Leitura à prova de falhas do caminho do A*
            if caminho and len(caminho) > 0:
                
                # Se o índice 0 for onde o inimigo já está, o próximo passo é o índice 1
                if caminho[0] == minha_pos_grid and len(caminho) > 1:
                    proximo_passo = caminho[1]
                else:
                    # Se o A* já filtrou o início, o próximo passo é direto o índice 0
                    proximo_passo = caminho[0]

                # Converte o próximo passo de volta para pixels
                alvo_x, alvo_y = grid_para_pixel(proximo_passo[0], proximo_passo[1])

                if len(caminho) == 1 or proximo_passo == jogador_pos_grid: #deixa a perseguição mais legal e real
                    alvo_x, alvo_y = jogador_x, jogador_y

                # Calcula a direção para o centro do próximo quadrado
                dist_x = alvo_x - self.center_x
                dist_y = alvo_y - self.center_y
                distancia_total = math.hypot(dist_x, dist_y)

                if distancia_total > 2: # Margem de erro pra evitar tremer
                    self.change_x = (dist_x / distancia_total) * self.velocidade
                    self.change_y = (dist_y / distancia_total) * self.velocidade
                else:
                    self.change_x = 0
                    self.change_y = 0
            else:
                self.change_x = 0
                self.change_y = 0

        elif self.estado == "patrulha":
            if self.tempo_espera_patrulha > 0:
                #para para 'descansar'
                self.tempo_espera_patrulha -= 1
                self.change_x = 0
                self.change_y = 0
            else:
                if not self.caminho_atual:
                    linha_aleatoria = minha_pos_grid[0] + random.randint(-4, 4)
                    coluna_aleatoria = minha_pos_grid[1] + random.randint(-4, 4)

                    if (0 <= linha_aleatoria < len(mapa)) and (0 <= coluna_aleatoria < len(mapa[0])):
                        if mapa[linha_aleatoria][coluna_aleatoria] == 0:
                            self.caminho_atual = ia.a_star(mapa, minha_pos_grid, (linha_aleatoria, coluna_aleatoria))
                    if not self.caminho_atual:
                        # Se não encontrou caminho, espera um pouco antes de tentar novamente
                        self.tempo_espera_patrulha = 30

                # Se já tem o caminho da patrulha, vai andando
                if self.caminho_atual and len(self.caminho_atual) > 0:
                    if self.caminho_atual[0] == minha_pos_grid and len(self.caminho_atual) > 1:
                        proximo_passo = self.caminho_atual[1]
                    else:
                        proximo_passo = self.caminho_atual[0]

                    alvo_x, alvo_y = grid_para_pixel(proximo_passo[0], proximo_passo[1])
                    dist_x = alvo_x - self.center_x
                    dist_y = alvo_y - self.center_y
                    distancia_total = math.hypot(dist_x, dist_y)

                    if distancia_total > 2:
                        # Anda devagar na patrulha (metade da velocidade)
                        self.change_x = (dist_x / distancia_total) * (self.velocidade / 2)
                        self.change_y = (dist_y / distancia_total) * (self.velocidade / 2)
                    else:
                        # Chegou no bloco! Tira ele da lista
                        if len(self.caminho_atual) > 1:
                            self.caminho_atual.pop(0)
                        else:
                            # Fim da patrulha. Zera a lista e descansa um pouco
                            self.caminho_atual = []
                            self.change_x = 0
                            self.change_y = 0
                            self.tempo_espera_patrulha = 60 # Espera 1 segundo

    def update(self, delta_time: float = 1/60, *args, **kwargs):
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time

# Inimigos Específicos herdando da base
class Slime(InimigoBase):
    def __init__(self, raio, cor):
        # Slimes são mais lentos
        super().__init__(raio, cor, velocidade=120, raio_visao=5, angulo_visao=360)
        self.angulo_olhar = 0 #começa olhando pra esquerda

class Morcego(InimigoBase):
    def __init__(self, raio, cor):
        # Morcegos são mais rápidos e enxergam longe (8 blocos), cone de 120 graus
        super().__init__(raio, cor, velocidade=240, raio_visao=8, angulo_visao=120)
        self.angulo_olhar = 180

    def update_ia(self, mapa, jogador_x, jogador_y):
        minha_pos_grid = pixel_para_grid(self.center_x, self.center_y)
        jogador_pos_grid = pixel_para_grid(jogador_x, jogador_y)

        # 1. Atualiza a direção do olhar
        if self.change_x != 0 or self.change_y != 0:
            self.angulo_olhar = math.degrees(math.atan2(-self.change_y, self.change_x))

        # 2. Usa Raycasting e FOV (não enxerga através de paredes)
        jogador_visivel = ia.is_player_in_fov(
            minha_pos_grid, 
            jogador_pos_grid, 
            self.angulo_olhar, 
            self.angulo_visao, 
            self.raio_visao, 
            mapa,
            True  # Morcegos ignoram paredes para perseguir o jogador
        )

        # 3. Máquina de Estados
        if jogador_visivel:
            self.estado = "perseguicao"
        else:
            self.estado = "patrulha"
            self.change_x = 0
            self.change_y = 0
            self.caminho_atual = [] # Limpa a linha de debug

        # 4. Perseguição (IGNORA PAREDES E O A*)
        if self.estado == "perseguicao":
            # Calcula a distância direta (linha reta em pixels) para o jogador
            dist_x = jogador_x - self.center_x
            dist_y = jogador_y - self.center_y
            distancia_total = math.hypot(dist_x, dist_y)

            if distancia_total > 2:
                # Voa direto para o jogador passando por cima de tudo
                self.change_x = (dist_x / distancia_total) * self.velocidade
                self.change_y = (dist_y / distancia_total) * self.velocidade
            else:
                self.change_x = 0
                self.change_y = 0
            
            # Para o Debug Visual funcionar, fingimos que o "caminho" é uma reta
            self.caminho_atual = [minha_pos_grid, jogador_pos_grid]