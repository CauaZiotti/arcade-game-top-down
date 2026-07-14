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
TEMPO_COOLDOWN_ATAQUE = 0.5  # segundos em idle após o ataque antes de poder atacar de novo
INTERVALO_RECALCULO_CAMINHO = 10  # frames entre buscas completas de A* durante a perseguição
TEMPO_MEMORIA_MORCEGO = 2.0  # segundos que o morcego continua buscando após perder o jogador de vista
TEMPO_INVULNERAVEL = 1.0  # segundos de invulnerabilidade do jogador após levar um golpe

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
        self.cooldown_ataque = 0.0
        self.vida_maxima = 1
        self.vida = 1
        self.tempo_flash_dano = 0.0
        self._anim_anterior = ("idle", "front")
        self.texture = anims[("idle", "front")][0]

    def _frames(self):
        return self.anims[(self.acao, self.direcao)]

    def atacar(self):
        # cooldown_ataque garante um tempo visível em idle entre um ataque e o
        # próximo — sem isso, um inimigo que fica parado dentro do alcance de
        # ataque reinicia a animação de ataque no frame seguinte ao fim da
        # anterior e nunca parece voltar pro idle.
        if self.morto or self.atacando or self.cooldown_ataque > 0:
            return
        self.atacando = True
        self.acao = "atack"
        self.frame = 0
        self.tempo_frame = 0.0

    def receber_dano(self, quantidade=1):
        """Reduz a vida da entidade; ao zerar, morre. Inimigos com mais de 1
        vida (morcego, slime) sobrevivem a um golpe e piscam brevemente pra
        avisar que foram atingidos mas ainda estão de pé."""
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
        # trocou de ação/direção? recomeça a animação do frame 0 (senão o índice
        # 'vaza' de uma animação pra outra e a troca fica truncada/pulada)
        chave = (self.acao, self.direcao)
        if chave != self._anim_anterior:
            self._anim_anterior = chave
            self.frame = 0
            self.tempo_frame = 0.0

        if self.cooldown_ataque > 0:
            self.cooldown_ataque -= delta_time

        if self.tempo_flash_dano > 0:
            # só mexe no alpha enquanto o flash está ativo (e no frame em que
            # ele expira) — assim não conflita com o próprio piscar de
            # invulnerabilidade que o Jogador controla em seu update()
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
        self.velocidade_base = 220  # mais devagar que antes (era 300), dá mais peso aos golpes dos inimigos
        self.velocidade = self.velocidade_base
        self.tempo_velocidade_extra = 0.0  # duração restante do bônus da poção azul
        # caixa de colisão menor que o sprite (o corpo do cavaleiro não preenche os 96px)
        self.meia_larg = 16
        self.meia_alt = 14

        self.vida_maxima = 3
        self.vida = self.vida_maxima
        self.tempo_invulneravel = 0.0

    def receber_dano(self, quantidade=1):
        """Um golpe inimigo tira 1 vida e concede uma janela de invulnerabilidade —
        sem isso, encostar num inimigo por vários frames seguidos zerava a vida
        de uma vez só, o que na prática era a mesma morte instantânea de antes."""
        if self.morto or self.tempo_invulneravel > 0:
            return
        self.vida = max(0, self.vida - quantidade)
        self.tempo_invulneravel = TEMPO_INVULNERAVEL
        if self.vida <= 0:
            self.morrer()

    def curar(self, quantidade=1):
        """Efeito da poção vermelha."""
        self.vida = min(self.vida_maxima, self.vida + quantidade)

    def ativar_velocidade_extra(self, multiplicador, duracao):
        """Efeito da poção azul: acelera por `duracao` segundos. Uma nova poção
        durante o efeito só renova o tempo (não acumula multiplicador)."""
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

        # throttle do A*: evita rodar a busca completa a cada frame (60x/s)
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
            # Recalcula o caminho completo só quando o alvo muda de tile, o
            # caminho anterior acabou, ou já passou o intervalo de recálculo.
            # Rodar o A* inteiro a cada um dos 60 frames por segundo era o
            # maior custo da IA; entre recálculos, o inimigo continua seguindo
            # o caminho já calculado (a direção é recomputada todo frame, só
            # a busca em si é que fica mais espaçada).
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
        # Slimes são mais lentos, mas aguentam 2 golpes
        super().__init__(anims_slime(), velocidade=120, raio_visao=5, angulo_visao=360, vida=2)
        self.angulo_olhar = 0 #começa olhando pra esquerda

class Morcego(InimigoBase):
    def __init__(self):
        # Morcegos são mais rápidos, enxergam longe (8 blocos), cone de 120 graus,
        # e aguentam 3 golpes — o mais resistente dos dois inimigos
        super().__init__(anims_morcego(), velocidade=240, raio_visao=8, angulo_visao=120, vida=3)
        self.angulo_olhar = 180
        self.colide_paredes = False # voa por cima das paredes

        # memória de curto prazo: some da linha de visão por até 2s sem desistir
        self.tempo_sem_ver_jogador = 0.0
        self.ultima_pos_jogador = None # último (x, y) em pixels onde o viu

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

        # 1. Atualiza a direção do olhar
        if self.change_x != 0 or self.change_y != 0:
            self.angulo_olhar = math.degrees(math.atan2(-self.change_y, self.change_x))

        # 2. Usa Raycasting e FOV: a visão É bloqueada por paredes. Só o VOO
        # ignora paredes (colide_paredes=False lá embaixo) — ele pode voar por
        # cima de um obstáculo que já viu o jogador atravessar, mas não
        # enxerga através de paredes.
        jogador_visivel = ia.is_player_in_fov(
            minha_pos_grid,
            jogador_pos_grid,
            self.angulo_olhar,
            self.angulo_visao,
            self.raio_visao,
            mapa
        )

        # 3. Máquina de Estados com memória de curto prazo: perder a linha de
        # visão por um instante (uma coluna passando na frente, um degrau de
        # parede) não faz o morcego esquecer o jogador na hora — ele guarda a
        # última posição vista e só desiste depois de TEMPO_MEMORIA_MORCEGO
        # segundos seguidos sem recuperar a visão.
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

        # 4. Perseguição (IGNORA PAREDES E O A*): mira no jogador enquanto
        # visível, ou na última posição conhecida enquanto ainda "lembra" dele
        if self.estado == "perseguicao" and self.ultima_pos_jogador is not None:
            alvo_x, alvo_y = self.ultima_pos_jogador
            dist_x = alvo_x - self.center_x
            dist_y = alvo_y - self.center_y
            distancia_total = math.hypot(dist_x, dist_y)

            if distancia_total > 2:
                # Voa direto para o alvo passando por cima de tudo
                self.change_x = (dist_x / distancia_total) * self.velocidade
                self.change_y = (dist_y / distancia_total) * self.velocidade
            else:
                self.change_x = 0
                self.change_y = 0

            # Para o Debug Visual funcionar, fingimos que o "caminho" é uma reta
            self.caminho_atual = [minha_pos_grid, pixel_para_grid(alvo_x, alvo_y)]
        else:
            self.estado = "patrulha"
            self.change_x = 0
            self.change_y = 0
            self.caminho_atual = [] # Limpa a linha de debug
            self.tempo_sem_ver_jogador = 0.0
            self.ultima_pos_jogador = None
