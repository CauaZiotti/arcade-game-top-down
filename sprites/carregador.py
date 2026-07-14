import arcade
from PIL import Image

ACOES = ["idle", "run", "atack", "dead"]
DIRECOES = ["front", "back", "side", "side_flip"]


def fatiar(caminho, frame_larg, frame_alt, deslocamento=(0, 0)):
    
    if deslocamento == (0, 0):
        sheet = arcade.load_spritesheet(caminho)
        n = sheet.image.width // frame_larg
        return sheet.get_texture_grid(size=(frame_larg, frame_alt), columns=n, count=n)

    img = Image.open(caminho).convert("RGBA")
    n = img.width // frame_larg
    texturas = []
    for i in range(n):
        frame = img.crop((i * frame_larg, 0, (i + 1) * frame_larg, frame_alt))
        base = Image.new("RGBA", (frame_larg, frame_alt), (0, 0, 0, 0))
        base.paste(frame, deslocamento)
        texturas.append(arcade.Texture(base))
    return texturas


def _centro_do_desenho(caminho, frame_larg, frame_alt):
    
    img = Image.open(caminho).convert("RGBA")
    bb = img.crop((0, 0, frame_larg, frame_alt)).getchannel("A").getbbox()
    return (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2


def espelhar(texturas):
    return [t.flip_left_right() for t in texturas]


def completar(anims):
   
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
    A = "Assets/Character"
    deslocamentos = {}
    for direcao, vista in [("front", "front"), ("back", "back"), ("side", "side")]:
        cx, cy = _centro_do_desenho(f"{A}/Idle/Idle_{vista}_view.png", 32, 32)
        deslocamentos[direcao] = (round(16 - cx), round(16 - cy))

    anims = {}
    for acao, pasta in [("idle", "Idle"), ("run", "Run"), ("atack", "Atack"), ("dead", "Dead")]:
        for direcao, vista in [("front", "front"), ("back", "back"), ("side", "side")]:
            caminho = f"{A}/{pasta}/{pasta}_{vista}_view.png"
            anims[(acao, direcao)] = fatiar(caminho, 32, 32, deslocamentos[direcao])
    return completar(anims)


def anims_morcego():
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
