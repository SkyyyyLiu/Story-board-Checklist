#!/usr/bin/env python3
"""分镜Checklist — 手机扫码传输服务器"""
import os, json, socket, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PORT = 8899
DATA_STORE = []
LOCK = threading.Lock()
DIR = os.path.dirname(os.path.abspath(__file__))

PHONE_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>传送到分镜Checklist</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d0d0f;color:#f0f0f2;font-family:-apple-system,'PingFang SC',sans-serif;padding:24px 20px;min-height:100vh;display:flex;flex-direction:column}
h1{font-size:20px;font-weight:600;margin-bottom:6px;color:#fff}
p{font-size:14px;color:rgba(255,255,255,0.5);margin-bottom:16px}
textarea{flex:1;width:100%;min-height:200px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:16px;color:#fff;font-size:16px;line-height:1.7;font-family:inherit;resize:vertical}
.btn{width:100%;padding:14px;margin-top:12px;border:none;border-radius:12px;font-size:17px;font-weight:600;background:#007aff;color:#fff;cursor:pointer}
.btn:active{opacity:0.7}
.status{margin-top:12px;text-align:center;font-size:14px;color:rgba(255,255,255,0.4)}
.status.ok{color:#30d158}.status.err{color:#ff453a}
</style></head><body>
<h1>📋 传送到分镜Checklist</h1>
<p>粘贴分镜内容，每行一个。</p>
<textarea id="t"></textarea>
<button class="btn" id="b">📤 发送到监视器</button>
<div class="status" id="s"></div>
<script>
const b=document.getElementById('b'),t=document.getElementById('t'),s=document.getElementById('s');
b.addEventListener('click',async()=>{const v=t.value.trim();if(!v){s.textContent='⚠️ 输入内容';s.className='status err';return}
b.disabled=true;b.textContent='⏳...';try{const r=await fetch('/api/send',{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:v});const d=await r.json()
if(d.ok){s.textContent='✅ '+d.count+' 行已传送';s.className='status ok';t.value=''}else{s.textContent='❌ 失败';s.className='status err'}}catch(e){s.textContent='❌ '+e.message;s.className='status err'}
b.disabled=false;b.textContent='📤 发送到监视器'})
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        p=urlparse(self.path).path
        if p in('/','/index.html'):
            f=os.path.join(DIR,'index.html')
            if os.path.exists(f):
                with open(f,'rb')as x: d=x.read()
                self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.send_header('Access-Control-Allow-Origin','*');self.end_headers();self.wfile.write(d)
            else: self.send_error(404)
            return
        if p=='/phone':
            self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.send_header('Access-Control-Allow-Origin','*');self.end_headers();self.wfile.write(PHONE_PAGE.encode())
            return
        if p=='/api/poll':
            with LOCK:
                if DATA_STORE: d=DATA_STORE.pop(0)
                else: d=None
            self.send_response(200);self.send_header('Content-Type','application/json;charset=utf-8');self.send_header('Access-Control-Allow-Origin','*');self.end_headers();self.wfile.write(json.dumps({'ok':True,'data':d}).encode())
            return
        self.send_error(404)
    def do_POST(self):
        if self.path=='/api/send':
            l=int(self.headers.get('Content-Length',0));b=self.rfile.read(l).decode('utf-8')
            c=len([x for x in b.split('\n') if x.strip()])
            with LOCK: DATA_STORE.append(b)
            self.send_response(200);self.send_header('Content-Type','application/json;charset=utf-8');self.send_header('Access-Control-Allow-Origin','*');self.end_headers();self.wfile.write(json.dumps({'ok':True,'count':c}).encode())

def get_ip():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try: s.connect(('10.255.255.255',1));return s.getsockname()[0]
    except: return '127.0.0.1'
    finally: s.close()

if __name__=='__main__':
    ip=get_ip();url=f'http://{ip}:{PORT}/'
    print(f'\n  📋 分镜Checklist 传输服务器')
    print(f'  ─────────────────────────────')
    print(f'  🌐 监视器打开: {url}')
    print(f'  📱 手机扫码: {url}phone')
    print(f'  按 Ctrl+C 停止\n')
    try: HTTPServer(('0.0.0.0',PORT),H).serve_forever()
    except KeyboardInterrupt: print('\n  已停止')
