import arcade
from entities.entities import LARGURA_TELA, ALTURA_TELA

COR_FUNDO_VITORIA = (12, 32, 18)
COR_FUNDO_DERROTA = (32, 12, 14)


class TelaFim(arcade.View):

    def __init__(self, vitoria):
        super().__init__()
        self.vitoria = vitoria
        self.background_color = COR_FUNDO_VITORIA if vitoria else COR_FUNDO_DERROTA
        cx, cy = LARGURA_TELA / 2, ALTURA_TELA / 2

        titulo_texto = "FASE CONCLUÍDA!" if vitoria else "GAME OVER"
        cor_titulo = arcade.color.LIGHT_GREEN if vitoria else arcade.color.RED_DEVIL
        self.titulo = arcade.Text(
            titulo_texto, cx, cy + 50, cor_titulo, 48,
            anchor_x="center", bold=True,
        )

        subtitulo_texto = (
            "Você eliminou todos os inimigos da masmorra."
            if vitoria else
            "Você foi derrotado pelos inimigos da masmorra."
        )
        self.subtitulo = arcade.Text(
            subtitulo_texto, cx, cy, arcade.color.WHITE, 16, anchor_x="center",
        )
        self.instrucao = arcade.Text(
            "ENTER: jogar novamente      ESC: sair",
            cx, cy - 50, arcade.color.LIGHT_GRAY, 14, anchor_x="center",
        )

    def on_show_view(self):
        self.window.background_color = self.background_color

    def on_draw(self):
        self.clear()
        self.titulo.draw()
        self.subtitulo.draw()
        self.instrucao.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            from views.tela_jogo import TelaJogo
            tela_jogo = TelaJogo()
            tela_jogo.setup()
            self.window.show_view(tela_jogo)
        elif key == arcade.key.ESCAPE:
            arcade.exit()
