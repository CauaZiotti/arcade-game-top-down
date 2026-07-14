import arcade
import math
import random
from ia import ia_system as ia
from sprites.carregador import anims_personagem, anims_morcego, anims_slime

TILE_PX = 16
ESCALA = 3
TAMANHO_TILE = TILE_PX * ESCALA  # 48
ALTURA_TELA = 720
LARGURA_TELA = 960

ALTURA_MUNDO = ALTURA_TELA
LARGURA_MUNDO = LARGURA_TELA

DURACAO_FRAME = 0.12  # segundos por keyframe de animação
TEMPO_COOLDOWN_ATAQUE = 0.5  # segundos em idle após o ataque antes de poder atacar de novo
INTERVALO_RECALCULO_CAMINHO = 10  # frames entre buscas completas de A* durante a perseguição
TEMPO_MEMORIA_MORCEGO = 2.0  # segundos que o morcego continua buscando após perder o jogador de vista
TEMPO_INVULNERAVEL = 1.0  # segundos de invulnerabilidade do jogador após levar um golpe

def definir_mundo(linhas, colunas):
    global ALTURA_MUNDO, LARGURA_MUNDO
    ALTURA_MUNDO = linhas * TAMANHO_TILE
    LARGURA_MUNDO = colunas * TAMANHO_TILE

