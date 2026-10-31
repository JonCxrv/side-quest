# side-quest

Completa as missões de vídeo do Discord clicando na tela por você. O vídeo roda de verdade e o cliente do Discord não é modificado.

## Uso

1. Abra o `side-quest.exe` numa pasta só para ele.
2. Salve em `templates/` os prints dos botões, recortando **só a palavra** (`Win+Shift+S`):
   - `start.png`: "Assistir"
   - `resume.png`: "Continuar"
   - `claim.png`: "Reivindicar"
   - `done.png`: o X que fecha o vídeo
   - `mobile.png` (opcional): o título "Continue no seu telefone"
3. Deixe a página de Missões do Discord visível e escolha `1` no menu.

Para parar, jogue o mouse no canto superior esquerdo da tela. As recompensas são resgatadas manualmente.

## Desenvolvimento

```
pip install -r requirements.txt
python side_quest.py
pyinstaller --onefile --name side-quest side_quest.py
```
