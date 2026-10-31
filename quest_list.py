"""Lista as missões de jogo da conta abrindo o Discord num Chrome separado.

O script não faz nenhuma requisição ao Discord: ele só lê a resposta que a própria
página de missões recebe ao carregar (via protocolo de depuração do Chrome).
"""
import json
import math
import socket
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import websocket

from paths import APP_DIR, BUILD

PROFILE_DIR = APP_DIR / "browser-profile"  # login do Discord fica salvo aqui; não compartilhe
RAW_DUMP = BUILD / "quests.json"
QUEST_HOME = "https://discord.com/quest-home"
QUESTS_API = "/quests/@me"
LOGIN_TIMEOUT = 5 * 60

BROWSERS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe",
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


class DevToolsError(Exception):
    pass


class DevTools:
    """Cliente mínimo do protocolo de depuração do Chrome."""

    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=5, suppress_origin=True)
        self.next_id = 0
        self.events = []

    def send(self, method, **params):
        self.next_id += 1
        msg_id = self.next_id
        self.ws.send(json.dumps({"id": msg_id, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == msg_id:
                if "error" in msg:
                    raise DevToolsError(msg["error"].get("message", str(msg["error"])))
                return msg.get("result", {})
            if "method" in msg:
                self.events.append(msg)

    def poll(self):
        """Eventos recebidos até agora (espera no máximo 1 s por um novo)."""
        self.ws.settimeout(1)
        try:
            self.events.append(json.loads(self.ws.recv()))
        except websocket.WebSocketTimeoutException:
            pass
        events, self.events = self.events, []
        return [e for e in events if "method" in e]

    def close(self):
        self.ws.close()


def find_browser():
    return next((b for b in BROWSERS if b.exists()), None)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def open_browser(port):
    browser = find_browser()
    if not browser:
        raise SystemExit("Chrome ou Edge não encontrado.")
    proc = subprocess.Popen([
        str(browser),
        f"--remote-debugging-port={port}",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank",
    ])

    for _ in range(30):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=2) as res:
                pages = [t for t in json.load(res) if t.get("type") == "page"]
            if pages:
                return proc, pages[0]["webSocketDebuggerUrl"]
        except OSError:
            pass
        time.sleep(1)
    proc.terminate()
    raise SystemExit("Não consegui me conectar ao navegador.")


def capture_quests(tools):
    """Abre a página de missões e devolve o JSON que o Discord recebe com a lista."""
    tools.send("Network.enable")
    tools.send("Page.navigate", url=QUEST_HOME)

    request_ids = set()
    asked_login = False
    deadline = time.time() + LOGIN_TIMEOUT
    while time.time() < deadline:
        for event in tools.poll():
            method, params = event["method"], event.get("params", {})
            if method == "Network.responseReceived":
                url_path = urlparse(params["response"]["url"]).path
                if url_path.endswith(QUESTS_API) and params["response"].get("status") == 200:
                    request_ids.add(params["requestId"])
            elif method == "Network.loadingFinished" and params["requestId"] in request_ids:
                request_ids.discard(params["requestId"])
                try:
                    body = tools.send("Network.getResponseBody", requestId=params["requestId"])
                except DevToolsError as err:
                    # Acontece quando a página muda logo depois (ex.: após o login); espera a próxima.
                    print(f"  (resposta descartada pelo navegador: {err}; aguardando de novo)")
                    continue
                return json.loads(body["body"])

        try:
            path = tools.send("Runtime.evaluate", expression="location.pathname").get("result", {}).get("value", "")
        except DevToolsError:
            continue  # página trocando bem nessa hora
        if path.startswith("/login") or path.startswith("/register"):
            if not asked_login:
                print("Faça login no Discord na janela do navegador que abriu (só na primeira vez)...")
                asked_login = True
        elif asked_login:
            # Depois do login o Discord vai para outra página; volta para as missões.
            asked_login = False
            tools.send("Page.navigate", url=QUEST_HOME)
    raise SystemExit("Não encontrei a lista de missões a tempo.")


def parse_game_quests(data):
    """Missões de jogo pendentes: [{app_id, name, minutes, enrolled}]."""
    quests = data.get("quests", []) if isinstance(data, dict) else data
    now = datetime.now(timezone.utc)
    result = []
    for quest in quests:
        config = quest.get("config") or {}
        status = quest.get("user_status") or {}
        if status.get("completed_at"):
            continue
        expires = config.get("expires_at")
        if expires and datetime.fromisoformat(expires.replace("Z", "+00:00")) < now:
            continue

        tasks = (config.get("task_config_v2") or config.get("task_config") or {}).get("tasks") or {}
        task = tasks.get("PLAY_ON_DESKTOP")
        if not task:
            continue

        app = config.get("application") or {}
        task_apps = task.get("applications") or []
        app_id = (task_apps[0].get("id") if task_apps else None) or app.get("id")
        done = ((status.get("progress") or {}).get("PLAY_ON_DESKTOP") or {}).get("value", 0)
        remaining = max(task.get("target", 900) - done, 60)
        result.append({
            "app_id": str(app_id),
            "name": app.get("name") or (config.get("messages") or {}).get("game_title") or "?",
            "minutes": math.ceil(remaining / 60),
            "enrolled": bool(status.get("enrolled_at")),
        })
    return result


def fetch_game_quests():
    print("\nAbrindo o Discord numa janela separada do navegador...")
    port = free_port()
    proc, ws_url = open_browser(port)
    tools = DevTools(ws_url)
    try:
        data = capture_quests(tools)
    finally:
        tools.close()
        proc.terminate()

    # Guarda a resposta crua, para conferir se algo não for reconhecido.
    BUILD.mkdir(exist_ok=True)
    RAW_DUMP.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return parse_game_quests(data)
