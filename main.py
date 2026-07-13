#Cauã Ziotti e Diego Breskovit

import arcade
import arcade.math
import math
from entities.entities import (
    Jogador, Slime, Morcego,
    TAMANHO_TILE, ESCALA, LARGURA_TELA, ALTURA_TELA,
    definir_mundo, grid_para_pixel,
)
import entities.entities as ent
from sprites.tiles import construir_mapa, sprite_objeto, sprite_porta

TITULO = "Projeto Final - Arcade_Game c/ IA - Top Down"

# Mundo maior que a tela: matriz 30x40 tiles de 48px => 1920x1440 pixels.
# A câmera (janela de 960x720) segue o personagem.
LINHAS_MAPA = 30
COLUNAS_MAPA = 40

# salas e corredores escavados na escuridão: (linha_ini, col_ini, linha_fim, col_fim)
AREAS_LIVRES = [
    (4, 3, 10, 14),    # sala 1 (spawn, canto superior esquerdo)
    (3, 22, 11, 36),   # sala 2 (superior direita)
    (16, 2, 26, 12),   # sala 3 (inferior esquerda)
    (17, 17, 25, 26),  # sala 4 (centro-baixo)
    (15, 31, 26, 37),  # sala 5 (inferior direita)
    (6, 14, 7, 22),    # corredor sala 1 -> sala 2
    (10, 6, 16, 7),    # corredor sala 1 -> sala 3
    (11, 33, 15, 34),  # corredor sala 2 -> sala 5
    (20, 12, 21, 17),  # corredor sala 3 -> sala 4
    (20, 26, 21, 31),  # corredor sala 4 -> sala 5
]

def criar_mapa():
    """Gera a matriz do mundo: começa tudo parede (1) e escava as áreas livres (0)."""
    mapa = [[1] * COLUNAS_MAPA for _ in range(LINHAS_MAPA)]
    for l1, c1, l2, c2 in AREAS_LIVRES:
        for l in range(l1, l2 + 1):
            for c in range(c1, c2 + 1):
                mapa[l][c] = 0
    # pilastra no meio da sala 2 (vira paredão com face de tijolos, como na referência)
    for l in range(6, 9):
        for c in range(28, 31):
            mapa[l][c] = 1
    return mapa

MAPA = criar_mapa()

# objetos decorativos espalhados: (arquivo, larg_frame, alt_frame, linha, coluna)
OBJETOS_DECORACAO = [
    ("Assets/Objects/Chest_1.png", 16, 16, 4, 5),      # baú encostado na parede da sala 1
    ("Assets/Objects/Barrel_1.png", 16, 16, 16, 3),    # barris na sala 3
    ("Assets/Objects/Barrel_2.png", 16, 16, 17, 3),
    ("Assets/Objects/Red_potion.png", 16, 16, 24, 10),
    ("Assets/Objects/Blue_potion.png", 16, 16, 4, 24),
]
PORTA_DECORACAO = (1.5, 25.5)  # porta 2x2 no muro norte da sala 2

ALCANCE_ATAQUE_JOGADOR = TAMANHO_TILE * 1.2   # raio da espadada
ALCANCE_ATAQUE_INIMIGO = TAMANHO_TILE * 0.8   # inimigo perto o bastante começa a atacar
ALCANCE_DANO_INIMIGO = TAMANHO_TILE * 0.45    # encostou de verdade = jogador morre