# ==========================================
# Funções de Tradução (Pixels <-> Matriz)
# ==========================================
def pixel_para_grid(x, y):
    coluna = int(x // TAMANHO_TILE)
    linha = int((ALTURA_MUNDO - y) // TAMANHO_TILE)
    return linha, coluna

def grid_para_pixel(linha, coluna):
    x = (coluna * TAMANHO_TILE) + (TAMANHO_TILE / 2)
    y = ALTURA_MUNDO - (linha * TAMANHO_TILE) - (TAMANHO_TILE / 2)
    return x, y

def colide_com_parede(x, y, mapa, meia_larg, meia_alt):
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
    def __init__(self, anims):
        super().__init__(scale=ESCALA)
        self.anims = anims
        self.acao = "idle"
        self.direcao = "front"
        self.frame = 0
        self.tempo_frame = 0.0
        self.morto = False
        self.atacando = False
        self.cooldown_ataque = 0.0
        self.vida_maxima = 1
        self.vida = 1
        self.tempo_flash_dano = 0.0
        self._anim_anterior = ("idle", "front")
        self.texture = anims[("idle", "front")][0]

    def _frames(self):
        return self.anims[(self.acao, self.direcao)]

    def atacar(self):
        if self.morto or self.atacando or self.cooldown_ataque > 0:
            return
        self.atacando = True
        self.acao = "atack"
        self.frame = 0
        self.tempo_frame = 0.0

    def receber_dano(self, quantidade=1):
        if self.morto:
            return
        self.vida -= quantidade
        if self.vida <= 0:
            self.morrer()
        else:
            self.tempo_flash_dano = 0.15

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
        self.tempo_flash_dano = 0.0
        self.alpha = 255

    def atualizar_direcao(self):
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
            self.direcao = "back"   
        else:
            self.direcao = "front"  

    def update_animation(self, delta_time: float = 1/60, *args, **kwargs):
        chave = (self.acao, self.direcao)
        if chave != self._anim_anterior:
            self._anim_anterior = chave
            self.frame = 0
            self.tempo_frame = 0.0

        if self.cooldown_ataque > 0:
            self.cooldown_ataque -= delta_time

        if self.tempo_flash_dano > 0:
            self.tempo_flash_dano -= delta_time
            self.alpha = 130
            if self.tempo_flash_dano <= 0:
                self.alpha = 255

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
                    self.cooldown_ataque = TEMPO_COOLDOWN_ATAQUE
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
        self.velocidade_base = 220 
        self.velocidade = self.velocidade_base
        self.tempo_velocidade_extra = 0.0  
        self.meia_larg = 16
        self.meia_alt = 14

        self.vida_maxima = 3
        self.vida = self.vida_maxima
        self.tempo_invulneravel = 0.0

    def receber_dano(self, quantidade=1):
        if self.morto or self.tempo_invulneravel > 0:
            return
        self.vida = max(0, self.vida - quantidade)
        self.tempo_invulneravel = TEMPO_INVULNERAVEL
        if self.vida <= 0:
            self.morrer()

    def curar(self, quantidade=1):
        self.vida = min(self.vida_maxima, self.vida + quantidade)

    def ativar_velocidade_extra(self, multiplicador, duracao):
        self.velocidade = self.velocidade_base * multiplicador
        self.tempo_velocidade_extra = duracao

    def update(self, delta_time: float = 1/60, *args, **kwargs):
        if self.morto:
            self.alpha = 255
            return

        if self.tempo_invulneravel > 0:
            self.tempo_invulneravel -= delta_time
            # pisca enquanto está invulnerável, feedback claro de que levou dano
            self.alpha = 120 if int(self.tempo_invulneravel * 10) % 2 == 0 else 255
        else:
            self.alpha = 255

        if self.tempo_velocidade_extra > 0:
            self.tempo_velocidade_extra -= delta_time
            if self.tempo_velocidade_extra <= 0:
                self.tempo_velocidade_extra = 0.0
                self.velocidade = self.velocidade_base

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
    def __init__(self, anims, velocidade, raio_visao, angulo_visao, vida=1):
        super().__init__(anims)
        self.velocidade = velocidade
        self.vida_maxima = vida
        self.vida = vida
        self.estado = "patrulha"

        #parametros de IA
        self.raio_visao = raio_visao #dist máx em blocos
        self.angulo_visao = angulo_visao #ângulo de cone de visão em graus
        self.angulo_olhar = 0 #onde o inimigo está olhando no momento

        self.caminho_atual = []
        self.tempo_espera_patrulha = 0

        self._alvo_busca_anterior = None
        self._contagem_recalculo = 0

        self.mapa = None
        self.colide_paredes = True
        self.meia_larg = 12
        self.meia_alt = 12

    def update_ia(self, mapa, jogador_x, jogador_y, delta_time=1/60):
        self.mapa = mapa
        if self.morto:
            return
        if self.atacando:
            self.change_x = 0
            self.change_y = 0
            return

        minha_pos_grid = pixel_para_grid(self.center_x, self.center_y)
        jogador_pos_grid = pixel_para_grid(jogador_x, jogador_y)

        if self.change_x != 0 or self.change_y != 0:
            self.angulo_olhar = math.degrees(math.atan2(-self.change_y, self.change_x))

        jogador_visivel = ia.is_player_in_fov(
            minha_pos_grid,
            jogador_pos_grid,
            self.angulo_olhar,
            self.angulo_visao,
            self.raio_visao,
            mapa
        )

        if jogador_visivel:
            self.estado = "perseguicao"
            self.tempo_espera_patrulha = 0
        else:
            self.estado = "patrulha"

        if self.estado == "perseguicao":
            if (jogador_pos_grid != self._alvo_busca_anterior
                    or not self.caminho_atual
                    or self._contagem_recalculo <= 0):
                self.caminho_atual = ia.a_star(mapa, minha_pos_grid, jogador_pos_grid)
                self._alvo_busca_anterior = jogador_pos_grid
                self._contagem_recalculo = INTERVALO_RECALCULO_CAMINHO
            else:
                self._contagem_recalculo -= 1

            caminho = self.caminho_atual # Guarda o caminho atual para debug ou uso futuro

            if caminho and len(caminho) > 0:
                if caminho[0] == minha_pos_grid and len(caminho) > 1:
                    proximo_passo = caminho[1]
                else:
                    proximo_passo = caminho[0]

                alvo_x, alvo_y = grid_para_pixel(proximo_passo[0], proximo_passo[1])

                if len(caminho) == 1 or proximo_passo == jogador_pos_grid: 
                    alvo_x, alvo_y = jogador_x, jogador_y

                
                dist_x = alvo_x - self.center_x
                dist_y = alvo_y - self.center_y
                distancia_total = math.hypot(dist_x, dist_y)

                if distancia_total > 2: 
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
                        self.tempo_espera_patrulha = 30

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
                        self.change_x = (dist_x / distancia_total) * (self.velocidade / 2)
                        self.change_y = (dist_y / distancia_total) * (self.velocidade / 2)
                    else:
                        if len(self.caminho_atual) > 1:
                            self.caminho_atual.pop(0)
                        else:
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
            self.center_x = max(0, min(LARGURA_MUNDO, novo_x))
            self.center_y = max(0, min(ALTURA_MUNDO, novo_y))
        self.atualizar_direcao()

# Inimigos Específicos herdando da base
class Slime(InimigoBase):
    def __init__(self):
        super().__init__(anims_slime(), velocidade=120, raio_visao=5, angulo_visao=360, vida=2)
        self.angulo_olhar = 0 #começa olhando pra esquerda

class Morcego(InimigoBase):
    def __init__(self):
        super().__init__(anims_morcego(), velocidade=240, raio_visao=8, angulo_visao=120, vida=3)
        self.angulo_olhar = 180
        self.colide_paredes = False # voa por cima das paredes

        # memória de curto prazo: some da linha de visão por até 2s sem desistir
        self.tempo_sem_ver_jogador = 0.0
        self.ultima_pos_jogador = None 

    def update_ia(self, mapa, jogador_x, jogador_y, delta_time=1/60):
        self.mapa = mapa
        if self.morto:
            return
        if self.atacando:
            self.change_x = 0
            self.change_y = 0
            return

        minha_pos_grid = pixel_para_grid(self.center_x, self.center_y)
        jogador_pos_grid = pixel_para_grid(jogador_x, jogador_y)

        if self.change_x != 0 or self.change_y != 0:
            self.angulo_olhar = math.degrees(math.atan2(-self.change_y, self.change_x))


        jogador_visivel = ia.is_player_in_fov(
            minha_pos_grid,
            jogador_pos_grid,
            self.angulo_olhar,
            self.angulo_visao,
            self.raio_visao,
            mapa
        )

        if jogador_visivel:
            self.tempo_sem_ver_jogador = 0.0
            self.ultima_pos_jogador = (jogador_x, jogador_y)
            self.estado = "perseguicao"
        elif self.estado == "perseguicao":
            self.tempo_sem_ver_jogador += delta_time
            if self.tempo_sem_ver_jogador >= TEMPO_MEMORIA_MORCEGO:
                self.estado = "patrulha"
                self.tempo_sem_ver_jogador = 0.0
                self.ultima_pos_jogador = None

        if self.estado == "perseguicao" and self.ultima_pos_jogador is not None:
            alvo_x, alvo_y = self.ultima_pos_jogador
            dist_x = alvo_x - self.center_x
            dist_y = alvo_y - self.center_y
            distancia_total = math.hypot(dist_x, dist_y)

            if distancia_total > 2:
                self.change_x = (dist_x / distancia_total) * self.velocidade
                self.change_y = (dist_y / distancia_total) * self.velocidade
            else:
                self.change_x = 0
                self.change_y = 0

            self.caminho_atual = [minha_pos_grid, pixel_para_grid(alvo_x, alvo_y)]
        else:
            self.estado = "patrulha"
            self.change_x = 0
            self.change_y = 0
            self.caminho_atual = [] # Limpa a linha de debug
            self.tempo_sem_ver_jogador = 0.0
            self.ultima_pos_jogador = None
