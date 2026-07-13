# Autotiling estilo dungeon: lê a matriz do mapa (1=parede/vazio, 0=chão) e
# monta o cenário como no tileset de referência:
#   - salas escavadas na escuridão (parede longe do chão nem é desenhada)
#   - paredes ao norte do chão têm 2 camadas: FACE de tijolos + CAPA de pedras em cima
#   - demais bordas ganham a pedra arredondada virada para o lado do chão
#
# Classificação em 2 passadas:
#   1) cada célula vira CHAO, FACE (parede com chão logo ao sul), CAPA (parede
#      encostada em chão/face) ou VAZIO (parede profunda, fica só o fundo escuro)
#   2) cada CAPA escolhe canto/borda olhando onde tem CHAO ou FACE em volta
#
# Posições no Tileset.png (grade de 16px, coluna/linha contadas do topo),
# usando a "sala grande" como template (colunas 17-24, linhas 1-6):
#   (17,1) canto sup-esq | (18..23,1) capa superior | (24,1) canto sup-dir
#   (18..23,2) face de tijolos
#   (17,3..5) borda esquerda | (18..23,3..5) chão | (24,3..5) borda direita
#   (17,6) canto inf-esq | (18..23,6) capa inferior | (24,6) canto inf-dir

import arcade
from sprites.carregador import fatiar

CAMINHO_TILESET = "Assets/Tileset/Tileset.png"
TILE_PX = 16

CANTO_SUP_ESQ = (17, 1)
CANTO_SUP_DIR = (24, 1)
CANTO_INF_ESQ = (17, 6)
CANTO_INF_DIR = (24, 6)
CAPAS_SUP = [(c, 1) for c in range(18, 24)]
CAPAS_INF = [(c, 6) for c in range(18, 24)]
BORDA_ESQ = (17, 3)
BORDA_DIR = (24, 3)
FACES = [(c, 2) for c in range(18, 24)]
CHAOS = [(c, l) for l in range(3, 6) for c in range(18, 24)]

RECT_PORTA = arcade.LBWH(10 * TILE_PX, 8 * TILE_PX, 32, 32)  # porta fechada 2x2 tiles


class Tileset:
    def __init__(self):
        self.sheet = arcade.load_spritesheet(CAMINHO_TILESET)
        self.cache = {}

    def tex(self, col, lin):
        if (col, lin) not in self.cache:
            rect = arcade.LBWH(col * TILE_PX, lin * TILE_PX, TILE_PX, TILE_PX)
            self.cache[(col, lin)] = self.sheet.get_texture(rect)
        return self.cache[(col, lin)]


def _variacao(lista, linha, coluna):
    """Variação fixa (determinística) pela posição, pra não piscar entre frames."""
    return lista[(linha * 7 + coluna * 13) % len(lista)]


CHAO, FACE, CAPA, VAZIO = "chao", "face", "capa", "vazio"

def _classificar(mapa):
    linhas, colunas = len(mapa), len(mapa[0])

    def chao(l, c):
        return 0 <= l < linhas and 0 <= c < colunas and mapa[l][c] == 0

    tipo = [[VAZIO] * colunas for _ in range(linhas)]
    for l in range(linhas):
        for c in range(colunas):
            if mapa[l][c] == 0:
                tipo[l][c] = CHAO
            elif chao(l + 1, c) and not chao(l - 1, c) and not chao(l, c - 1) and not chao(l, c + 1):
                tipo[l][c] = FACE  # parede reta com chão logo abaixo = tijolos

    # capa = parede que encosta (8 direções) em chão ou face
    for l in range(linhas):
        for c in range(colunas):
            if tipo[l][c] != VAZIO:
                continue
            for dl in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    ll, cc = l + dl, c + dc
                    if 0 <= ll < linhas and 0 <= cc < colunas and tipo[ll][cc] in (CHAO, FACE):
                        tipo[l][c] = CAPA
                        break
                if tipo[l][c] == CAPA:
                    break
    return tipo


