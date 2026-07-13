# Carrega os spritesheets e monta os dicionários de animação de cada entidade.
# Cada animação é uma lista de texturas; a chave é (acao, direcao).
# Direções: front, back, side (olhando p/ direita) e side_flip (espelhado p/ esquerda).

import arcade

ACOES = ["idle", "run", "atack", "dead"]
DIRECOES = ["front", "back", "side", "side_flip"]


def fatiar(caminho, frame_larg, frame_alt):
    """Fatia um spritesheet horizontal em N frames (N = largura da imagem / largura do frame)."""
    sheet = arcade.load_spritesheet(caminho)
    n = sheet.image.width // frame_larg
    return sheet.get_texture_grid(size=(frame_larg, frame_alt), columns=n, count=n)


def espelhar(texturas):
    return [t.flip_left_right() for t in texturas]


def completar(anims):
    """Preenche as direções/ações que o spritesheet não tem:
    - sem 'back'  -> usa o 'front'  (morcego e slime não têm vista de costas)
    - sem 'run'   -> usa o 'idle'   (morcego voa e slime pula com os mesmos frames)
    - 'side_flip' -> espelha o 'side' (as artes laterais olham para a direita)
    """
    for acao in ACOES:
        if (acao, "front") not in anims:
            base = "idle" if acao == "run" else acao
            anims[(acao, "front")] = anims.get((base, "front"), anims[("idle", "front")])
        if (acao, "side") not in anims:
            base = "idle" if acao == "run" else acao
            anims[(acao, "side")] = anims.get((base, "side"), anims[(acao, "front")])
        if (acao, "back") not in anims:
            anims[(acao, "back")] = anims[(acao, "front")]
        if (acao, "side_flip") not in anims:
            anims[(acao, "side_flip")] = espelhar(anims[(acao, "side")])
    return anims


def anims_personagem():
    """Personagem: frames de 32x32 (2x2 unidades de 16px).
    Atack 4f | Dead 6f | Idle 4-5f | Run 6f (a contagem sai da largura do arquivo)."""
    A = "Assets/Character"
    anims = {}
    for acao, pasta in [("idle", "Idle"), ("run", "Run"), ("atack", "Atack"), ("dead", "Dead")]:
        for direcao, vista in [("front", "front"), ("back", "back"), ("side", "side")]:
            caminho = f"{A}/{pasta}/{pasta}_{vista}_view.png"
            anims[(acao, direcao)] = fatiar(caminho, 32, 32)
    return completar(anims)


def anims_morcego():
    """Morcego: idle 16x16 (4f) | atack 16x32 (5f) | dead 16x32 (4f). Sem vista de costas."""
    A = "Assets/Enemies/Bat"
    anims = {
        ("idle", "front"): fatiar(f"{A}/Idle/Idle_front_view.png", 16, 16),
        ("idle", "side"): fatiar(f"{A}/Idle/Idle_side_view.png", 16, 16),
        ("atack", "front"): fatiar(f"{A}/Atack/Atack_front_view.png", 16, 32),
        ("atack", "side"): fatiar(f"{A}/Atack/Atack_side_view.png", 16, 32),
        ("dead", "front"): fatiar(f"{A}/Dead/Dead_front_view.png", 16, 32),
        ("dead", "side"): fatiar(f"{A}/Dead/Dead_side_view.png", 16, 32),
    }
    return completar(anims)


def anims_slime():
    """Slime: idle/run/walk num sheet só 16x16 (4f) | atack front 16x28, side 32x16 (4f)
    | dead 3 frames (largura do arquivo dividida por 3, serve p/ todas as vistas)."""
    A = "Assets/Enemies/Slime"
    dead_sheet = arcade.load_spritesheet(f"{A}/Dead/Dead_all_views.png")
    dead_larg = dead_sheet.image.width // 3
    anims = {
        ("idle", "front"): fatiar(f"{A}/Idle_run_walk/Idle_run_walk.png", 16, 16),
        ("atack", "front"): fatiar(f"{A}/Atack/Atack_front_view.png", 16, 28),
        ("atack", "side"): fatiar(f"{A}/Atack/Atack_side_view.png", 32, 16),
        ("dead", "front"): fatiar(f"{A}/Dead/Dead_all_views.png", dead_larg, dead_sheet.image.height),
    }
    return completar(anims)
