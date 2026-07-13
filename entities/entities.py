import arcade
import math
import random
from ia import ia_system as ia
from sprites.carregador import anims_personagem, anims_morcego, anims_slime

# Tileset é 16px; escala 3x => cada tile ocupa 48px na tela.
# A janela é 960x720; o MUNDO pode ser maior (a câmera segue o personagem).
TILE_PX = 16
ESCALA = 3
TAMANHO_TILE = TILE_PX * ESCALA  # 48
ALTURA_TELA = 720
LARGURA_TELA = 960

# dimensões do mundo em pixels; atualizadas por definir_mundo() com o tamanho da matriz
ALTURA_MUNDO = ALTURA_TELA
LARGURA_MUNDO = LARGURA_TELA

DURACAO_FRAME = 0.12  # segundos por keyframe de animação

def definir_mundo(linhas, colunas):
    """Registra o tamanho do mapa (em tiles) pras conversões pixel<->grid."""
    global ALTURA_MUNDO, LARGURA_MUNDO
    ALTURA_MUNDO = linhas * TAMANHO_TILE
    LARGURA_MUNDO = colunas * TAMANHO_TILE

# ==========================================
# Funções de Tradução (Pixels <-> Matriz)
# ==========================================
def pixel_para_grid(x, y):
    #Converte coordenada do mundo para linha e coluna da matriz
    coluna = int(x // TAMANHO_TILE)
    linha = int((ALTURA_MUNDO - y) // TAMANHO_TILE)
    return linha, coluna

def grid_para_pixel(linha, coluna):
    #Converte linha e coluna da matriz para o centro do Tile no mundo
    x = (coluna * TAMANHO_TILE) + (TAMANHO_TILE / 2)
    y = ALTURA_MUNDO - (linha * TAMANHO_TILE) - (TAMANHO_TILE / 2)
    return x, y

def colide_com_parede(x, y, mapa, meia_larg, meia_alt):
    """Testa os 4 cantos da caixa de colisão contra a matriz (1 = parede)."""
    for dx in (-meia_larg, meia_larg):
        for dy in (-meia_alt, meia_alt):
            linha, coluna = pixel_para_grid(x + dx, y + dy)
            if not (0 <= linha < len(mapa) and 0 <= coluna < len(mapa[0])):
                return True
            if mapa[linha][coluna] == 1:
                return True
    return False

# ==========================================
# Base animada (máquina de estados de animação)
# ==========================================
class EntidadeAnimada(arcade.Sprite):
    """Sprite com animações por (acao, direcao).
    Ações: idle, run, atack (toca 1x e volta pro idle), dead (toca 1x e congela no último frame).
    """
    def __init__(self, anims):
        super().__init__(scale=ESCALA)
        self.anims = anims
        self.acao = "idle"
        self.direcao = "front"
        self.frame = 0
        self.tempo_frame = 0.0
        self.morto = False
        self.atacando = False
        self.texture = anims[("idle", "front")][0]

    def _frames(self):
        return self.anims[(self.acao, self.direcao)]

    def atacar(self):
        if self.morto or self.atacando:
            return
        self.atacando = True
        self.acao = "atack"
        self.frame = 0
        self.tempo_frame = 0.0

    def morrer(self):
        if self.morto:
            return
        self.morto = True
        self.atacando = False
        self.acao = "dead"
        self.frame = 0
        self.tempo_frame = 0.0
        self.change_x = 0
        self.change_y = 0

    def atualizar_direcao(self):
        """Escolhe ação (idle/run) e direção do sprite a partir do movimento atual."""
        if self.morto or self.atacando:
            return
        dx, dy = self.change_x, self.change_y
        if dx == 0 and dy == 0:
            self.acao = "idle"
            return
        self.acao = "run"
        if abs(dx) >= abs(dy):
            self.direcao = "side" if dx > 0 else "side_flip"
        elif dy > 0:
            self.direcao = "back"   # subindo = de costas
        else:
            self.direcao = "front"  # descendo = de frente

    def update_animation(self, delta_time: float = 1/60, *args, **kwargs):
        frames = self._frames()
        self.tempo_frame += delta_time
        if self.tempo_frame >= DURACAO_FRAME:
            self.tempo_frame -= DURACAO_FRAME
            if self.acao == "dead":
                if self.frame < len(frames) - 1:
                    self.frame += 1  # congela no último frame
            elif self.acao == "atack":
                self.frame += 1
                if self.frame >= len(frames):  # ataque tocou inteiro
                    self.frame = 0
                    self.atacando = False
                    self.acao = "idle"
            else:
                self.frame = (self.frame + 1) % len(frames)
        self.frame = min(self.frame, len(frames) - 1)
        self.texture = self._frames()[self.frame]

# ==========================================
# Jogador
# ==========================================
class Jogador(EntidadeAnimada):
    def __init__(self, mapa):
        super().__init__(anims_personagem())
        self.mapa = mapa
        self.velocidade = 300
        # caixa de colisão menor que o sprite (o corpo do cavaleiro não preenche os 96px)
        self.meia_larg = 16
        self.meia_alt = 14

    def update(self, delta_time: float = 1/60, *args, **kwargs):
        if self.morto:
            return
        # move eixo por eixo: se bater na parede, cancela só aquele eixo (permite deslizar)
        novo_x = self.center_x + self.change_x * delta_time
        if not colide_com_parede(novo_x, self.center_y, self.mapa, self.meia_larg, self.meia_alt):
            self.center_x = novo_x
        novo_y = self.center_y + self.change_y * delta_time
        if not colide_com_parede(self.center_x, novo_y, self.mapa, self.meia_larg, self.meia_alt):
            self.center_y = novo_y
        self.atualizar_direcao()

# ==========================================
# Inimigos
# ==========================================
class InimigoBase(EntidadeAnimada):
    def __init__(self, anims, velocidade, raio_visao, angulo_visao):
        super().__init__(anims)
        self.velocidade = velocidade
        self.estado = "patrulha"

        #parametros de IA
        self.raio_visao = raio_visao #dist máx em blocos
        self.angulo_visao = angulo_visao #ângulo de cone de visão em graus
        self.angulo_olhar = 0 #onde o inimigo está olhando no momento

        self.caminho_atual = []
        self.tempo_espera_patrulha = 0

        self.mapa = None
        self.colide_paredes = True
        self.meia_larg = 12
        self.meia_alt = 12

    def update_ia(self, mapa, jogador_x, jogador_y):
        self.mapa = mapa
        if self.morto:
            return
        if self.atacando:
            self.change_x = 0
            self.change_y = 0
            return

        # Descobre onde está o player e o inimigo
        minha_pos_grid = pixel_para_grid(self.center_x, self.center_y)
        jogador_pos_grid = pixel_para_grid(jogador_x, jogador_y)

        # Alinha o ângulo do olhar com o movimento (menos no change_y p/ alinhar Pixels e Matriz)
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

            if caminho and len(caminho) > 0:
                # Se o índice 0 for onde o inimigo já está, o próximo passo é o índice 1
                if caminho[0] == minha_pos_grid and len(caminho) > 1:
                    proximo_passo = caminho[1]
                else:
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
        if self.morto:
            return
        novo_x = self.center_x + self.change_x * delta_time
        novo_y = self.center_y + self.change_y * delta_time
        if self.colide_paredes and self.mapa:
            if not colide_com_parede(novo_x, self.center_y, self.mapa, self.meia_larg, self.meia_alt):
                self.center_x = novo_x
            if not colide_com_parede(self.center_x, novo_y, self.mapa, self.meia_larg, self.meia_alt):
                self.center_y = novo_y
        else:
            # voadores atravessam paredes, mas não saem do mundo
            self.center_x = max(0, min(LARGURA_MUNDO, novo_x))
            self.center_y = max(0, min(ALTURA_MUNDO, novo_y))
        self.atualizar_direcao()

# Inimigos Específicos herdando da base
class Slime(InimigoBase):
    def __init__(self):
        # Slimes são mais lentos
        super().__init__(anims_slime(), velocidade=120, raio_visao=5, angulo_visao=360)
        self.angulo_olhar = 0 #começa olhando pra esquerda

class Morcego(InimigoBase):
    def __init__(self):
        # Morcegos são mais rápidos e enxergam longe (8 blocos), cone de 120 graus
        super().__init__(anims_morcego(), velocidade=240, raio_visao=8, angulo_visao=120)
        self.angulo_olhar = 180
        self.colide_paredes = False # voa por cima das paredes

    def update_ia(self, mapa, jogador_x, jogador_y):
        self.mapa = mapa
        if self.morto:
            return
        if self.atacando:
            self.change_x = 0
            self.change_y = 0
            return

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
