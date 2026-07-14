import arcade
import arcade.math
import math
from entities.entities import (
    Jogador, Slime, Morcego,
    TAMANHO_TILE, ESCALA, LARGURA_TELA, ALTURA_TELA,
    definir_mundo, grid_para_pixel,
)
import entities.entities as ent
from entities.objetos import (
    ArmadilhaUrso, ArmadilhaEspinho, Bau,
    pocao_azul, pocao_vermelha, criar_chave,
)
from sprites.tiles import construir_mapa, sprite_objeto, sprite_porta
from ui.hud import HUD

LINHAS_MAPA = 30
COLUNAS_MAPA = 40

AREAS_LIVRES = [
    (4, 3, 10, 14),    # sala 1 (spawn, canto superior esquerdo)
    (3, 22, 11, 36),   # sala 2 (superior direita)
    (16, 2, 28, 13),   # sala 3 (inferior esquerda, ampliada)
    (17, 17, 27, 28),  # sala 4 (centro-baixo, ampliada)
    (14, 30, 27, 38),  # sala 5 (inferior direita, ampliada)
    (6, 14, 7, 22),    # corredor sala 1 -> sala 2
    (10, 6, 16, 7),    # corredor sala 1 -> sala 3
    (11, 33, 15, 34),  # corredor sala 2 -> sala 5
    (20, 12, 21, 17),  # corredor sala 3 -> sala 4
    (20, 26, 21, 31),  # corredor sala 4 -> sala 5
]

def criar_mapa():
    mapa = [[1] * COLUNAS_MAPA for _ in range(LINHAS_MAPA)]
    for l1, c1, l2, c2 in AREAS_LIVRES:
        for l in range(l1, l2 + 1):
            for c in range(c1, c2 + 1):
                mapa[l][c] = 0
    
    for l in range(6, 9):
        for c in range(28, 31):
            mapa[l][c] = 1
    return mapa

MAPA = criar_mapa()

OBJETOS_DECORACAO = [
    ("Assets/Objects/Barrel_1.png", 16, 16, 16, 3),    # barris na sala 3
    ("Assets/Objects/Barrel_2.png", 16, 16, 17, 3),
    ("Assets/Objects/Barrel_1.png", 16, 16, 24, 20),   # barris na sala 4 (ampliada)
    ("Assets/Objects/Barrel_2.png", 16, 16, 17, 33),   # barril na sala 5 (ampliada)
]
PORTA_DECORACAO = (1.5, 25.5)  

POCOES = [
    ("azul", 4, 24),       # sala 2
    ("azul", 24, 35),      # sala 5
    ("vermelha", 24, 10),  # sala 3
    ("vermelha", 6, 6),    # sala 1, perto do spawn
    ("vermelha", 22, 24),  # sala 4
]

ARMADILHAS_URSO = [
    (13, 6),   # corredor sala 1 -> sala 3
    (20, 14),  # corredor sala 3 -> sala 4
]
ARMADILHAS_ESPINHO = [
    (6, 18, 0.0),   # corredor sala 1 -> sala 2
    (20, 28, 1.0),  # corredor sala 4 -> sala 5 (fase deslocada, fora de sincronia)
]

POSICAO_BAU = (4, 5)      # sala 1 — o mesmo canto onde o jogador nasce, pra fechar o ciclo
POSICAO_CHAVE = (4, 6.4)  # ao lado do baú, só aparece quando ele abre

ALCANCE_ATAQUE_JOGADOR = TAMANHO_TILE * 1.2   # raio da espadada
ALCANCE_ATAQUE_INIMIGO = TAMANHO_TILE * 0.8   # inimigo perto o bastante começa a atacar
ALCANCE_DANO_INIMIGO = TAMANHO_TILE * 0.45    # encostou de verdade = jogador leva dano
RAIO_COLETA = TAMANHO_TILE * 0.5              # alcance pra pegar poção/chave
RAIO_ARMADILHA = TAMANHO_TILE * 0.35          # alcance pra disparar armadilha

TEMPO_ANTES_DE_TROCAR_TELA = 1.2  # segundos pra deixar a animação de morte/vitória aparecer

# teclas de movimento agrupadas por direção (WASD + setas)
TECLAS_CIMA = (arcade.key.W, arcade.key.UP)
TECLAS_BAIXO = (arcade.key.S, arcade.key.DOWN)
TECLAS_ESQUERDA = (arcade.key.A, arcade.key.LEFT)
TECLAS_DIREITA = (arcade.key.D, arcade.key.RIGHT)
TECLAS_MOVIMENTO = TECLAS_CIMA + TECLAS_BAIXO + TECLAS_ESQUERDA + TECLAS_DIREITA


