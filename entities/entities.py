import arcade

class Jogador(arcade.SpriteSolidColor):
    def __init__(self, largura, altura, cor):
        super().__init__(largura, altura, cor)
        self.velocidade = 5

    def update(self, *args, **kwargs):
        # A movimentação baseada em change_x e change_y é processada aqui
        self.center_x += self.change_x
        self.center_y += self.change_y

class InimigoBase(arcade.SpriteCircle):
    def __init__(self, raio, cor, velocidade):
        super().__init__(raio, cor)
        self.velocidade = velocidade
        self.estado = "patrulha" # Pode ser "patrulha" ou "perseguicao"

    def update_ia(self, mapa, jogador_pos):
        # Aqui é onde você vai integrar o seu arquivo ia_sistemas.py depois!
        # Exemplo: chamar o A* e alterar self.change_x e self.change_y para seguir o caminho
        pass

    def update(self, *args, **kwargs):
        self.center_x += self.change_x
        self.center_y += self.change_y

# Inimigos Específicos herdando da base
class Slime(InimigoBase):
    def __init__(self, raio, cor):
        # Slimes são mais lentos
        super().__init__(raio, cor, velocidade=2)
        self.raio_visao = 4 

class Morcego(InimigoBase):
    def __init__(self, raio, cor):
        # Morcegos são mais rápidos e enxergam mais longe
        super().__init__(raio, cor, velocidade=4)
        self.raio_visao = 8
        self.angulo_visao = 120