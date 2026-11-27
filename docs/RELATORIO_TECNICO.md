# Caçada em Marte

**Relatório técnico do projeto A3**  
**Equipe Ares**  
**Disciplina:** Usabilidade, desenvolvimento web, mobile e jogos  
**Professor indicado no enunciado:** Elzo Brito dos Santos Filho

| Integrante | RA |
|---|---|
| Nicolas Cruz Peres | 82610219 |
| Rodrigo Santana Matos | 82199719 |

## Objetivo e história

O projeto aplica conceitos de programação em Python a um jogo 2D de ação. Em 2150, uma frota alienígena corta o contato da colônia Ares com a Terra. A nave de defesa precisa atravessar o Cânion Ares e a Calota Boreal para enfrentar os chefes Mandíbula Rubra e Sentinela Boreal.

## Estrutura

| Caminho | Responsabilidade |
|---|---|
| `main.py` | Ponto de entrada |
| `src/marte/game.py` | Janela, entrada do jogador, telas e HUD |
| `src/marte/mission.py` | Regras de movimento, colisão, surgimento, ondas, mapas, pontuação e super |
| `src/marte/art.py` | Desenho de naves, cenário, projéteis e partículas |
| `src/marte/audio.py` | Trilha e efeitos sonoros |
| `src/marte/profile.py` | Leitura e gravação do perfil, loja e ranking local |
| `assets/img/` e `assets/sons/` | Recursos de imagem e áudio |
| `tests/` | Verificações automatizadas |

## Laço do jogo e colisões

A janela coleta eventos e verifica as teclas pressionadas. Em uma partida ativa, o código converte as teclas em direção, disparo e pedido de uso do super. A simulação recebe o intervalo entre quadros em segundos, chamado `dt`. Multiplicar a velocidade por `dt` produz o deslocamento do quadro mesmo quando o tempo de renderização varia.

As posições são armazenadas com precisão fracionária. Para colisões, o Pygame fornece retângulos em torno dos objetos. Quando o retângulo de um tiro cruza o de um inimigo, a simulação aplica dano. O placar só recebe os pontos daquele inimigo ao eliminá-lo. Quando a nave do jogador perde vida, o intervalo de proteção evita perder várias vidas por contatos seguidos no mesmo instante.

## Campanha, super e personalização

Cada mapa tem duas ondas e um chefe. A velocidade e a composição das ondas mudam durante a campanha. Os obstáculos ocupam parte da arena, enquanto as melhorias coletáveis e a barra de super dão ao jogador novas formas de responder à pressão. Quando Mandíbula Rubra cai, a campanha segue para a Calota Boreal e a nave recupera uma vida se estiver abaixo do limite. A batalha termina em vitória quando Sentinela Boreal cai e em derrota quando acabam as vidas.

As eliminações de inimigos comuns em sequência podem multiplicar a pontuação até ×5. O super consome a barra cheia e dispara três projéteis que atravessam os alvos. O jogo alterna os itens coletáveis entre carga de energia, tiro rápido por seis segundos e reparo. As três naves mudam a estratégia. Ares carrega a barra mais rapidamente, Cometa favorece mobilidade e tiros duplos, e Bastião troca velocidade por uma vida a mais. Os três estilos de tiro personalizam a aparência.

## Recursos gráficos e som

A interface desenha naves, projéteis e partículas com primitivas do Pygame. Cada região usa sua própria paleta. Os arquivos WAV em `assets/sons/` são gerados por síntese de ondas e ruído. O jogo alterna as trilhas de menu, Cânion Ares e Calota Boreal com `pygame.mixer.music`, e toca efeitos de ações com `pygame.mixer.Sound`. A tecla M controla os dois.

## Persistência local

Ao fim de uma partida, o perfil registra piloto, pontuação e resultado. O placar local apresenta as dez melhores partidas. Os créditos somam a parte inteira de pontos divididos por cinco, com mais 100 na vitória. Comprar uma nave desconta créditos e mantém o desbloqueio para partidas seguintes. O JSON também guarda a nave equipada e a preferência de disparo. O arquivo fica na pasta de dados do usuário, separada dos arquivos do jogo.

## Verificação

Os testes ficam em `tests/` e podem ser rodados com `python -m unittest discover -s tests -v` com o ambiente do projeto instalado. Para o ensaio, abram a versão extraída do ZIP e verifiquem o menu, os controles, a barra de poder, a promoção para o segundo mapa, a loja e o ranking após fechar e reabrir o jogo.

As capturas, dependências e instruções de execução ficam no [README](../README.md). Os slides resumem a proposta e a construção para a apresentação. O [guia de estudo](GUIA_DE_ESTUDO_E_APRESENTACAO.md) indica quais trechos do código mostrar.
