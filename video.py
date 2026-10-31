"""Missões de vídeo: clica nos botões da tela como uma pessoa faria e espera o vídeo acabar."""
import os
import random
import time

import numpy as np
import pyautogui
import pyscreeze

from paths import BUILD, DEFAULT_TEMPLATES, TEMPLATES

NOT_FOUND = (pyautogui.ImageNotFoundException, pyscreeze.ImageNotFoundException)


def template(name):
    """Print da pessoa em templates/, se existir; senão, o padrão que vem com o programa."""
    custom = TEMPLATES / name
    return custom if custom.exists() else DEFAULT_TEMPLATES / name


START = template("start.png")    # parte fixa do botão "Assistir" (sem o tempo)
RESUME = template("resume.png")  # botão "Continuar", de vídeos começados e não terminados
CLAIM = template("claim.png")    # botão "Reivindicar", que aparece quando a missão foi concluída
DONE = template("done.png")      # o X de fechar o vídeo (aparece quando ele abre)
MOBILE = template("mobile.png")  # título "Continue no seu telefone" (missões só de celular)
DEBUG_SHOT = BUILD / "ultimo_fim.png"

CONFIDENCE = 0.85
POLL_SECONDS = 1
MAX_MINUTES = 20
ATTEMPTS = 3  # tentativas por missão antes de pular

STILL_SECONDS = (10, 15)  # imagem parada por esse tempo (sorteado) = vídeo terminou
CHANGED_FRACTION = 0.002  # fração mínima de pixels mudando para considerar que o vídeo está rodando

# Mover o mouse para o canto superior esquerdo interrompe o script.
pyautogui.FAILSAFE = True

SETUP_HELP = f"""
Se os botões não forem reconhecidos (outro idioma, tema ou escala de tela),
salve os seus próprios prints na pasta que vai abrir agora:
  {TEMPLATES}

Use Win+Shift+S e salve com estes nomes:
  start.png  -> o botão "Assistir" da missão, recortando SÓ a palavra
                (sem o tempo, que muda de um vídeo para outro)
  resume.png -> o botão "Continuar", que aparece quando um vídeo foi
                fechado antes do fim (recortando SÓ a palavra)
  claim.png  -> o botão "Reivindicar recompensa", que aparece quando a
                missão foi concluída (recortando SÓ a palavra "Reivindicar")
  done.png   -> o X no canto da tela que fecha o vídeo
  mobile.png -> (opcional) o título "Continue no seu telefone" da janela
                que aparece nas missões que só funcionam no celular

Tire os prints com o Discord no mesmo zoom e na mesma tela em que vai usar.
"""


def locate(template):
    if not template.exists():
        return None
    try:
        return pyautogui.locateOnScreen(str(template), confidence=CONFIDENCE, grayscale=True)
    except NOT_FOUND:
        return None


def locate_all(template):
    try:
        return list(pyautogui.locateAllOnScreen(str(template), confidence=CONFIDENCE, grayscale=True))
    except NOT_FOUND:
        return []


def is_new(box, baseline):
    return all(abs(box.left - b.left) > 10 or abs(box.top - b.top) > 10 for b in baseline)


def same_spot(a, b):
    """Mesmo botão de missão, mesmo que o texto tenha mudado ("Assistir" -> "Continuar")."""
    ax, ay = a.left + a.width / 2, a.top + a.height / 2
    bx, by = b.left + b.width / 2, b.top + b.height / 2
    return abs(ax - bx) < 80 and abs(ay - by) < 25


def locate_buttons():
    """Botões de vídeo pendentes: "Assistir" e "Continuar"."""
    return locate_all(START) + (locate_all(RESUME) if RESUME.exists() else [])


