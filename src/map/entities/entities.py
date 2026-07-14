import arcade

class Jogador(arcade.Sprite):
    def __init__(self, imagem, escala):
        super().__init__(imagem, escala)
        self.velocidade = 5

    def update(self):
        # A movimentação baseada em change_x e change_y é processada aqui
        self.center_x += self.change_x
        self.center_y += self.change_y

class InimigoBase(arcade.Sprite):
    def __init__(self, imagem, escala, velocidade):
        super().__init__(imagem, escala)
        self.velocidade = velocidade
        self.estado = "patrulha" # Pode ser "patrulha" ou "perseguicao"

    def update_ia(self, mapa, jogador_pos):
        # Aqui é onde você vai integrar o seu arquivo ia_sistemas.py depois!
        # Exemplo: chamar o A* e alterar self.change_x e self.change_y para seguir o caminho
        pass

    def update(self):
        self.center_x += self.change_x
        self.center_y += self.change_y

# Inimigos Específicos herdando da base
class Slime(InimigoBase):
    def __init__(self, imagem, escala):
        # Slimes são mais lentos
        super().__init__(imagem, escala, velocidade=2)
        self.raio_visao = 4 

class Morcego(InimigoBase):
    def __init__(self, imagem, escala):
        # Morcegos são mais rápidos e enxergam mais longe
        super().__init__(imagem, escala, velocidade=4)
        self.raio_visao = 8
        self.angulo_visao = 120