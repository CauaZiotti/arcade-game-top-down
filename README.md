# arcade-game-top-down

Jogo desenvolvido na matéria de jogos 2D do IFFAR-FW.

Dungeon crawler 2D top-down feito em Python com a biblioteca **Arcade**. O jogador explora uma masmorra maior que a tela (câmera com scroll), enfrenta inimigos com IA (percepção, máquina de estados e busca de caminho), coleta poções e desvia de armadilhas até eliminar todos os monstros e recuperar a chave do baú final.

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

**Controles:** WASD / Setas — mover · ESPAÇO — atacar · TAB — modo debug (visualiza a IA) · ENTER — confirmar nos menus · R — reiniciar a fase.

## Tecnologias

- **Python 3.12**
- **Arcade 3.3.3** — engine 2D (janela, `Sprite`/`SpriteList`, câmera, texturas, texto, spritesheets)
- **Pyglet 2.1.15** — backend de janela/eventos usado internamente pelo Arcade
- **Pillow 11.3.0** — fatiamento e recorte de spritesheets (autotiling do tileset, centralização de sprites do personagem)

## Algoritmos e técnicas de IA

- **Percepção por FOV + Raycasting** ([ia/ia_system.py](ia/ia_system.py)) — cada inimigo só "vê" o jogador se ele estiver dentro do raio de alcance, dentro do cone de visão (ângulo) e com linha de visão livre (o raycast anda célula a célula pela matriz do mapa e para se encontrar parede). É o que faz o morcego perder o jogador de vista atrás de uma coluna, por exemplo.
- **Máquina de Estados Finita (FSM)** ([entities/entities.py](entities/entities.py)) — todo inimigo alterna entre `patrulha` (anda por pontos aleatórios do mapa) e `perseguição` (persegue o jogador), decidido pela percepção acima. O morcego tem um terceiro comportamento: guarda a última posição vista do jogador por até 2s antes de desistir da perseguição (memória de curto prazo).
- **Busca de caminho A\*** ([ia/ia_system.py](ia/ia_system.py)) — usado pelo slime (que anda pelo chão e colide com paredes) tanto na perseguição quanto na patrulha aleatória, com heurística de Manhattan e desempate por distância à reta (evita o caminho "andar tudo numa direção, depois tudo na outra"). O morcego ignora o A* porque voa por cima dos obstáculos.

## Checklist dos requisitos

- [x] Jogo 2D do gênero **top-down**, em Python com **Arcade 3.3.3**
- [x] Fase completa e funcional: movimentação vista de cima, colisão com obstáculos e navegação em tile map baseado em matriz
- [x] Início, desenvolvimento e finalização claros — objetivo definido (eliminar os inimigos e pegar a chave do baú), condição de vitória e condição de derrota
- [x] Mundo maior que a janela, com **scroll de câmera** (`arcade.Camera2D` seguindo o jogador, presa aos limites do mapa)
- [x] **Tela inicial**, **tela principal do jogo** e **tela de fim de jogo**, cada uma como `arcade.View` própria ([views/tela_inicial.py](views/tela_inicial.py), [views/tela_jogo.py](views/tela_jogo.py), [views/tela_fim.py](views/tela_fim.py))
- [x] **HUD** com informações relevantes ao jogador: vida (corações), objetivo atual da fase e status de efeitos temporários ([ui/hud.py](ui/hud.py))
- [x] Cenário estruturado a partir de **matrizes convertidas em tile map**, com autotiling (chão, paredes, faces de tijolo) a partir do tileset ([sprites/tiles.py](sprites/tiles.py))
- [x] Organização em classes/entidades/views/sistemas separados: `entities/` (jogador, inimigos, poções, armadilhas, baú/chave), `ia/` (algoritmos de IA), `sprites/` (tileset e animações), `ui/` (HUD), `views/` (telas)
- [x] **Pelo menos 3 técnicas de IA** implementadas, integradas ao jogo e claramente observáveis (visíveis também no modo debug com TAB): FOV + Raycasting, Máquina de Estados Finita e A\*
- [x] Coerência das IAs com a proposta do jogo: slime lento que persegue pelo chão desviando de paredes (A\*), morcego rápido que voa por cima de obstáculos mas ainda assim precisa *ver* o jogador pra perseguir (FOV/raycasting) e "esquece" o alvo depois de um tempo sem contato visual (FSM com memória)
- [x] Uso adequado da arquitetura do Arcade: `Sprite`, `SpriteList`, `on_update()`, `on_draw()`, movimentação via `change_x`/`change_y` e uso correto de `delta_time` em toda a lógica de movimento e animação

## Mecânicas extras

- [x] Sistema de vida do jogador (3 vidas) com invulnerabilidade temporária e piscar visual após levar dano
- [x] Inimigos com vida múltipla: slime aguenta 2 golpes, morcego aguenta 3
- [x] Poções coletáveis: azul concede velocidade extra por tempo limitado, vermelha cura 1 vida
- [x] Armadilhas como obstáculo: armadilha de urso (dispara uma vez) e armadilha de espinho (dano cíclico, em ritmo próprio por armadilha)
- [x] Baú final que abre só depois de eliminar todos os inimigos, revelando a chave que vence o jogo

## Créditos

- **Assets (tileset, personagem, inimigos e objetos)**: [Bitlands Dungeon](https://somepizzart.itch.io/bitlands-dungeon), por [SomePizzaArt](https://somepizzart.itch.io/)
