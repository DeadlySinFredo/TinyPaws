"""OBS browser source: http://127.0.0.1:<port>/ draws the pet on a transparent canvas.

The Qt loop calls publish() with the same draw items the desktop renderer gets;
browsers receive them via Server-Sent Events. Bound to localhost only.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .sprites import PALETTE, SPRITES

PAGE = r"""<!doctype html><meta charset="utf-8"><title>TinyPaws OBS</title>
<style>html,body{margin:0;background:transparent;overflow:hidden}canvas{width:100vw;height:100vh;object-fit:contain;image-rendering:pixelated}</style>
<canvas id="c"></canvas><script>
const c=document.getElementById('c'),g=c.getContext('2d');let S={},P={},cache={},scale=0;
function sprite(n,f){const k=n+f;if(cache[k])return cache[k];const r=S[n],o=document.createElement('canvas');
o.width=r[0].length*scale;o.height=r.length*scale;const x=o.getContext('2d');
if(f){x.translate(o.width,0);x.scale(-1,1)}
r.forEach((row,y)=>[...row].forEach((ch,i)=>{if(ch!='.'){x.fillStyle=P[ch];x.fillRect(i*scale,y*scale,scale,scale)}}));
return cache[k]=o}
function font(px){g.font='bold '+Math.max(8,px|0)+'px "DejaVu Sans Mono",monospace'}
function draw(f){if(c.width!=f.w||c.height!=f.h){c.width=f.w;c.height=f.h}
if(f.s!=scale){scale=f.s;cache={}}g.clearRect(0,0,c.width,c.height);
for(const it of f.items){const k=it[0];
if(k=='sprite')g.drawImage(sprite(it[1],it[4]),it[2]|0,it[3]|0);
else if(k=='rect'){g.fillStyle=it[5];g.fillRect(it[1]|0,it[2]|0,it[3]|0,it[4]|0)}
else if(k=='text'){font(it[4]);g.textAlign='center';g.lineWidth=Math.max(1,it[4]/7);g.strokeStyle='#1b1b1b';
g.strokeText(it[1],it[2],it[3]);g.fillStyle=it[5];g.fillText(it[1],it[2],it[3])}
else if(k=='bubble'){font(10+scale*1.5);const w=g.measureText(it[1]).width+16,h=10+scale*1.5+12;
const x=Math.max(4,Math.min(c.width-w-4,it[2]-w/2)),y=Math.max(4,it[3]-h-6);
g.fillStyle='#fff';g.strokeStyle='#2b1d16';g.lineWidth=2;g.beginPath();g.roundRect(x,y,w,h,6);g.fill();g.stroke();
g.fillStyle='#2b1d16';g.textAlign='center';g.textBaseline='middle';g.fillText(it[1],x+w/2,y+h/2);g.textBaseline='alphabetic'}
else if(k=='rays'){const[,cx,cy,t,a,R]=it;g.fillStyle=`rgba(255,215,64,${0.43*a})`;
for(let i=0;i<12;i++){const b=t*0.5+i*Math.PI/6;g.beginPath();g.moveTo(cx,cy);
g.lineTo(cx+R*Math.cos(b-0.1),cy+R*Math.sin(b-0.1));g.lineTo(cx+R*Math.cos(b+0.1),cy+R*Math.sin(b+0.1));g.fill()}}
else if(k=='spot'){const[,cx,top,bot,wt,wb,a]=it,gr=g.createLinearGradient(0,top,0,bot);
gr.addColorStop(0,`rgba(255,250,220,${0.08*a})`);gr.addColorStop(1,`rgba(255,250,220,${0.43*a})`);
g.fillStyle=gr;g.beginPath();g.moveTo(cx-wt,top);g.lineTo(cx+wt,top);g.lineTo(cx+wb,bot);g.lineTo(cx-wb,bot);g.fill()}}}
fetch('sprites.json').then(r=>r.json()).then(d=>{S=d.sprites;P=d.palette;
new EventSource('stream').onmessage=e=>draw(JSON.parse(e.data))});
</script>"""


class ObsServer:
    def __init__(self, port=8737, fps=30):
        self.fps, self.frame, self.seq = fps, '{"w":1,"h":1,"s":1,"items":[]}', 0
        self.cond = threading.Condition()
        assets = json.dumps({'sprites': SPRITES, 'palette': PALETTE}).encode()
        srv = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, body, ctype):
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                path = self.path.split('?')[0]
                if path == '/':
                    self._send(PAGE.encode(), 'text/html; charset=utf-8')
                elif path == '/sprites.json':
                    self._send(assets, 'application/json')
                elif path == '/stream':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()
                    seen = -1
                    try:
                        while srv.httpd:
                            with srv.cond:
                                srv.cond.wait_for(lambda: srv.seq != seen, timeout=15)
                                seen, data = srv.seq, srv.frame
                            self.wfile.write(b'data: ' + data.encode() + b'\n\n')
                            self.wfile.flush()
                            time.sleep(1 / srv.fps)  # cap per-client rate
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                else:
                    self.send_error(404)

        # localhost only: the stream shows chat names, nothing to expose on the LAN
        self.httpd = ThreadingHTTPServer(('127.0.0.1', port), H)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def publish(self, w, h, scale, items):
        data = json.dumps({'w': w, 'h': h, 's': scale, 'items': items}, separators=(',', ':'))
        with self.cond:
            if data != self.frame:
                self.frame, self.seq = data, self.seq + 1
                self.cond.notify_all()

    def close(self):
        httpd, self.httpd = self.httpd, None
        httpd.shutdown()
        httpd.server_close()