class TelaJogo(arcade.View):

    def __init__(self):
        super().__init__()

        # Gerenciadores de Sprites (SpriteList)
        self.lista_jogadores = None
        self.lista_inimigos = None
        self.lista_chao = None
        self.lista_paredes = None
        self.lista_decor = None
        self.lista_pocoes = None
        self.lista_armadilhas = None
        self.lista_objetivo = None  # baú + chave

        self.camera = None
        self.hud = None
        self.teclas_seguradas = set()
        self.modo_debug = False

        self.total_inimigos = 0
        self.bau = None
        self.chave = None
        self.fim_de_jogo = None       # None enquanto joga; True (vitória) ou False (derrota)
        self.tempo_para_trocar_tela = 0.0

    def setup(self):
        self.background_color = (24, 20, 37)
        definir_mundo(LINHAS_MAPA, COLUNAS_MAPA)

        self.camera = arcade.Camera2D()
        self.hud = HUD(LARGURA_TELA, ALTURA_TELA)

        self.lista_jogadores = arcade.SpriteList()
        self.lista_inimigos = arcade.SpriteList()
        self.lista_pocoes = arcade.SpriteList()
        self.lista_armadilhas = arcade.SpriteList()
        self.lista_objetivo = arcade.SpriteList()

        # Autotiling: chão, paredes (capas + faces de tijolo) e tochas/banners automáticos
        self.lista_chao, self.lista_paredes, self.lista_decor = construir_mapa(
            MAPA, TAMANHO_TILE, grid_para_pixel
        )

        # objetos decorativos e a porta
        for caminho, fl, fa, linha, coluna in OBJETOS_DECORACAO:
            x, y = grid_para_pixel(linha, coluna)
            self.lista_decor.append(sprite_objeto(caminho, fl, fa, x, y, ESCALA))
        x, y = grid_para_pixel(*PORTA_DECORACAO)
        self.lista_decor.append(sprite_porta(x, y, ESCALA))

        # poções: azul acelera, vermelha cura
        for tipo, linha, coluna in POCOES:
            x, y = grid_para_pixel(linha, coluna)
            fabrica = pocao_azul if tipo == "azul" else pocao_vermelha
            self.lista_pocoes.append(fabrica(x, y, ESCALA, RAIO_COLETA))

        # armadilhas: urso dispara uma vez, espinho pulsa em ciclo
        for linha, coluna in ARMADILHAS_URSO:
            x, y = grid_para_pixel(linha, coluna)
            self.lista_armadilhas.append(ArmadilhaUrso(x, y, ESCALA, RAIO_ARMADILHA))
        for linha, coluna, atraso in ARMADILHAS_ESPINHO:
            x, y = grid_para_pixel(linha, coluna)
            self.lista_armadilhas.append(ArmadilhaEspinho(x, y, ESCALA, RAIO_ARMADILHA, atraso))

        # baú: começa fechado, só abre quando o último inimigo cai (ver on_update)
        x, y = grid_para_pixel(*POSICAO_BAU)
        self.bau = Bau(x, y, ESCALA)
        self.lista_objetivo.append(self.bau)
        self.chave = None

        #Jogador (colide com as paredes da matriz)
        self.jogador = Jogador(MAPA)
        self.jogador.center_x, self.jogador.center_y = grid_para_pixel(7, 8) # Nasce na sala 1
        self.lista_jogadores.append(self.jogador)

        #Inimigos: (classe, linha, coluna)
        for classe, linha, coluna in [
            (Slime, 21, 21),   # sala 4
            (Slime, 21, 7),    # sala 3
            (Slime, 25, 11),   # sala 3 (área ampliada)
            (Morcego, 7, 25),  # sala 2
            (Morcego, 20, 34), # sala 5
            (Morcego, 24, 22), # sala 4 (área ampliada)
        ]:
            inimigo = classe()
            inimigo.center_x, inimigo.center_y = grid_para_pixel(linha, coluna)
            self.lista_inimigos.append(inimigo)
        self.total_inimigos = len(self.lista_inimigos)

        # câmera já nasce em cima do jogador
        self.camera.position = self.posicao_camera_alvo()
        self.teclas_seguradas.clear()
        self.fim_de_jogo = None
        self.tempo_para_trocar_tela = 0.0
        self.hud.atualizar(self.jogador, self._texto_objetivo(self.total_inimigos))

    def _texto_objetivo(self, inimigos_vivos):
        """Objetivo mostrado no HUD: primeiro elimine todos, depois pegue a chave."""
        if inimigos_vivos > 0:
            return f"Inimigos restantes: {inimigos_vivos}/{self.total_inimigos}"
        if self.chave is None or not self.chave.coletada:
            return "Baú aberto! Volte e pegue a chave para vencer."
        return "Chave em mãos!"

    def atualizar_movimento_jogador(self):
        if self.jogador.morto:
            self.jogador.change_x = 0
            self.jogador.change_y = 0
            return
        dx = (any(t in self.teclas_seguradas for t in TECLAS_DIREITA)
              - any(t in self.teclas_seguradas for t in TECLAS_ESQUERDA))
        dy = (any(t in self.teclas_seguradas for t in TECLAS_CIMA)
              - any(t in self.teclas_seguradas for t in TECLAS_BAIXO))
        magnitude = math.hypot(dx, dy)
        if magnitude == 0:
            self.jogador.change_x = 0
            self.jogador.change_y = 0
        else:
            self.jogador.change_x = (dx / magnitude) * self.jogador.velocidade
            self.jogador.change_y = (dy / magnitude) * self.jogador.velocidade

    def posicao_camera_alvo(self):
        """Centro da câmera: segue o jogador, sem mostrar nada fora do mundo."""
        x = max(LARGURA_TELA / 2, min(ent.LARGURA_MUNDO - LARGURA_TELA / 2, self.jogador.center_x))
        y = max(ALTURA_TELA / 2, min(ent.ALTURA_MUNDO - ALTURA_TELA / 2, self.jogador.center_y))
        return (x, y)

    def on_draw(self):
        """ Renderiza tudo na tela (pixelated mantém o pixel art nítido no zoom 3x) """
        self.clear()
        with self.camera.activate():
            self.lista_chao.draw(pixelated=True)
            self.lista_paredes.draw(pixelated=True)
            self.lista_decor.draw(pixelated=True)
            self.lista_armadilhas.draw(pixelated=True)
            self.lista_pocoes.draw(pixelated=True)
            self.lista_objetivo.draw(pixelated=True)
            self.lista_inimigos.draw(pixelated=True)
            self.lista_jogadores.draw(pixelated=True)

            if self.modo_debug:
                self.desenhar_debug_visual()

        self.hud.desenhar()

    def desenhar_debug_visual(self):
        """ Cria a sombra e desenha os cálculos matemáticos da IA """
        pontos_sombra = [
            (0, 0), (ent.LARGURA_MUNDO, 0),
            (ent.LARGURA_MUNDO, ent.ALTURA_MUNDO), (0, ent.ALTURA_MUNDO)
        ]
        arcade.draw_polygon_filled(pontos_sombra, (0, 0, 0, 100))

        # Roda o debug para TODOS os inimigos na tela
        for inimigo in self.lista_inimigos:
            raio_px = inimigo.raio_visao * TAMANHO_TILE

            # FOV (Círculo ou Cone)
            if inimigo.angulo_visao >= 360:
                arcade.draw_circle_outline(inimigo.center_x, inimigo.center_y, raio_px, arcade.color.YELLOW, 2)
            else:
                angulo_rad = math.radians(-inimigo.angulo_olhar)
                metade_fov_rad = math.radians(inimigo.angulo_visao / 2)

                x1 = inimigo.center_x + raio_px * math.cos(angulo_rad - metade_fov_rad)
                y1 = inimigo.center_y + raio_px * math.sin(angulo_rad - metade_fov_rad)
                arcade.draw_line(inimigo.center_x, inimigo.center_y, x1, y1, arcade.color.YELLOW, 2)

                x2 = inimigo.center_x + raio_px * math.cos(angulo_rad + metade_fov_rad)
                y2 = inimigo.center_y + raio_px * math.sin(angulo_rad + metade_fov_rad)
                arcade.draw_line(inimigo.center_x, inimigo.center_y, x2, y2, arcade.color.YELLOW, 2)

                xc = inimigo.center_x + raio_px * math.cos(angulo_rad)
                yc = inimigo.center_y + raio_px * math.sin(angulo_rad)
                arcade.draw_line(inimigo.center_x, inimigo.center_y, xc, yc, arcade.color.RED, 1)

            # Rota de Perseguição
            if inimigo.caminho_atual:
                for i in range(len(inimigo.caminho_atual) - 1):
                    p_atual = inimigo.caminho_atual[i]
                    p_prox = inimigo.caminho_atual[i+1]

                    x_a, y_a = grid_para_pixel(p_atual[0], p_atual[1])
                    x_b, y_b = grid_para_pixel(p_prox[0], p_prox[1])

                    arcade.draw_line(x_a, y_a, x_b, y_b, arcade.color.MAGENTA, 3)
                    arcade.draw_circle_filled(x_a, y_a, 4, arcade.color.MAGENTA)

                ultimo = inimigo.caminho_atual[-1]
                x_u, y_u = grid_para_pixel(ultimo[0], ultimo[1])
                arcade.draw_circle_filled(x_u, y_u, 4, arcade.color.MAGENTA)

    def on_update(self, delta_time):
        """ Lógica do jogo atualizada a cada frame """
        self.atualizar_movimento_jogador()
        self.lista_jogadores.update(delta_time)

        for inimigo in self.lista_inimigos:
            if not inimigo.morto and not self.jogador.morto:
                inimigo.update_ia(MAPA, self.jogador.center_x, self.jogador.center_y, delta_time)
        self.lista_inimigos.update(delta_time)

        if not self.jogador.morto:
            # Combate: inimigo vivo perto do jogador ataca; encostou, causa dano
            for inimigo in self.lista_inimigos:
                if inimigo.morto:
                    continue
                dist = math.hypot(inimigo.center_x - self.jogador.center_x,
                                  inimigo.center_y - self.jogador.center_y)
                if dist < ALCANCE_ATAQUE_INIMIGO:
                    inimigo.atacar()
                if dist < ALCANCE_DANO_INIMIGO:
                    self.jogador.receber_dano(1)

            # Armadilhas: urso dispara uma vez, espinho machuca enquanto estendido
            for armadilha in self.lista_armadilhas:
                armadilha.verificar_colisao(self.jogador)

            # Poções: some ao encostar e aplica o efeito
            for pocao in list(self.lista_pocoes):
                pocao.tentar_coletar(self.jogador)

        inimigos_vivos = sum(1 for i in self.lista_inimigos if not i.morto)

        if self.fim_de_jogo is None:
            if self.jogador.morto:
                self.fim_de_jogo = False
                self.tempo_para_trocar_tela = TEMPO_ANTES_DE_TROCAR_TELA
            else:
                if inimigos_vivos == 0 and not self.bau.esta_aberto:
                    self.bau.abrir()
                    x, y = grid_para_pixel(*POSICAO_CHAVE)
                    self.chave = criar_chave(x, y, ESCALA, RAIO_COLETA)
                    self.lista_objetivo.append(self.chave)
                if self.chave is not None and self.chave.tentar_coletar(self.jogador):
                    self.fim_de_jogo = True
                    self.tempo_para_trocar_tela = TEMPO_ANTES_DE_TROCAR_TELA
        else:
            self.tempo_para_trocar_tela -= delta_time
            if self.tempo_para_trocar_tela <= 0:
                from views.tela_fim import TelaFim
                self.window.show_view(TelaFim(vitoria=self.fim_de_jogo))

        self.hud.atualizar(self.jogador, self._texto_objetivo(inimigos_vivos))

        # Avança os keyframes de todo mundo
        self.lista_jogadores.update_animation(delta_time)
        self.lista_inimigos.update_animation(delta_time)
        self.lista_decor.update_animation(delta_time)
        self.lista_pocoes.update_animation(delta_time)
        self.lista_armadilhas.update_animation(delta_time)
        self.lista_objetivo.update_animation(delta_time)

        # câmera segue o personagem suavemente, presa aos limites do mundo
        self.camera.position = arcade.math.lerp_2d(
            self.camera.position, self.posicao_camera_alvo(), 0.12
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.TAB:
            self.modo_debug = not self.modo_debug
        if key == arcade.key.R:
            self.setup()
            return

        if key in TECLAS_MOVIMENTO:
            self.teclas_seguradas.add(key)

        if self.jogador.morto:
            return

        if key == arcade.key.SPACE:
            self.jogador.atacar()
            # espadada acerta inimigos no raio de alcance
            for inimigo in self.lista_inimigos:
                dist = math.hypot(inimigo.center_x - self.jogador.center_x,
                                  inimigo.center_y - self.jogador.center_y)
                if dist < ALCANCE_ATAQUE_JOGADOR:
                    inimigo.receber_dano(1)

    def on_key_release(self, key, modifiers):
        self.teclas_seguradas.discard(key)
