from __future__ import annotations

import html
import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlparse

from weapo_games.games.candidate_vote.game import CandidateVoteGame


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


class LocalVoteServer:
    def __init__(self, game: CandidateVoteGame) -> None:
        self.game = game
        self.server = ThreadingHTTPServer(("0.0.0.0", 0), self._handler())
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        return f"http://{local_ip()}:{self.server.server_port}/"

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def _handler(self):
        game = self.game

        class Handler(BaseHTTPRequestHandler):
            def _send(self, body: str, content_type: str = "text/html; charset=utf-8") -> None:
                encoded = body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(encoded)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(encoded)

            def do_OPTIONS(self) -> None:  # noqa: N802
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def do_GET(self) -> None:  # noqa: N802
                if urlparse(self.path).path != "/":
                    self.send_error(404)
                    return
                candidates = [
                    {"id": c.id, "name": c.name, "color": c.color}
                    for c in game.snapshot()
                ]
                voters = [{"id": v.id, "name": v.name, "has_voted": v.has_voted} for v in game.voters_snapshot()]
                payload = json.dumps({"candidates": candidates, "voters": voters}, ensure_ascii=False)
                self._send(_PAGE.replace("__DATA__", payload))

            def do_POST(self) -> None:  # noqa: N802
                if urlparse(self.path).path != "/vote":
                    self.send_error(404)
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    data = json.loads(self.rfile.read(length))
                    accepted = game.add_vote(int(data["voter_id"]), int(data["candidate_id"]))
                except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                    accepted = False
                self._send(json.dumps({"accepted": accepted}), "application/json")

            def log_message(self, *_args) -> None:
                return

        return Handler


_PAGE = """<!doctype html><html lang='es'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Votación</title><style>
body{font-family:system-ui;background:#101318;color:#f3f5f7;margin:0;padding:20px}h1{text-align:center;color:#f5c542}
#grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;max-width:700px;margin:auto}
button{border:2px solid #444b57;border-radius:12px;background:#1a1f27;color:white;padding:18px 8px;font-size:17px;min-height:100px}
button.voter-option{min-height:145px;font-size:21px;padding:24px 12px}
button.selected{outline:4px solid #f5c542;border-color:white}#confirm{display:block;margin:22px auto;background:#f5c542;color:#111318;font-weight:bold;min-height:auto;padding:13px 30px}
#message{text-align:center;color:#aeb6c2;font-size:16px}</style><h1>Emite tu voto</h1><div id='grid'></div>
<button id='confirm' disabled>Confirmar voto</button><p id='message'>Selecciona un candidato.</p><script>
const data=__DATA__,grid=document.querySelector('#grid'),confirm=document.querySelector('#confirm'),message=document.querySelector('#message');let selected=null,phase='voter',voterId=null;
function render(){grid.innerHTML='';selected=null;confirm.disabled=true;if(phase==='voter'){message.textContent='Selecciona tu nombre para continuar.';data.voters.filter(v=>!v.has_voted).forEach(v=>button(v.name,v.id,'#4f86c6'));confirm.textContent='Confirmar votante';}else{message.textContent='Selecciona un candidato.';data.candidates.forEach(c=>button(c.name,c.id,c.color));confirm.textContent='Confirmar voto';}}
function button(label,id,color){const b=document.createElement('button');b.textContent=label;if(phase==='voter')b.classList.add('voter-option');b.style.borderTop='12px solid '+color;b.onclick=()=>{selected=id;document.querySelectorAll('#grid button').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');confirm.disabled=false;};grid.appendChild(b)}
confirm.onclick=async()=>{if(phase==='voter'){voterId=selected;phase='candidate';render();return;}confirm.disabled=true;const r=await fetch('/vote',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({voter_id:voterId,candidate_id:selected})});const d=await r.json();if(d.accepted){phase='done';grid.innerHTML='';confirm.style.display='none';message.textContent='¡Voto registrado! Para emitir otro voto, vuelve a escanear el código QR.';}else{phase='done';grid.innerHTML='';confirm.style.display='none';message.textContent='Este votante ya ha votado. Escanea de nuevo el código QR.';}};render();
</script>"""