class FasePrincipal(arcade.View):
    def __init__(self):
        super().__init__()

        # Gerenciadores de Sprites (SpriteList)
        self.lista_jogadores = None
        self.lista_inimigos = None
        self.lista_chao = None
        self.lista_paredes = None
        self.lista_decor = None

        self.camera = None
        self.modo_debug = False
        self.texto_fim = arcade.Text(
            "", LARGURA_TELA / 2, ALTURA_TELA / 2,
            arcade.color.WHITE, 40, anchor_x="center", anchor_y="center", bold=True,
        )

    def setup(self):
        self.background_color = (24, 20, 37)
        definir_mundo(LINHAS_MAPA, COLUNAS_MAPA)

        self.camera = arcade.Camera2D()

        self.lista_jogadores = arcade.SpriteList()
        self.lista_inimigos = arcade.SpriteList()

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

        #Jogador (colide com as paredes da matriz)
        self.jogador = Jogador(MAPA)
        self.jogador.center_x, self.jogador.center_y = grid_para_pixel(7, 8) # Nasce na sala 1
        self.lista_jogadores.append(self.jogador)

        #Inimigos: (classe, linha, coluna)
        for classe, linha, coluna in [
            (Slime, 21, 21),   # sala 4
            (Slime, 21, 7),    # sala 3
            (Morcego, 7, 25),  # sala 2
            (Morcego, 20, 34), # sala 5
        ]:
            inimigo = classe()
            inimigo.center_x, inimigo.center_y = grid_para_pixel(linha, coluna)
            self.lista_inimigos.append(inimigo)

        # câmera já nasce em cima do jogador
        self.camera.position = self.posicao_camera_alvo()
        self.texto_fim.text = ""

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
            self.lista_inimigos.draw(pixelated=True)
            self.lista_jogadores.draw(pixelated=True)

            if self.modo_debug:
                self.desenhar_debug_visual()

        # GUI fora da câmera do mundo (fica fixa na tela)
        if self.texto_fim.text:
            self.texto_fim.draw()

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
        self.lista_jogadores.update(delta_time)

        for inimigo in self.lista_inimigos:
            if not inimigo.morto and not self.jogador.morto:
                inimigo.update_ia(MAPA, self.jogador.center_x, self.jogador.center_y)
        self.lista_inimigos.update(delta_time)

        # Combate: inimigo vivo perto do jogador ataca; encostou, mata
        if not self.jogador.morto:
            for inimigo in self.lista_inimigos:
                if inimigo.morto:
                    continue
                dist = math.hypot(inimigo.center_x - self.jogador.center_x,
                                  inimigo.center_y - self.jogador.center_y)
                if dist < ALCANCE_ATAQUE_INIMIGO:
                    inimigo.atacar()
                if dist < ALCANCE_DANO_INIMIGO:
                    self.jogador.morrer()
                    self.texto_fim.text = "GAME OVER - aperte R"

        if not self.jogador.morto and all(i.morto for i in self.lista_inimigos):
            self.texto_fim.text = "FASE LIMPA!"

        # Avança os keyframes de todo mundo
        self.lista_jogadores.update_animation(delta_time)
        self.lista_inimigos.update_animation(delta_time)
        self.lista_decor.update_animation(delta_time)

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

        if self.jogador.morto:
            return

        if key == arcade.key.SPACE:
            self.jogador.atacar()
            # espadada acerta inimigos no raio de alcance
            for inimigo in self.lista_inimigos:
                dist = math.hypot(inimigo.center_x - self.jogador.center_x,
                                  inimigo.center_y - self.jogador.center_y)
                if dist < ALCANCE_ATAQUE_JOGADOR:
                    inimigo.morrer()

        if key == arcade.key.W or key == arcade.key.UP: self.jogador.change_y = self.jogador.velocidade
        elif key == arcade.key.S or key == arcade.key.DOWN: self.jogador.change_y = -self.jogador.velocidade
        elif key == arcade.key.A or key == arcade.key.LEFT: self.jogador.change_x = -self.jogador.velocidade
        elif key == arcade.key.D or key == arcade.key.RIGHT: self.jogador.change_x = self.jogador.velocidade

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.W, arcade.key.S, arcade.key.UP, arcade.key.DOWN]: self.jogador.change_y = 0
        elif key in [arcade.key.A, arcade.key.D, arcade.key.LEFT, arcade.key.RIGHT]: self.jogador.change_x = 0

def main():
    janela = arcade.Window(LARGURA_TELA, ALTURA_TELA, TITULO)
    fase = FasePrincipal()
    fase.setup()
    janela.show_view(fase)
    arcade.run()

if __name__ == "__main__":
    main()