def human_click(box):
    """Clica num ponto aleatório dentro do botão, com movimento e tempo variados."""
    x = box.left + random.randint(box.width // 4, box.width * 3 // 4)
    y = box.top + random.randint(box.height // 4, box.height * 3 // 4)
    pyautogui.moveTo(x, y, duration=random.uniform(0.3, 0.9), tween=pyautogui.easeInOutQuad)
    time.sleep(random.uniform(0.1, 0.4))
    pyautogui.click()


def wait_for_new(template, baseline, timeout):
    """Espera aparecer o template num lugar onde ele não estava antes (ignora os X já na tela)."""
    end = time.time() + timeout
    while time.time() < end:
        for box in locate_all(template):
            if is_new(box, baseline):
                return box
        time.sleep(POLL_SECONDS)
    return None


def center_shot():
    """Centro da tela (onde fica o vídeo). Ignora bordas, barra de tarefas e o mouse."""
    w, h = pyautogui.size()
    return pyautogui.screenshot(region=(int(w * 0.15), int(h * 0.15), int(w * 0.70), int(h * 0.70)))


def gray(shot):
    return np.asarray(shot.convert("L"), dtype=np.int16)[::4, ::4]


def wait_until_still(timeout):
    """Espera a imagem do vídeo ficar parada por 10 a 15 s, sinal de que ele terminou."""
    still_needed = random.uniform(*STILL_SECONDS)
    start = still_since = time.time()
    shot = center_shot()
    prev = gray(shot)
    while time.time() - start < timeout:
        time.sleep(POLL_SECONDS)
        shot = center_shot()
        cur = gray(shot)
        changed = (np.abs(cur - prev) > 10).mean()
        prev = cur
        if changed > CHANGED_FRACTION:
            still_since = time.time()

        elapsed = int(time.time() - start)
        still = int(time.time() - still_since)
        print(f"\r  assistindo: {elapsed // 60:02d}:{elapsed % 60:02d} (parado há {still}s) ", end="", flush=True)
        if time.time() - still_since >= still_needed:
            # Guarda o print do momento em que achou que terminou, para conferir se errar.
            BUILD.mkdir(exist_ok=True)
            shot.save(DEBUG_SHOT)
            print()
            return True
    print()
    return False


def move_away():
    """Tira o mouse de cima do vídeo, para os controles do player sumirem."""
    w, h = pyautogui.size()
    pyautogui.moveTo(
        random.randint(int(w * 0.85), int(w * 0.95)),
        random.randint(int(h * 0.80), int(h * 0.90)),
        duration=random.uniform(0.3, 0.8),
    )


def wait_for_open(baseline, timeout):
    """Depois do clique, espera abrir o vídeo (X novo) ou a janela de "só no celular"."""
    end = time.time() + timeout
    while time.time() < end:
        if MOBILE.exists() and locate(MOBILE):
            return "mobile", None
        for box in locate_all(DONE):
            if is_new(box, baseline):
                return "video", box
        time.sleep(POLL_SECONDS)
    return None, None


def video_open(baseline):
    """O vídeo está aberto enquanto houver um X que não estava na tela antes de abrir."""
    return [b for b in locate_all(DONE) if is_new(b, baseline)]


def close_video(baseline):
    """Fecha o vídeo com Esc; se não fechar, procura o X onde ele estiver agora e clica."""
    for _ in range(3):
        pyautogui.press("esc")
        time.sleep(random.uniform(1.5, 2.5))
        xs = video_open(baseline)
        if not xs:
            return True
        human_click(xs[0])
        time.sleep(random.uniform(1.5, 2.5))
        if not video_open(baseline):
            return True
    return False


def watch(button):
    """Assiste o vídeo de um botão. Retorna "done", "mobile" (só no celular), "failed" ou "stuck"."""
    for attempt in range(1, ATTEMPTS + 1):
        baseline = locate_all(DONE)
        human_click(button)
        opened, _ = wait_for_open(baseline, 30)
        if opened == "mobile":
            time.sleep(random.uniform(1, 3))
            pyautogui.press("esc")
            time.sleep(1.5)
            return "mobile" if not locate(MOBILE) else "stuck"
        if not opened:
            print("  O vídeo não abriu.")
            return "failed"
        move_away()

        if not wait_until_still(MAX_MINUTES * 60):
            print(f"  O vídeo não terminou em {MAX_MINUTES} min.")
        time.sleep(random.uniform(2, 6))
        if not close_video(baseline):
            return "stuck"
        time.sleep(2)

        # Concluída só quando o botão "Reivindicar" aparece no lugar da missão.
        if any(same_spot(b, button) for b in locate_all(CLAIM)):
            return "done"
        print(f"  Ainda não concluiu (tentativa {attempt}/{ATTEMPTS}), abrindo de novo...")
    return "failed"


def menu():
    TEMPLATES.mkdir(exist_ok=True)
    print("\nDeixe a página de Missões do Discord visível na tela principal.")
    print("Para parar, jogue o mouse no canto superior esquerdo ou aperte Ctrl+C.")
    input("Enter para começar...")
    time.sleep(3)

    done_count = mobile_count = 0
    skipped = []
    while True:
        buttons = [b for b in locate_buttons() if not any(same_spot(b, s) for s in skipped)]
        if not buttons:
            print("Nenhum botão de vídeo encontrado na tela.")
            if done_count + len(skipped) == 0:
                print(SETUP_HELP)
                os.startfile(TEMPLATES)
            break

        button = min(buttons, key=lambda b: (b.top, b.left))
        print(f"({done_count + len(skipped) + 1}) Iniciando vídeo...")
        result = watch(button)
        if result == "stuck":
            print("  ✖ Não consegui fechar a janela. Parando para você conferir.")
            break
        if result == "done":
            done_count += 1
            print("  ✔ Vídeo concluído.")
            # Pausa antes do próximo, como uma pessoa faria.
            time.sleep(random.uniform(8, 25))
        else:
            skipped.append(button)
            if result == "mobile":
                mobile_count += 1
                print("  » Só pode ser vista no celular, pulando.")
            else:
                print("  ✖ Pulando esta missão.")
            time.sleep(random.uniform(2, 5))

    failed = len(skipped) - mobile_count
    print(f"\nFim. {done_count} vídeo(s) concluído(s), {mobile_count} só no celular, {failed} com falha.")
    print("Resgate as recompensas no Discord.")
