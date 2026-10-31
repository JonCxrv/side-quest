# side-quest

Ajuda a completar as missões de vídeo (Quests) do Discord sem mexer no cliente do Discord.

O vídeo roda de verdade na tela. O programa só faz os cliques por você, com o mouse do sistema, e passa para a próxima missão quando o vídeo termina.

## Como usar

1. Coloque o `side-quest.exe` numa pasta só para ele (ele cria arquivos ao lado).
2. Dê dois cliques. Se o Windows avisar que o app não é reconhecido, clique em *Mais informações → Executar assim mesmo*.
3. Na primeira vez, escolha `1`. O programa abre a pasta `templates/` e explica quais prints salvar lá.
4. Abra a página de Missões no Discord, escolha `1` de novo e deixe a janela visível.

Para parar, jogue o mouse no **canto superior esquerdo** da tela ou aperte `Ctrl+C`.

### Prints dos botões

Cada pessoa tira os próprios prints, porque os botões mudam com o idioma e o tema. Use `Win+Shift+S` e recorte **só a palavra** de cada botão, sem o tempo do vídeo:

| Arquivo | O que recortar | Obrigatório |
| --- | --- | --- |
| `start.png` | "Assistir" | Sim |
| `resume.png` | "Continuar" | Sim |
| `claim.png` | "Reivindicar" | Sim |
| `done.png` | O X que fecha o vídeo | Sim |
| `mobile.png` | O título "Continue no seu telefone" | Não |

## Como funciona

Para cada missão com "Assistir" ou "Continuar" na tela, de cima para baixo:

1. Clica no botão e espera o vídeo abrir.
2. Se for uma missão só de celular, fecha a janela do QR code e pula.
3. Espera a imagem do vídeo ficar parada por 10 a 15 s, sinal de que ele terminou.
4. Fecha o vídeo com `Esc` (ou no X, onde ele estiver).
5. Confere se o botão virou "Reivindicar". Se ainda estiver "Continuar", reabre (até 3 vezes).

As recompensas são resgatadas manualmente, porque às vezes o Discord pede captcha.

## Desenvolvimento

Precisa de Windows e Python 3.10+.

```
pip install -r requirements.txt
python side_quest.py
```

Para gerar o `.exe`:

```
pip install pyinstaller
pyinstaller --onefile --name side-quest side_quest.py
```

O arquivo sai em `dist/side-quest.exe`.

| Arquivo | Função |
| --- | --- |
| `side_quest.py` | Menu principal |
| `video.py` | Cliques automáticos nas missões de vídeo |
| `paths.py` | Pastas usadas pelo programa (código ou `.exe`) |
