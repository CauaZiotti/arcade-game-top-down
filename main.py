#Cauã Ziotti e Diego Breskovit

import arcade
import math
from entities.entities import Jogador, Slime, Morcego, TAMANHO_TILE, grid_para_pixel

LARGURA_TELA = 800
ALTURA_TELA = 600
TITULO = "Projeto Final - Arcade_Game c/ IA - Top Down"

#mapa do jogo, dividido por tiles de 40. 800x600 pixel, matriz de 20x15. 1=parede, 0=livre
MAPA_TESTE = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

class FasePrincipal(arcade.View):
    def __init__(self):
        super().__init__()
        
        # Gerenciadores de Sprites (SpriteList)
        self.lista_jogadores = None
        self.lista_inimigos = None
        self.lista_paredes = None #lista para o cenário

        self.modo_debug = False

    def setup(self):
        self.lista_jogadores = arcade.SpriteList()
        self.lista_inimigos = arcade.SpriteList()
        self.lista_paredes = arcade.SpriteList()

        # Lendo a matriz e criando as paredes
        for linha in range(len(MAPA_TESTE)):
            for coluna in range(len(MAPA_TESTE[0])):
                if MAPA_TESTE[linha][coluna] == 1:
                    parede = arcade.SpriteSolidColor(TAMANHO_TILE, TAMANHO_TILE, arcade.color.GRAY)
                    x, y = grid_para_pixel(linha, coluna)
                    parede.center_x = x
                    parede.center_y = y
                    self.lista_paredes.append(parede)

        #Jogador
        self.jogador = Jogador(20, 20, arcade.color.BLUE)
        self.jogador.center_x, self.jogador.center_y = grid_para_pixel(1, 1) # Nasce no canto superior esquerdo
        self.lista_jogadores.append(self.jogador)

        #Slime
        self.slime = Slime(15, arcade.color.APPLE_GREEN)
        self.slime.center_x, self.slime.center_y = grid_para_pixel(13, 18) # Nasce no canto inferior direito
        self.lista_inimigos.append(self.slime)

        #Morcego
        self.morcego = Morcego(15, arcade.color.PURPLE)
        self.morcego.center_x, self.morcego.center_y = grid_para_pixel(1, 18) # Nasce no canto superior direito
        self.lista_inimigos.append(self.morcego)

    def on_draw(self):
        """ Renderiza tudo na tela """
        self.clear() # Limpa a tela
        self.lista_paredes.draw()
        self.lista_inimigos.draw()
        self.lista_jogadores.draw()

        if self.modo_debug:
            self.desenhar_debug_visual()

    def desenhar_debug_visual(self):
        """ Cria a sombra e desenha os cálculos matemáticos da IA """
        pontos_sombra = [
            (0, 0), (LARGURA_TELA, 0), 
            (LARGURA_TELA, ALTURA_TELA), (0, ALTURA_TELA)
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
        # Atualiza a posição baseada na velocidade atual
        self.lista_jogadores.update()

        self.slime.update_ia(MAPA_TESTE, self.jogador.center_x, self.jogador.center_y)
        self.morcego.update_ia(MAPA_TESTE, self.jogador.center_x, self.jogador.center_y)
        self.lista_inimigos.update()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.TAB:
            self.modo_debug = not self.modo_debug

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