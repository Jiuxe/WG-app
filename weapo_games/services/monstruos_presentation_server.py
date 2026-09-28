from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import unquote
import socket

from weapo_games.games.monstruos import MonstruosGame


def _local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


class MonstruosPresentationServer:
    """Publica únicamente el estado seguro para la ventana de jugadores."""

    def __init__(self, game: MonstruosGame, image_dir: Path) -> None:
        self.game = game
        self.image_dir = image_dir
        self.server = ThreadingHTTPServer(("0.0.0.0", 0), self._handler())
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        return f"http://{_local_ip()}:{self.server.server_port}/"

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _handler(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def _send(self, body: str, content_type: str = "text/html; charset=utf-8") -> None:
                encoded = body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(encoded)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(encoded)

            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/" or self.path.startswith("/?"):
                    self._send(_PAGE)
                    return
                if self.path == "/api/state":
                    state = owner.game.published
                    public_state = {
                        "active": [
                            {"name": m["name"], "max_hp": m["max_hp"]}
                            for m in state["active"]
                        ],
                        "queue": [
                            {"name": m["name"], "max_hp": m["max_hp"]}
                            for m in state["queue"]
                        ],
                        "players": state["players"],
                    }
                    self._send(json.dumps(public_state, ensure_ascii=False), "application/json; charset=utf-8")
                    return
                if self.path.startswith("/image/"):
                    filename = unquote(self.path.removeprefix("/image/"))
                    if filename not in {f.name for f in owner.image_dir.glob("*.jpg")}:
                        self.send_error(404)
                        return
                    image_path = owner.image_dir / filename
                    data = image_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(data)
                    return
                self.send_error(404)

            def log_message(self, *_args) -> None:
                return

        return Handler


_PAGE = """<!doctype html>
<html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Monstruos</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{font-family:system-ui;background:#101318;color:#f3f5f7;margin:0;min-height:100vh;padding:30px 34px 88px}
#layout{display:grid;grid-template-columns:260px minmax(0,1fr);gap:28px;max-width:1800px;margin:0 auto}
#players{background:#1a1f27;border:1px solid #343b47;border-radius:18px;padding:18px;height:max-content;position:sticky;top:30px}
#players h2{font-size:18px;color:#f6d7a7;margin:0 0 14px;text-transform:uppercase;letter-spacing:.06em}
.player{display:flex;justify-content:space-between;gap:12px;padding:11px 4px;border-bottom:1px solid #343b47;font-size:18px}.player:last-child{border-bottom:0}.player .points{font-weight:900;color:#f5c542;white-space:nowrap}
#content{min-width:0}#active{display:grid;grid-template-columns:repeat(3,minmax(230px,1fr));gap:28px}
.card{background:#231b25;border:2px solid #6b4054;border-radius:22px;padding:26px;display:flex;flex-direction:column;align-items:center;min-height:480px;box-shadow:0 12px 30px #0005}
.card img{width:100%;height:330px;object-fit:contain;border-radius:14px}.name{font-size:clamp(22px,2.2vw,36px);font-weight:800;color:#f6d7a7;text-align:center;margin-top:18px}.hp{font-size:clamp(24px,2vw,34px);font-weight:900;color:#e86c75;margin-top:14px}
#queue{display:flex;justify-content:center;gap:14px;flex-wrap:wrap;margin:28px auto 0;max-width:1400px}.small{min-width:130px;background:#1a1f27;border:1px solid #343b47;border-radius:14px;padding:12px;text-align:center}.small img{width:100px;height:90px;object-fit:contain}.small .name{font-size:16px;margin-top:5px}
#controls{position:fixed;right:24px;bottom:20px;display:flex;gap:10px}button{border:1px solid #d8a91b;border-radius:9px;background:#f5c542;color:#111318;font-weight:800;padding:13px 22px;font-size:15px}button.secondary{background:#242932;color:#f3f5f7;border-color:#444b57}
@media(max-width:1050px){#layout{grid-template-columns:1fr}#players{position:static}#active{grid-template-columns:repeat(3,minmax(180px,1fr))}}
@media(max-width:850px){#active{grid-template-columns:1fr}.card{min-height:0}.card img{height:260px}}
</style></head><body><div id='layout'><aside id='players'><h2>Jugadores</h2><div id='playerList'></div></aside><main id='content'><section id='active'></section><section id='queue'></section></main></div><div id='controls'><button onclick='load()'>Refrescar</button><button class='secondary' onclick='window.close()'>Salir</button></div>
<script>
const active=document.querySelector('#active'),queue=document.querySelector('#queue'),playerList=document.querySelector('#playerList');
function image(name){return '/image/'+encodeURIComponent(name+'.jpg')}
function card(m,small=false){return `<article class='${small?'small':'card'}'><img src='${image(m.name)}' alt='${m.name}'><div class='name'>${m.name}</div><div class='hp'>❤ ${m.max_hp}</div></article>`}
function player(p){return `<div class='player'><span>${p.name}</span><span class='points'>${p.score} puntos</span></div>`}
async function load(){const state=await fetch('/api/state',{cache:'no-store'}).then(r=>r.json());active.innerHTML=state.active.map(m=>card(m)).join('');queue.innerHTML=state.queue.map(m=>card(m,true)).join('');playerList.innerHTML=state.players.map(player).join('')}
load();setInterval(load,2000);
</script></body></html>"""
