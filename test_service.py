import json, threading, urllib.request
from http.server import ThreadingHTTPServer
from service import Handler

srv=ThreadingHTTPServer(("127.0.0.1",0),Handler); port=srv.server_address[1]
t=threading.Thread(target=srv.serve_forever,daemon=True); t.start()
with urllib.request.urlopen(f"http://127.0.0.1:{port}/health") as r:
    health=json.load(r)
assert health["version"]=="0.5" and health["status"]=="ok"
req=urllib.request.Request(f"http://127.0.0.1:{port}/build_request", data=json.dumps({"scene":"coffee","view":"front"}).encode(), headers={"Content-Type":"application/json"}, method="POST")
with urllib.request.urlopen(req) as r: out=json.load(r)
assert out["scene"]=="coffee" and len(out["references"])>=3
srv.shutdown(); print("v0.4 service tests passed", health)
