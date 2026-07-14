#Cauã Ziotti e Diego Breskovit

import arcade
from entities.entities import LARGURA_TELA, ALTURA_TELA
from views.tela_inicial import TelaInicial

TITULO = "Projeto Final - Arcade_Game c/ IA - Top Down"

def main():
    janela = arcade.Window(LARGURA_TELA, ALTURA_TELA, TITULO)
    janela.show_view(TelaInicial())
    arcade.run()

if __name__ == "__main__":
    main()
