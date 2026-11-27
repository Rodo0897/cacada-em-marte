# Guia de estudo e apresentação

## Como estudar em dupla

1. **Joguem uma partida.** Explorem o menu, experimentem o super e identifiquem o que muda quando a nave atravessa para a Calota Boreal.
2. **Sigam um quadro.** Abram `main.py` e localizem a chamada de `Game().run()`. Em `src/marte/game.py`, encontrem a leitura de eventos, atualização e desenho.
3. **Sigam um disparo.** Em `src/marte/mission.py`, encontrem o nascimento do laser, seu movimento e o teste que detecta um acerto. Expliquem quando a pontuação muda.
4. **Sigam uma compra.** Em `src/marte/profile.py`, encontrem o controle de saldo, o desbloqueio da nave e a gravação do perfil. Comparem o JSON antes e depois de uma partida completa no próprio computador.
5. **Troquem os papéis.** Cada um explica o trecho estudado pelo outro e demonstra um controle sem ler o roteiro.

## Roteiro para cinco minutos

| Tempo | Quem | O que apresentar |
|---|---|---|
| 0:00–0:40 | Nicolas | Mostrar o título, os integrantes, a história e o objetivo |
| 0:40–1:35 | Rodrigo | Mostrar os mapas e explicar como a dificuldade aumenta |
| 1:35–2:30 | Nicolas | Abrir uma partida e demonstrar movimento, tiros e power-ups |
| 2:30–3:45 | Rodrigo | Explicar o laço principal e a colisão com um trecho curto de código |
| 3:45–4:25 | Ambos | Apresentar loja, ranking e salvamento. Mostrar o super ao vivo se a barra já estiver cheia |
| 4:25–5:00 | Ambos | Explicar a divisão de tarefas e declarar onde usaram o Codex |

Ensaiem com o jogo já instalado. Se o tempo acabar antes da segunda fase, usem a captura da Calota Boreal que já está nos slides.

## Falas para ensaiar

- **Nicolas, abertura:** “Somos Nicolas Cruz Peres e Rodrigo Santana Matos, da Equipe Ares. Em nosso jogo, uma frota se aproxima da primeira colônia de Marte. O piloto precisa sobreviver a quatro ondas ao todo e vencer dois chefes.”
- **Rodrigo, campanha:** “O Cânion Ares ensina a desviar e atirar. A Calota Boreal acelera o combate. Os chefes têm padrões diferentes, então vale guardar o super para o momento certo.”
- **Nicolas, jogo ao vivo:** “Uso A e D para mover e Espaço para disparar. Alguns inimigos deixam melhorias. Os abates e as coletas de energia carregam a barra. Quando ela chega a 100%, X dispara três tiros que atravessam os alvos.”
- **Rodrigo, desafio técnico:** “Para evitar que o movimento dependa da taxa de quadros, o código multiplica a velocidade pelos segundos desde o quadro anterior. Nas colisões, compara os retângulos e aplica dano quando se cruzam.” Mostre `Mission.step()` e `_hit_targets()`.
- **Ambos, encerramento:** “Propusemos juntos as melhorias. Nicolas executou a primeira versão, e Rodrigo iniciou o teste em outro computador. Usamos o Codex para implementar grande parte do código, produzir os recursos e preparar os documentos. O README lista onde a IA foi usada.” Atualizem a frase sobre os testes após a validação da versão atual.

## Alteração ao vivo para praticar

Façam a prática em uma cópia da pasta. Alterem o primeiro valor de velocidade em `PATTERNS`, no arquivo `src/marte/mission.py`, e observem o efeito na primeira onda. Depois desfaçam a mudança. Os dois integrantes devem conseguir encontrar a configuração, prever o efeito e explicar o resultado.

## Perguntas para praticar

