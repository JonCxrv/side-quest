# side-quest

Completa missões do Discord no Windows: assiste os vídeos e "joga" os jogos das missões por você.

> ⚠️ Simular jogos vai contra os Termos de Serviço do Discord. Use por sua conta e risco.

## Como usar

Coloque o `side-quest.exe` numa pasta só para ele e abra com dois cliques. Se o Windows avisar que o app não é reconhecido, clique em *Mais informações → Executar assim mesmo*.

### Missões de vídeo

1. Abra o Discord na página de **Missões**.
2. No programa, escolha **1**.
3. Não mexa no mouse. Ele assiste um vídeo atrás do outro.

Para parar, jogue o mouse no canto superior esquerdo da tela.

### Missões de jogo

1. No Discord, **aceite** as missões de jogo que você quer fazer.
2. No programa, escolha **2** e depois **1** (busca automática).
3. Vai abrir uma janela do navegador com o Discord. Na primeira vez, faça login nela. Depois ela fecha sozinha.
4. Confira a lista de jogos e aperte Enter para começar.
5. Deixe o Discord aberto. Os jogos rodam um de cada vez, pelo tempo de cada missão.

Se preferir, escolha **2** no passo 2 para digitar os nomes dos jogos.

No final, resgate as recompensas no Discord.

## Se os botões não forem reconhecidos

O programa já vem com prints do Discord em português. Se você usa outro idioma, tema ou tamanho de tela, recorte os botões com `Win+Shift+S` e salve na pasta `templates`, ao lado do `.exe`:

`start.png` (Assistir) · `resume.png` (Continuar) · `claim.png` (Reivindicar) · `done.png` (X do vídeo) · `mobile.png` (Continue no seu telefone)

## Segurança

A pasta `browser-profile` guarda o seu login do Discord. **Não compartilhe.** Para passar o programa para alguém, envie só o `.exe`.

## Desenvolvimento

```
pip install -r requirements.txt pyinstaller
python side_quest.py
pyinstaller --onefile --name side-quest --add-data "assets/templates;assets/templates" side_quest.py
```
