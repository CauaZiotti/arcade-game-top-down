import arcade

COR_VIDA_CHEIA = arcade.color.RED
COR_VIDA_VAZIA = (70, 30, 30)


class HUD:
    """HUD desenhado em espaço de tela: usa uma câmera própria (parada, sem
    seguir o jogador) pra ficar sempre fixo no mesmo canto, independente de
    pra onde a câmera do mundo estiver olhando.

    Mostra as informações relevantes ao jogador pedidas no enunciado: vida
    atual, o objetivo da fase (inimigos restantes -> pegar a chave) e o
    status de efeitos temporários (poção de velocidade).
    """

    def __init__(self, largura_tela, altura_tela):
        self.camera = arcade.Camera2D()

        self.texto_objetivo = arcade.Text(
            "", 18, altura_tela - 58, arcade.color.LIGHT_GRAY, 14
        )
        self.texto_status = arcade.Text(
            "", 18, altura_tela - 78, arcade.color.LIGHT_BLUE, 13, bold=True
        )
        self.texto_ajuda = arcade.Text(
            "WASD/Setas: mover   ESPAÇO: atacar   TAB: modo debug (IA)",
            18, 16, arcade.color.LIGHT_GRAY, 12,
        )
        self._largura_coracao = 20
        self._x_coracoes = 18
        self._y_coracoes = altura_tela - 34
        self._vida = 0
        self._vida_maxima = 0

    def atualizar(self, jogador, texto_objetivo):
        self._vida = jogador.vida
        self._vida_maxima = jogador.vida_maxima
        self.texto_objetivo.text = texto_objetivo
        if jogador.tempo_velocidade_extra > 0:
            self.texto_status.text = f"Velocidade! ({jogador.tempo_velocidade_extra:.1f}s)"
        else:
            self.texto_status.text = ""

    def desenhar(self):
        with self.camera.activate():
            for i in range(self._vida_maxima):
                cor = COR_VIDA_CHEIA if i < self._vida else COR_VIDA_VAZIA
                cx = self._x_coracoes + i * self._largura_coracao
                arcade.draw_circle_filled(cx, self._y_coracoes, 8, cor)
            self.texto_objetivo.draw()
            if self.texto_status.text:
                self.texto_status.draw()
            self.texto_ajuda.draw()
