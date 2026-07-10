#Cauã Ziotti e Diego Breskovit

import arcade
from entities.entities import Jogador, Slime, Morcego

LARGURA_TELA = 800
ALTURA_TELA = 600
TITULO = "Projeto Final - Arcade_Game c/ IA - Top Down"

class FasePrincipal(arcade.View):
    def __init__(self):
        super().__init__()
        
        # Gerenciadores de Sprites (SpriteList)
        self.lista_jogadores = None
        self.lista_inimigos = None
        
        # Variáveis do jogador e cenário
        self.jogador = None
        self.morcego = None
        self.slime = None

    def setup(self):
        """ Inicializa o jogo e configura as entidades """
        self.lista_jogadores = arcade.SpriteList()
        self.lista_inimigos = arcade.SpriteList()

        # Instanciando o Jogador (substitua 'player.png' pela sua imagem)
        self.jogador = Jogador(16,16,arcade.color.BLUE)
        self.jogador.center_x = LARGURA_TELA / 2
        self.jogador.center_y = ALTURA_TELA / 2
        self.lista_jogadores.append(self.jogador)

        # Instanciando os Inimigos
        self.slime = Slime(16, arcade.color.APPLE_GREEN)
        self.slime.center_x = 200
        self.slime.center_y = 200
        
        self.morcego = Morcego(16, arcade.color.CRIMSON)
        self.morcego.center_x = 600
        self.morcego.center_y = 500

        self.lista_inimigos.append(self.slime)
        self.lista_inimigos.append(self.morcego)

    def on_draw(self):
        """ Renderiza tudo na tela """
        self.clear() # Limpa a tela
        
        self.lista_inimigos.draw()
        self.lista_jogadores.draw()

    def on_update(self, delta_time):
        """ Lógica do jogo atualizada a cada frame """
        # Atualiza a posição baseada na velocidade atual
        self.lista_jogadores.update()
        self.lista_inimigos.update()
        
        # Futuramente: Passar o delta_time para os cálculos da IA se necessário
        # self.slime.update_ia(mapa_matriz, (self.jogador.center_x, self.jogador.center_y))

    def on_key_press(self, key, modifiers):
        """ Lê o teclado para mover o jogador """
        if key == arcade.key.W or key == arcade.key.UP:
            self.jogador.change_y = self.jogador.velocidade
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.jogador.change_y = -self.jogador.velocidade
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.jogador.change_x = -self.jogador.velocidade
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.jogador.change_x = self.jogador.velocidade

    def on_key_release(self, key, modifiers):
        """ Zera a velocidade quando o jogador solta a tecla """
        if key == arcade.key.W or key == arcade.key.S or key == arcade.key.UP or key == arcade.key.DOWN:
            self.jogador.change_y = 0
        elif key == arcade.key.A or key == arcade.key.D or key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.jogador.change_x = 0

def main():
    janela = arcade.Window(LARGURA_TELA, ALTURA_TELA, TITULO)
    fase = FasePrincipal()
    fase.setup()
    janela.show_view(fase)
    arcade.run()

if __name__ == "__main__":
    main()