- **Como o jogo detecta um acerto?** Ele verifica se os retângulos do projétil e do alvo se sobrepõem.
- **Por que guardar posição como número fracionário?** Deslocamentos pequenos se acumulam entre quadros. Arredondar antes de gravar a posição perderia parte do movimento.
- **Como as ondas avançam?** A simulação acompanha a fila de inimigos e os que ainda estão na tela. Quando uma onda termina, prepara a próxima ou chama o chefe.
- **O que muda ao equipar outra nave?** Mudam atributos como velocidade, quantidade de tiros, vidas ou ritmo de carga do super. Os estilos de tiro mudam a aparência.
- **Como provar que o ranking é salvo?** Terminamos uma partida nomeada, fechamos o jogo e, ao reabrir, vemos a pontuação entre as melhores se ela estiver no top 10.
- **Como mostrar um teste?** Escolham um teste de colisão, persistência ou transição de mapa. Expliquem a situação preparada, o que o teste executa e o resultado que ele espera.


## Trechos que os dois precisam saber explicar

| Onde olhar | O que dizer e mostrar |
|---|---|
| `main.py` → `Game().run()` | A primeira linha de execução cria o jogo. O laço lê as entradas, atualiza a simulação, desenha e apresenta o novo quadro. O menu, a partida, a pausa e as telas finais são estados diferentes. |
| `marte/game.py` → `handle()` e `update()` | Enter é um evento pontual. Manter A, D ou Espaço é lido a cada quadro. Na pausa, a partida deixa de avançar. Todos os módulos `marte/` ficam dentro de `src/`. |
| `marte/mission.py` → `step()`, `move_lasers()` e `_hit_targets()` | Para mover a nave, o código soma direção × velocidade × tempo. Se a caixa do tiro se sobrepõe à do alvo, o alvo perde resistência. Só os alvos destruídos geram pontos. Asteroides podem interceptar o tiro normal. |
| `marte/mission.py` → `_destroy_target()` e `_fire_player()` | Três abates comuns aumentam um nível de combo, até ×5. Abates dão carga. Quando o jogador usa X com a barra cheia, a carga volta a zero e surgem três projéteis. Cada faixa perfura os alvos e só causa dano uma vez a cada alvo. |
| `marte/mission.py` → `progress_wave()` | A onda avança quando a fila de surgimento e a lista de inimigos ficam vazias. Depois da segunda onda vem o chefe. O primeiro chefe libera a Calota. O segundo conclui a missão em vitória. |
| `marte/profile.py` → `record()`, `select_ship()` e `_save()` | O jogo registra o resultado uma vez ao mudar para a tela final. Pontos viram créditos e o ranking guarda os dez melhores resultados deste computador. O JSON também guarda a nave equipada. |
| `marte/art.py` e `marte/audio.py` | As naves e efeitos usam formas, cores e partículas. O áudio é gerado por código, salvo em WAV e reproduzido com Pygame. Há trilhas diferentes para menu, Cânion e Calota. |

Se pedirem uma alteração além da velocidade, tentem mudar o valor do batedor em `ENEMY_POINTS` de 100 para 150 em uma cópia. Expliquem que o valor é multiplicado pelo combo. Para verificar, abatam apenas o primeiro batedor, quando o combo ainda vale ×1.

## Ensaio final no notebook do Rodrigo

1. Extraiam o **ZIP atualizado** em uma pasta nova. Sigam as instruções do README e abram o jogo.
2. Iniciem uma missão com um apelido, movimentem a nave, disparem e pausem. Terminem a partida com pontos. Fechem, reabram e confirmem que o resultado aparece em **Ranking local**.
3. Deixem o jogo no menu e o arquivo `src/marte/mission.py` já aberto no VS Code. Durante a fala ao vivo, mostrem primeiro o movimento e o tiro. Se a barra encher a tempo, mostrem X. Reservem as capturas para explicar o segundo chefe, mesmo se não chegarem lá durante a apresentação.
4. Passem o roteiro duas vezes com cronômetro. Na segunda vez, troquem as falas e façam a alteração de treino. Contem na apresentação o que de fato testaram, revisaram e modificaram.
