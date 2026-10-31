"""Missões de jogo: roda um executável vazio com o nome que o Discord reconhece."""
import json
import random
import subprocess
import time
import urllib.request
from pathlib import Path

from paths import APP_DIR, BUILD

GAMES_DIR = APP_DIR / "games"

DUMMY_EXE = BUILD / "dummy.exe"
DETECTABLE_CACHE = BUILD / "detectable.json"
DETECTABLE_URL = "https://discord.com/api/v9/applications/detectable"
CSC = Path(r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe")

CACHE_MAX_AGE = 24 * 60 * 60
EXTRA_SECONDS = (30, 180)  # margem aleatória somada ao tempo da missão
PAUSE_SECONDS = (60, 300)  # pausa aleatória entre um jogo e outro

# Janela vazia e minimizada que fica aberta até ser encerrada. O título é o nome do jogo.
DUMMY_SOURCE = """
using System;
using System.Windows.Forms;

class Dummy
{
    [STAThread]
    static void Main(string[] args)
    {
        var form = new Form
        {
            Text = args.Length > 0 ? args[0] : "Game",
            WindowState = FormWindowState.Minimized,
            ShowInTaskbar = true,
        };
        Application.Run(form);
    }
}
"""


def load_detectable():
    """Lista pública de jogos que o Discord detecta, com cache de 1 dia."""
    BUILD.mkdir(exist_ok=True)
    if DETECTABLE_CACHE.exists() and time.time() - DETECTABLE_CACHE.stat().st_mtime < CACHE_MAX_AGE:
        return json.loads(DETECTABLE_CACHE.read_text(encoding="utf-8"))

    print("Baixando a lista de jogos do Discord...")
    req = urllib.request.Request(DETECTABLE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as res:
        data = res.read()
    DETECTABLE_CACHE.write_bytes(data)
    return json.loads(data)


def win_executable(app):
    exes = [e for e in app.get("executables") or [] if e.get("os") == "win32"]
    exes.sort(key=lambda e: e.get("is_launcher", False))
    return exes[0]["name"] if exes else None


def search(apps, query):
    """Retorna os jogos com executável Windows cujo nome bate com a busca (exatos primeiro)."""
    q = query.strip().lower()
    exact, partial = [], []
    for app in apps:
        if not win_executable(app):
            continue
        names = [app["name"].lower()] + [a.lower() for a in app.get("aliases") or []]
        if q in names:
            exact.append(app)
        elif any(q in n for n in names):
            partial.append(app)
    return exact + partial


def pick(apps, query):
    matches = search(apps, query)
    if not matches:
        print(f'  Nenhum jogo encontrado para "{query}". Confira o nome na missão.')
        return None
    if len(matches) == 1 or matches[0]["name"].lower() == query.strip().lower():
        return matches[0]

    print("  Vários jogos encontrados:")
    for i, app in enumerate(matches[:10], 1):
        print(f"    {i}. {app['name']}")
    choice = input("  Número (Enter para pular): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= min(len(matches), 10):
        return matches[int(choice) - 1]
    return None


def ask_minutes(default=15):
    answer = input(f"Tempo da missão em minutos [{default}]: ").strip()
    return int(answer) if answer.isdigit() and int(answer) > 0 else default


def build_dummy():
    if DUMMY_EXE.exists():
        return
    if not CSC.exists():
        raise SystemExit(f"Compilador C# não encontrado em {CSC}")
    BUILD.mkdir(exist_ok=True)
    print("Preparando o executável (só na primeira vez)...")
    source = BUILD / "Dummy.cs"
    source.write_text(DUMMY_SOURCE, encoding="utf-8")
    subprocess.run(
        [str(CSC), "/nologo", "/target:winexe", f"/out:{DUMMY_EXE}", str(source)],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def install_fake(app):
    """Copia o dummy para games/<id>/<caminho que o Discord espera>."""
    exe_path = GAMES_DIR / app["id"] / Path(win_executable(app))
    exe_path.parent.mkdir(parents=True, exist_ok=True)
    if not exe_path.exists():
        exe_path.write_bytes(DUMMY_EXE.read_bytes())
    return exe_path


def countdown(seconds, label):
    end = time.time() + seconds
    while (left := end - time.time()) > 0:
        print(f"\r  {label}: {int(left // 60):02d}:{int(left % 60):02d} restantes ", end="", flush=True)
        time.sleep(min(1, left))
    print()


def play(queue):
    """Roda os jogos da fila, um de cada vez. queue = [(app, minutos)]."""
    build_dummy()
    print(f"\n{len(queue)} jogo(s) na fila: {', '.join(a['name'] for a, _ in queue)}")
    print("Deixe o Discord aberto. Ctrl+C para parar.\n")

    for i, (app, minutes) in enumerate(queue):
        exe = install_fake(app)
        # Tempo da missão + margem aleatória, para não terminar sempre no mesmo segundo.
        duration = minutes * 60 + random.randint(*EXTRA_SECONDS)
        print(f"({i + 1}/{len(queue)}) {app['name']} — ~{duration // 60} min")

        proc = subprocess.Popen([str(exe), app["name"]], cwd=exe.parent)
        try:
            countdown(duration, "jogando")
        finally:
            proc.terminate()
            proc.wait(timeout=10)
        print("  ✔ Encerrado. Confira o progresso da missão no Discord.")

        if i < len(queue) - 1:
            countdown(random.randint(*PAUSE_SECONDS), "pausa antes do próximo")

    print("\nFim! Resgate as recompensas no Discord.")


def manual_queue(apps):
    print("\nDigite os jogos das suas missões, como aparecem no Discord.")
    chosen = []
    while True:
        query = input("Nome do jogo (Enter vazio para começar): ").strip()
        if not query:
            break
        if app := pick(apps, query):
            chosen.append(app)
            print(f"  ✔ {app['name']}")
    if not chosen:
        return []
    minutes = ask_minutes()
    return [(app, minutes) for app in chosen]


def auto_queue(apps):
    import quest_list

    print("\nPara buscar suas missões, o Discord vai abrir numa janela separada do navegador.")
    print("Na primeira vez você precisa fazer login nela; depois o login fica salvo.")
    if input("Continuar? [S/n]: ").strip().lower() == "n":
        return []

    quests = quest_list.fetch_game_quests()
    if not quests:
        print("Nenhuma missão de jogo pendente encontrada.")
        return []

    by_id = {app["id"]: app for app in apps}
    queue = []
    print("\nMissões de jogo encontradas:")
    for quest in quests:
        app = by_id.get(quest["app_id"])
        if not app or not win_executable(app):
            print(f"  ✖ {quest['name']}: o Discord não informa um executável para Windows, pulando")
        elif not quest["enrolled"]:
            print(f"  ! {quest['name']}: missão ainda não aceita, aceite no Discord e busque de novo")
        else:
            print(f"  ✔ {quest['name']}: faltam {quest['minutes']} min")
            queue.append((app, quest["minutes"]))

    if queue and input("\nComeçar? [S/n]: ").strip().lower() == "n":
        return []
    return queue


def menu():
    apps = load_detectable()
    print("\nComo quer escolher os jogos?")
    print("1. Buscar minhas missões automaticamente (abre o Discord no navegador)")
    print("2. Digitar os jogos manualmente")
    choice = input("> ").strip()

    queue = auto_queue(apps) if choice == "1" else manual_queue(apps) if choice == "2" else []
    if queue:
        play(queue)