def _tile_capa(tipo, l, c):
    """Escolhe canto/borda da capa de pedras olhando o que tem em volta.

    Dois testes diferentes:
      - chão de verdade (ch): decide os CANTOS convexos — a face de tijolo NÃO
        pode contar aqui, senão o fim de uma fileira de tijolos vira capa reta
        em vez de pedra de canto (bug nas bocas de corredor e pilastras)
      - aberto (ab = chão ou face): decide bordas retas e quinas diagonais
    """
    def ab(ll, cc):
        return 0 <= ll < len(tipo) and 0 <= cc < len(tipo[0]) and tipo[ll][cc] in (CHAO, FACE)

    def ch(ll, cc):
        return 0 <= ll < len(tipo) and 0 <= cc < len(tipo[0]) and tipo[ll][cc] == CHAO

    n, s = ab(l - 1, c), ab(l + 1, c)
    e, w = ab(l, c + 1), ab(l, c - 1)
    cn, cs = ch(l - 1, c), ch(l + 1, c)
    ce, cw = ch(l, c + 1), ch(l, c - 1)
    ne, nw = ab(l - 1, c + 1), ab(l - 1, c - 1)
    se, sw = ab(l + 1, c + 1), ab(l + 1, c - 1)

    # cantos convexos: chão de verdade em duas direções ortogonais
    if cs and ce and not cn and not cw: return CANTO_SUP_ESQ
    if cs and cw and not cn and not ce: return CANTO_SUP_DIR
    if cn and ce and not cs and not cw: return CANTO_INF_ESQ
    if cn and cw and not cs and not ce: return CANTO_INF_DIR
    # bordas retas (prioriza o lado aberto; chão ou face contam)
    if s and not n: return _variacao(CAPAS_SUP, l, c)
    if n and not s: return _variacao(CAPAS_INF, l, c)
    if e and not w: return BORDA_ESQ
    if w and not e: return BORDA_DIR
    if n and s: return _variacao(CAPAS_SUP, l, c)
    if e and w: return BORDA_ESQ
    # só diagonais abertas: quinas externas (degraus entre estruturas)
    if se and not (sw or ne or nw): return CANTO_SUP_ESQ
    if sw and not (se or ne or nw): return CANTO_SUP_DIR
    if ne and not (nw or se or sw): return CANTO_INF_ESQ
    if nw and not (ne or se or sw): return CANTO_INF_DIR
    # dois abertos do mesmo lado vertical: é continuação de parede lateral
    if ne and se and not (nw or sw): return BORDA_ESQ
    if nw and sw and not (ne or se): return BORDA_DIR
    if se or sw: return _variacao(CAPAS_SUP, l, c)
    return _variacao(CAPAS_INF, l, c)


class SpriteAnimado(arcade.Sprite):
    """Sprite decorativo com animação em loop (tocha, etc)."""
    def __init__(self, texturas, escala, x, y, duracao_frame=0.15):
        super().__init__(texturas[0], scale=escala, center_x=x, center_y=y)
        self.texturas = texturas
        self.duracao_frame = duracao_frame
        self.indice = 0
        self.tempo = 0.0

    def update_animation(self, delta_time: float = 1/60, *args, **kwargs):
        self.tempo += delta_time
        if self.tempo >= self.duracao_frame:
            self.tempo -= self.duracao_frame
            self.indice = (self.indice + 1) % len(self.texturas)
            self.texture = self.texturas[self.indice]


def construir_mapa(mapa, tamanho_tile, grid_para_pixel):
    """Monta as SpriteLists de chão, paredes e decoração automática (tochas/banners
    espalhados pelas faces de tijolo, como no mapa de referência)."""
    tileset = Tileset()
    escala = tamanho_tile / TILE_PX
    lista_chao = arcade.SpriteList()
    lista_paredes = arcade.SpriteList()
    lista_decor = arcade.SpriteList()

    texturas_tocha = fatiar("Assets/Objects/Torch.png", 16, 16)
    textura_banner = fatiar("Assets/Objects/Banner_1.png", 16, 16)[0]

    tipo = _classificar(mapa)
    linhas, colunas = len(mapa), len(mapa[0])

    for l in range(linhas):
        for c in range(colunas):
            x, y = grid_para_pixel(l, c)
            t = tipo[l][c]
            if t == CHAO:
                col, lin = _variacao(CHAOS, l, c)
                lista_chao.append(arcade.Sprite(tileset.tex(col, lin), scale=escala, center_x=x, center_y=y))
            elif t == FACE:
                col, lin = _variacao(FACES, l, c)
                lista_paredes.append(arcade.Sprite(tileset.tex(col, lin), scale=escala, center_x=x, center_y=y))
                # decoração automática pendurada nos tijolos
                assinatura = (l * 31 + c * 17) % 7
                if assinatura == 0:
                    lista_decor.append(SpriteAnimado(texturas_tocha, escala, x, y))
                elif assinatura == 3:
                    lista_decor.append(arcade.Sprite(textura_banner, scale=escala, center_x=x, center_y=y))
            elif t == CAPA:
                col, lin = _tile_capa(tipo, l, c)
                lista_paredes.append(arcade.Sprite(tileset.tex(col, lin), scale=escala, center_x=x, center_y=y))
                # parede sul exposta pro vazio ganha a face de tijolos por fora (como na referência)
                eh_capa_inferior = (col, lin) in ((CANTO_INF_ESQ, CANTO_INF_DIR) + tuple(CAPAS_INF))
                if eh_capa_inferior and l + 1 < linhas and tipo[l + 1][c] == VAZIO:
                    xf, yf = grid_para_pixel(l + 1, c)
                    colf, linf = _variacao(FACES, l + 1, c)
                    lista_paredes.append(arcade.Sprite(tileset.tex(colf, linf), scale=escala, center_x=xf, center_y=yf))

    return lista_chao, lista_paredes, lista_decor


def sprite_objeto(caminho, frame_larg, frame_alt, x, y, escala):
    """Objeto decorativo estático (baú, barril, poção...): usa o 1º frame do sheet."""
    return arcade.Sprite(fatiar(caminho, frame_larg, frame_alt)[0], scale=escala, center_x=x, center_y=y)


def sprite_porta(x, y, escala):
    """Porta de madeira fechada (2x2 tiles do tileset), decorativa sobre a parede."""
    tileset = Tileset()
    return arcade.Sprite(tileset.sheet.get_texture(RECT_PORTA), scale=escala, center_x=x, center_y=y)
