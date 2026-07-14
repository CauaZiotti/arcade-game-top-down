import math
from sprites.carregador import fatiar
from sprites.tiles import SpriteAnimado

# ==========================================
# Poções
# ==========================================
DURACAO_POCAO_VELOCIDADE = 3.5  # segundos
FATOR_POCAO_VELOCIDADE = 1.7    # multiplicador de velocidade enquanto o efeito dura
CURA_POCAO_VERMELHA = 1


class Coletavel(SpriteAnimado):

    def __init__(self, caminho, frame_larg, x, y, escala, raio_colisao, efeito=None):
        texturas = fatiar(caminho, frame_larg, 16)
        super().__init__(texturas, escala, x, y, duracao_frame=0.15)
        self._raio_colisao = raio_colisao
        self._efeito = efeito
        self.coletada = False

    def tentar_coletar(self, jogador):
        if self.coletada:
            return False
        dist = math.hypot(jogador.center_x - self.center_x, jogador.center_y - self.center_y)
        if dist >= self._raio_colisao:
            return False
        self.coletada = True
        if self._efeito:
            self._efeito(jogador)
        self.remove_from_sprite_lists()
        return True


def pocao_azul(x, y, escala, raio_colisao):
    """Poção azul: aumenta a velocidade do jogador por um tempo curto."""
    efeito = lambda jogador: jogador.ativar_velocidade_extra(FATOR_POCAO_VELOCIDADE, DURACAO_POCAO_VELOCIDADE)
    return Coletavel("Assets/Objects/Blue_potion.png", 16, x, y, escala, raio_colisao, efeito)


def pocao_vermelha(x, y, escala, raio_colisao):
    """Poção vermelha: cura 1 vida do jogador."""
    efeito = lambda jogador: jogador.curar(CURA_POCAO_VERMELHA)
    return Coletavel("Assets/Objects/Red_potion.png", 16, x, y, escala, raio_colisao, efeito)


def criar_chave(x, y, escala, raio_colisao):
    return Coletavel("Assets/Objects/Key_chest_2.png", 15, x, y, escala, raio_colisao)


# ==========================================
# Baú (objetivo final)
# ==========================================
class Bau(SpriteAnimado):
    """Baú da masmorra: começa fechado. Abre quando o último inimigo cai,
    revelando a chave da vitória."""

    def __init__(self, x, y, escala):
        texturas = fatiar("Assets/Objects/Chest_2.png", 16, 16)
        super().__init__(texturas, escala, x, y)
        self.esta_aberto = False

    def update_animation(self, delta_time=1 / 60, *args, **kwargs):
        pass  # não animado: só alterna entre fechado (índice 0) e aberto (índice 1)

    def abrir(self):
        if not self.esta_aberto:
            self.esta_aberto = True
            self.indice = 1
            self.texture = self.texturas[1]


# ==========================================
# Armadilhas
# ==========================================
class ArmadilhaUrso(SpriteAnimado):
    """Armadilha de urso: obstáculo escondido no chão de um corredor. Dispara
    uma única vez quando o jogador pisa nela (causa dano e fica visualmente
    'estourada', sem machucar de novo)."""

    DANO = 1

    def __init__(self, x, y, escala, raio_colisao):
        texturas = fatiar("Assets/Objects/Bear_trap.png", 16, 16)
        super().__init__(texturas, escala, x, y)
        self._raio_colisao = raio_colisao
        self.armada = True

    def update_animation(self, delta_time=1 / 60, *args, **kwargs):
        pass  # estado muda só quando dispara, não tem ciclo de animação

    def verificar_colisao(self, jogador):
        if not self.armada or jogador.morto:
            return
        dist = math.hypot(jogador.center_x - self.center_x, jogador.center_y - self.center_y)
        if dist < self._raio_colisao:
            self.armada = False
            self.indice = 1
            self.texture = self.texturas[1]
            jogador.receber_dano(self.DANO)


class ArmadilhaEspinho(SpriteAnimado):
    """Armadilha de espinhos: ciclo retraído -> subindo -> estendido -> retraído.
    Só machuca enquanto os espinhos estão totalmente pra fora; a invulnerabilidade
    do próprio jogador evita dano contínuo enquanto ele atravessa. `atraso_fase`
    deixa várias armadilhas fora de sincronia entre si."""

    DANO = 1
    DURACAO_RETRAIDO = 1.4
    DURACAO_SUBINDO = 0.3
    DURACAO_ESTENDIDO = 0.9
    _CICLO = DURACAO_RETRAIDO + DURACAO_SUBINDO + DURACAO_ESTENDIDO

    def __init__(self, x, y, escala, raio_colisao, atraso_fase=0.0):
        texturas = fatiar("Assets/Objects/Spike_trap.png", 16, 16)
        super().__init__(texturas, escala, x, y)
        self._raio_colisao = raio_colisao
        self.tempo = atraso_fase

    def update_animation(self, delta_time=1 / 60, *args, **kwargs):
        self.tempo += delta_time
        t = self.tempo % self._CICLO
        if t < self.DURACAO_RETRAIDO:
            self.indice = 0
        elif t < self.DURACAO_RETRAIDO + self.DURACAO_SUBINDO:
            self.indice = 1
        else:
            self.indice = 2
        self.texture = self.texturas[self.indice]

    @property
    def perigosa(self):
        return self.indice == 2

    def verificar_colisao(self, jogador):
        if not self.perigosa or jogador.morto:
            return
        dist = math.hypot(jogador.center_x - self.center_x, jogador.center_y - self.center_y)
        if dist < self._raio_colisao:
            jogador.receber_dano(self.DANO)
