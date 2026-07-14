import arcade
from entities.entities import LARGURA_TELA, ALTURA_TELA

COR_FUNDO = (18, 14, 28)


class TelaInicial(arcade.View):
    """Tela de início: título, objetivo do jogo e controles, antes de entrar na fase."""

    def __init__(self):
        super().__init__()
        self.background_color = COR_FUNDO
        cx, cy = LARGURA_TELA / 2, ALTURA_TELA / 2

        self.titulo = arcade.Text(
            "MASMORRA TOP-DOWN", cx, cy + 150,
            arcade.color.WHITE, 40, anchor_x="center", bold=True,
        )
        self.subtitulo = arcade.Text(
            "IA aplicada a jogos — percepção, máquina de estados e A*",
            cx, cy + 108, arcade.color.LIGHT_GRAY, 15, anchor_x="center",
        )

        linhas = [
            "Objetivo: elimine todos os inimigos da masmorra para vencer.",
            "Você tem 3 vidas — cada golpe de inimigo tira uma.",
            "",
            "WASD ou Setas: mover      ESPAÇO: atacar      TAB: modo debug (IA)",
            "",
            "Pressione ENTER para começar",
        ]
        self.linhas = [
            arcade.Text(
                texto, cx, cy - 10 - i * 26,
                arcade.color.YELLOW if "ENTER" in texto else arcade.color.LIGHT_GRAY,
                16, anchor_x="center", bold=("ENTER" in texto),
            )
            for i, texto in enumerate(linhas)
        ]

    def on_show_view(self):
        self.window.background_color = COR_FUNDO

    def on_draw(self):
        self.clear()
        self.titulo.draw()
        self.subtitulo.draw()
        for linha in self.linhas:
            linha.draw()

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.ENTER, arcade.key.SPACE):
            from views.tela_jogo import TelaJogo
            tela_jogo = TelaJogo()
            tela_jogo.setup()
            self.window.show_view(tela_jogo)
